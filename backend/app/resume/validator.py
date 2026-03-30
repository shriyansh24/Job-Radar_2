"""ATS compatibility checks for ResumeIR payloads."""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.resume.schemas import ATSCheckResult, ATSValidationResult

logger = structlog.get_logger()

STANDARD_SECTIONS = {
    "work": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "core competencies"],
    "summary": ["summary", "professional summary", "objective", "profile"],
}

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
    """Validate a ResumeIR dict for ATS compatibility."""

    def validate(self, ir: dict[str, Any]) -> ATSValidationResult:
        checks = [
            self._check_contact_name(ir),
            self._check_contact_email(ir),
            self._check_contact_phone(ir),
            self._check_has_work(ir),
            self._check_has_education(ir),
            self._check_has_skills(ir),
            self._check_has_summary(ir),
            self._check_bullet_quality(ir),
            self._check_no_image_only(ir),
            self._check_text_length(ir),
            self._check_standard_headers(ir),
        ]
        warnings = [check.message for check in checks if not check.passed]
        score = self._compute_score(checks)
        passed = score >= 60
        extracted_text_length = len(self._ir_to_text(ir))

        logger.info(
            "ats_validator.validate",
            score=score,
            passed=passed,
            checks_passed=sum(1 for check in checks if check.passed),
            checks_total=len(checks),
        )

        return ATSValidationResult(
            score=score,
            passed=passed,
            checks=checks,
            warnings=warnings,
            extracted_text_length=extracted_text_length,
        )

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
            message="Contact email present"
            if has_email
            else "Missing or invalid email address",
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
            message="Work experience section present"
            if has_work
            else "No work experience found - most ATS systems expect this section",
        )

    def _check_has_education(self, ir: dict[str, Any]) -> ATSCheckResult:
        education = ir.get("education", []) or []
        has_education = len(education) > 0
        return ATSCheckResult(
            field="has_education",
            passed=has_education,
            message="Education section present"
            if has_education
            else "No education section found",
        )

    def _check_has_skills(self, ir: dict[str, Any]) -> ATSCheckResult:
        skills = ir.get("skills", []) or []
        skill_categories = ir.get("skill_categories", {}) or {}
        has_skills = len(skills) > 0 or len(skill_categories) > 0
        return ATSCheckResult(
            field="has_skills",
            passed=has_skills,
            message="Skills section present"
            if has_skills
            else "No skills section - ATS keyword matching depends on explicit skill listings",
        )

    def _check_has_summary(self, ir: dict[str, Any]) -> ATSCheckResult:
        summary = ir.get("summary", "")
        has_summary = bool(summary and len(summary) > 10)
        return ATSCheckResult(
            field="has_summary",
            passed=has_summary,
            message="Professional summary present"
            if has_summary
            else "No professional summary - recommended for ATS optimization",
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

        action_count = sum(
            1 for bullet in all_bullets if action_verb_pattern.match(bullet.strip())
        )
        quant_count = sum(
            1 for bullet in all_bullets if quantified_pattern.search(bullet)
        )
        total = len(all_bullets)
        action_ratio = action_count / total
        quant_ratio = quant_count / total
        good_quality = action_ratio >= 0.5 and quant_ratio >= 0.2

        details: dict[str, object] = {
            "total_bullets": total,
            "action_verb_ratio": round(action_ratio, 2),
            "quantified_ratio": round(quant_ratio, 2),
        }

        if good_quality:
            message = (
                f"Bullet quality good: {action_count}/{total} action verbs, "
                f"{quant_count}/{total} quantified"
            )
        else:
            message = (
                f"Bullet quality needs improvement: {action_count}/{total} start with "
                f"action verbs, {quant_count}/{total} include metrics"
            )

        return ATSCheckResult(
            field="bullet_quality",
            passed=good_quality,
            message=message,
            details=details,
        )

    def _check_no_image_only(self, ir: dict[str, Any]) -> ATSCheckResult:
        has_text = len(self._ir_to_text(ir).strip()) > 50
        return ATSCheckResult(
            field="no_image_only",
            passed=has_text,
            message="Resume has parseable text content"
            if has_text
            else "Resume appears to have very little text - may be image-based",
        )

    def _check_text_length(self, ir: dict[str, Any]) -> ATSCheckResult:
        length = len(self._ir_to_text(ir))
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
        present_sections: list[str] = []
        for section_key in STANDARD_SECTIONS:
            content = ir.get(section_key)
            if content and (
                isinstance(content, list)
                and len(content) > 0
                or isinstance(content, str)
                and len(content) > 0
            ):
                present_sections.append(section_key)

        expected = {"work", "education", "skills"}
        missing = expected - set(present_sections)
        passed = len(missing) == 0
        return ATSCheckResult(
            field="standard_headers",
            passed=passed,
            message="All standard ATS sections present"
            if passed
            else f"Missing standard sections: {', '.join(sorted(missing))}",
            details={"present": present_sections, "missing": sorted(missing)},
        )

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
        for education in ir.get("education", []) or []:
            parts.append(
                f"{education.get('institution', '')} {education.get('degree', '')}"
            )
        for skill in ir.get("skills", []) or []:
            parts.append(skill)
        return "\n".join(parts)
