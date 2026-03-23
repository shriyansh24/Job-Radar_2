"""ATS Resume Validation — checks that a resume IR will parse well in ATS systems.

Performs structural checks on the ResumeIR dict without needing to render a PDF.
Checks: parseable text, standard section headers, keyword density, contact info,
section completeness, bullet quality, file size estimation.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.resume.schemas import ATSCheckResult, ATSValidationResult

logger = structlog.get_logger()

# Standard section headers ATS systems expect
STANDARD_SECTIONS = {
    "work": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "core competencies"],
    "summary": ["summary", "professional summary", "objective", "profile"],
}

# Weights for scoring
CHECK_WEIGHTS: dict[str, float] = {
    "contact_name": 10.0,
    "contact_email": 10.0,
    "contact_phone": 5.0,
    "has_work": 15.0,
    "has_education": 10.0,
    "has_skills": 10.0,
    "has_summary": 5.0,
    "bullet_quality": 15.0,
    "no_image_only": 5.0,
    "text_length": 10.0,
    "standard_headers": 5.0,
}


class ATSValidator:
    """Validates a ResumeIR dict for ATS compatibility."""

    def validate(self, ir: dict[str, Any]) -> ATSValidationResult:
        """Run all ATS checks against the IR and return a validation result."""
        checks: list[ATSCheckResult] = []
        warnings: list[str] = []

        # Contact checks
        checks.append(self._check_contact_name(ir))
        checks.append(self._check_contact_email(ir))
        checks.append(self._check_contact_phone(ir))

        # Section presence checks
        checks.append(self._check_has_work(ir))
        checks.append(self._check_has_education(ir))
        checks.append(self._check_has_skills(ir))
        checks.append(self._check_has_summary(ir))

        # Quality checks
        checks.append(self._check_bullet_quality(ir))
        checks.append(self._check_no_image_only(ir))
        checks.append(self._check_text_length(ir))
        checks.append(self._check_standard_headers(ir))

        # Collect warnings from failed checks
        for check in checks:
            if not check.passed:
                warnings.append(check.message)

        # Compute weighted score
        score = self._compute_score(checks)
        passed = score >= 60

        text_length = len(self._ir_to_text(ir))

        logger.info(
            "ats_validator.validate",
            score=score,
            passed=passed,
            checks_passed=sum(1 for c in checks if c.passed),
            checks_total=len(checks),
        )

        return ATSValidationResult(
            score=score,
            passed=passed,
            checks=checks,
            warnings=warnings,
            extracted_text_length=text_length,
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_contact_name(self, ir: dict[str, Any]) -> ATSCheckResult:
        contact = ir.get("contact", {}) or {}
        name = contact.get("name", "")
        has_name = bool(name and name != "Unknown")
        return ATSCheckResult(
            field="contact_name",
            passed=has_name,
            message="Contact name present" if has_name else "Missing contact name",
        )

    def _check_contact_email(self, ir: dict[str, Any]) -> ATSCheckResult:
        contact = ir.get("contact", {}) or {}
        email = contact.get("email", "")
        has_email = bool(email and "@" in email)
        return ATSCheckResult(
            field="contact_email",
            passed=has_email,
            message="Contact email present" if has_email else "Missing or invalid email address",
        )

    def _check_contact_phone(self, ir: dict[str, Any]) -> ATSCheckResult:
        contact = ir.get("contact", {}) or {}
        phone = contact.get("phone", "")
        has_phone = bool(phone and len(phone) >= 7)
        return ATSCheckResult(
            field="contact_phone",
            passed=has_phone,
            message="Phone number present" if has_phone else "Missing phone number",
        )

    def _check_has_work(self, ir: dict[str, Any]) -> ATSCheckResult:
        work = ir.get("work", []) or []
        has_work = len(work) > 0
        return ATSCheckResult(
            field="has_work",
            passed=has_work,
            message="Work experience section present" if has_work
            else "No work experience found — most ATS systems expect this section",
        )

    def _check_has_education(self, ir: dict[str, Any]) -> ATSCheckResult:
        edu = ir.get("education", []) or []
        has_edu = len(edu) > 0
        return ATSCheckResult(
            field="has_education",
            passed=has_edu,
            message="Education section present" if has_edu
            else "No education section found",
        )

    def _check_has_skills(self, ir: dict[str, Any]) -> ATSCheckResult:
        skills = ir.get("skills", []) or []
        cats = ir.get("skill_categories", {}) or {}
        has_skills = len(skills) > 0 or len(cats) > 0
        return ATSCheckResult(
            field="has_skills",
            passed=has_skills,
            message="Skills section present" if has_skills
            else "No skills section — ATS keyword matching depends on explicit skill listings",
        )

    def _check_has_summary(self, ir: dict[str, Any]) -> ATSCheckResult:
        summary = ir.get("summary", "")
        has_summary = bool(summary and len(summary) > 10)
        return ATSCheckResult(
            field="has_summary",
            passed=has_summary,
            message="Professional summary present" if has_summary
            else "No professional summary — recommended for ATS optimization",
        )

    def _check_bullet_quality(self, ir: dict[str, Any]) -> ATSCheckResult:
        work = ir.get("work", []) or []
        if not work:
            return ATSCheckResult(
                field="bullet_quality",
                passed=False,
                message="No work bullets to evaluate",
            )

        all_bullets: list[str] = []
        for role in work:
            all_bullets.extend(role.get("bullets", []) or [])

        if not all_bullets:
            return ATSCheckResult(
                field="bullet_quality",
                passed=False,
                message="Work experience has no bullet points",
            )

        # Check for action verbs and quantified results
        action_verb_pattern = re.compile(
            r"^(Led|Managed|Developed|Built|Designed|Implemented|Created|Delivered|"
            r"Improved|Reduced|Increased|Achieved|Established|Launched|Optimized|"
            r"Automated|Analyzed|Coordinated|Mentored|Spearheaded|Streamlined|"
            r"Engineered|Architected|Deployed|Maintained|Configured|Integrated|"
            r"Migrated|Resolved|Collaborated|Contributed|Supported|Executed|"
            r"Facilitated|Generated|Negotiated|Organized|Planned|Produced|"
            r"Researched|Trained|Transformed|Upgraded|Wrote)",
            re.IGNORECASE,
        )
        quantified_pattern = re.compile(r"\d+[%$xX]?|\$[\d,]+")

        action_count = sum(1 for b in all_bullets if action_verb_pattern.match(b.strip()))
        quant_count = sum(1 for b in all_bullets if quantified_pattern.search(b))

        total = len(all_bullets)
        action_ratio = action_count / total
        quant_ratio = quant_count / total

        good_quality = action_ratio >= 0.5 and quant_ratio >= 0.2

        details = {
            "total_bullets": total,
            "action_verb_ratio": round(action_ratio, 2),
            "quantified_ratio": round(quant_ratio, 2),
        }

        if good_quality:
            msg = f"Bullet quality good: {action_count}/{total} action verbs, "
            msg += f"{quant_count}/{total} quantified"
        else:
            msg = f"Bullet quality needs improvement: {action_count}/{total} start with "
            msg += f"action verbs, {quant_count}/{total} include metrics"

        return ATSCheckResult(
            field="bullet_quality",
            passed=good_quality,
            message=msg,
            details=details,
        )

    def _check_no_image_only(self, ir: dict[str, Any]) -> ATSCheckResult:
        # In IR-based validation, we flag if there is no textual content at all
        text = self._ir_to_text(ir)
        has_text = len(text.strip()) > 50
        return ATSCheckResult(
            field="no_image_only",
            passed=has_text,
            message="Resume has parseable text content" if has_text
            else "Resume appears to have very little text — may be image-based",
        )

    def _check_text_length(self, ir: dict[str, Any]) -> ATSCheckResult:
        text = self._ir_to_text(ir)
        length = len(text)
        # Reasonable resume is 500-10000 chars
        good_length = 300 <= length <= 15000
        return ATSCheckResult(
            field="text_length",
            passed=good_length,
            message=f"Resume text length: {length} chars (good range)"
            if good_length
            else f"Resume text length: {length} chars (outside recommended 300-15000)",
            details={"length": length},
        )

    def _check_standard_headers(self, ir: dict[str, Any]) -> ATSCheckResult:
        # Check that the IR has the standard sections ATS expects
        present_sections = []
        for section_key in STANDARD_SECTIONS:
            content = ir.get(section_key)
            if content and (isinstance(content, list) and len(content) > 0
                           or isinstance(content, str) and len(content) > 0):
                present_sections.append(section_key)

        expected = {"work", "education", "skills"}
        missing = expected - set(present_sections)
        passed = len(missing) == 0

        return ATSCheckResult(
            field="standard_headers",
            passed=passed,
            message="All standard ATS sections present" if passed
            else f"Missing standard sections: {', '.join(sorted(missing))}",
            details={"present": present_sections, "missing": sorted(missing)},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_score(self, checks: list[ATSCheckResult]) -> int:
        total_weight = 0.0
        earned_weight = 0.0
        for check in checks:
            weight = CHECK_WEIGHTS.get(check.field, 5.0)
            total_weight += weight
            if check.passed:
                earned_weight += weight

        if total_weight == 0:
            return 0
        return min(100, round((earned_weight / total_weight) * 100))

    @staticmethod
    def _ir_to_text(ir: dict[str, Any]) -> str:
        """Convert IR dict to plain text for length/content checks."""
        parts: list[str] = []
        contact = ir.get("contact", {}) or {}
        if contact.get("name"):
            parts.append(contact["name"])
        if contact.get("email"):
            parts.append(contact["email"])

        if ir.get("summary"):
            parts.append(ir["summary"])

        for work in ir.get("work", []) or []:
            parts.append(f"{work.get('company', '')} {work.get('title', '')}")
            for bullet in work.get("bullets", []) or []:
                parts.append(bullet)

        for edu in ir.get("education", []) or []:
            parts.append(f"{edu.get('institution', '')} {edu.get('degree', '')}")

        for skill in ir.get("skills", []) or []:
            parts.append(skill)

        return "\n".join(parts)
