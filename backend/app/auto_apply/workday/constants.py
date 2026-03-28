from __future__ import annotations

from .types import WizardStep

WORKDAY_SELECTORS: dict[str, str] = {
    "first_name": '[data-automation-id="legalNameSection_firstName"]',
    "last_name": '[data-automation-id="legalNameSection_lastName"]',
    "email": '[data-automation-id="email"]',
    "phone": '[data-automation-id="phone"]',
    "address_line1": '[data-automation-id="addressSection_addressLine1"]',
    "city": '[data-automation-id="addressSection_city"]',
    "state": '[data-automation-id="addressSection_countryRegion"]',
    "postal_code": '[data-automation-id="addressSection_postalCode"]',
    "resume_upload": '[data-automation-id="file-upload-input-ref"]',
    "next_button": '[data-automation-id="bottom-navigation-next-button"]',
    "previous_button": '[data-automation-id="bottom-navigation-previous-button"]',
    "job_title": '[data-automation-id="jobTitle"]',
    "company_name": '[data-automation-id="company"]',
    "currently_work_here": '[data-automation-id="currentlyWorkHere"]',
    "school_name": '[data-automation-id="school"]',
    "degree": '[data-automation-id="degree"]',
    "linkedin": '[data-automation-id="linkedinQuestion"]',
    "text_input": "input[type='text']:visible, textarea:visible",
}

PROFILE_TO_SELECTOR: dict[str, str] = {
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "phone": "phone",
    "linkedin_url": "linkedin",
}

STEP_INDICATORS: dict[WizardStep, list[str]] = {
    WizardStep.PERSONAL_INFO: [
        "legalNameSection_firstName",
        "legalNameSection_lastName",
        "email",
        "phone",
    ],
    WizardStep.EXPERIENCE: [
        "jobTitle",
        "company",
        "currentlyWorkHere",
    ],
    WizardStep.EDUCATION: [
        "school",
        "degree",
    ],
    WizardStep.VOLUNTARY_DISCLOSURES: [
        "voluntaryDisclosures",
        "gender",
        "ethnicity",
        "veteranStatus",
        "disabilityStatus",
    ],
    WizardStep.REVIEW: [
        "review",
    ],
}

JS_QUERY_SHADOW = """
(selector) => {
    function queryShadowAll(root, sel) {
        let results = [...root.querySelectorAll(sel)];
        root.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                results = results.concat(queryShadowAll(el.shadowRoot, sel));
            }
        });
        return results;
    }
    return queryShadowAll(document, selector);
}
"""

JS_QUERY_SHADOW_ONE = """
(selector) => {
    function queryShadow(root, sel) {
        let found = root.querySelector(sel);
        if (found) return found;
        for (const el of root.querySelectorAll('*')) {
            if (el.shadowRoot) {
                found = queryShadow(el.shadowRoot, sel);
                if (found) return found;
            }
        }
        return null;
    }
    return queryShadow(document, selector);
}
"""

JS_DETECT_AUTOMATION_IDS = """
() => {
    function collectIds(root) {
        let ids = [];
        root.querySelectorAll('[data-automation-id]').forEach(el => {
            ids.push(el.getAttribute('data-automation-id'));
        });
        root.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                ids = ids.concat(collectIds(el.shadowRoot));
            }
        });
        return ids;
    }
    return collectIds(document);
}
"""
