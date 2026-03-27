"""Tests for WorkdayBrowserAdapter with mock Playwright page objects."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auto_apply.workday_adapter import (
    WORKDAY_SELECTORS,
    ApplicationResult,
    StepResult,
    WizardStep,
    WorkdayBrowserAdapter,
)

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_profile(**overrides: Any) -> MagicMock:
    """Create a mock AutoApplyProfile."""
    defaults = {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "linkedin_url": "https://linkedin.com/in/janedoe",
        "github_url": "https://github.com/janedoe",
        "portfolio_url": "https://janedoe.dev",
    }
    defaults.update(overrides)
    profile = MagicMock()
    for k, v in defaults.items():
        setattr(profile, k, v)
    return profile


def _make_locator(*, count: int = 1, inner_text: str = "Next", tag: str = "input") -> MagicMock:
    """Return a mock Playwright Locator."""
    loc = MagicMock()
    loc.count = AsyncMock(return_value=count)
    loc.first = MagicMock()
    loc.first.inner_text = AsyncMock(return_value=inner_text)
    loc.first.fill = AsyncMock()
    loc.first.click = AsyncMock()
    loc.first.set_input_files = AsyncMock()
    loc.first.select_option = AsyncMock()
    loc.first.evaluate = AsyncMock(return_value=tag)
    return loc


def _make_page(
    *,
    automation_ids: list[str] | None = None,
    locator_map: dict[str, MagicMock] | None = None,
    next_button_text: str = "Next",
    has_next: bool = True,
) -> MagicMock:
    """Build a mock Playwright Page with configurable behavior."""
    page = MagicMock()

    # Default automation IDs (personal info page)
    if automation_ids is None:
        automation_ids = [
            "legalNameSection_firstName",
            "legalNameSection_lastName",
            "email",
            "phone",
        ]

    # evaluate() dispatcher
    async def _evaluate(js_code: str, arg: Any = None) -> Any:
        # Shadow DOM collect IDs
        if "collectIds" in js_code:
            return automation_ids
        # Shadow DOM query single
        if "queryShadow" in js_code and "queryShadowAll" not in js_code:
            return None  # fall through to locator path
        # Shadow DOM query all
        if "queryShadowAll" in js_code:
            return []
        # Element tag name
        if "tagName" in str(js_code):
            return "input"
        # Inner text
        if "innerText" in str(js_code):
            return next_button_text
        # Fill via JS
        if "dispatchEvent" in str(js_code):
            return None
        return None

    page.evaluate = AsyncMock(side_effect=_evaluate)
    page.screenshot = AsyncMock(return_value=b"fake-png-bytes")
    page.wait_for_load_state = AsyncMock()

    # locator() returns different mocks per selector
    default_loc = _make_locator(count=1, inner_text=next_button_text)
    next_loc = _make_locator(
        count=1 if has_next else 0,
        inner_text=next_button_text,
    )

    def _locator(selector: str) -> MagicMock:
        if locator_map and selector in locator_map:
            return locator_map[selector]
        if selector == WORKDAY_SELECTORS["next_button"]:
            return next_loc
        # Resume upload locator — not present by default
        if selector == WORKDAY_SELECTORS["resume_upload"]:
            return _make_locator(count=0)
        return default_loc

    page.locator = MagicMock(side_effect=_locator)

    return page


@pytest.fixture()
def profile() -> MagicMock:
    return _make_profile()


# ---------------------------------------------------------------------------
# Tests: Initialization
# ---------------------------------------------------------------------------


class TestWorkdayBrowserAdapterInit:
    def test_default_delays(self, profile: MagicMock) -> None:
        page = _make_page()
        adapter = WorkdayBrowserAdapter(page, profile)
        assert adapter.action_delay == (3.0, 5.0)
        assert adapter.MAX_PAGES == 15

    def test_custom_delays(self, profile: MagicMock) -> None:
        page = _make_page()
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0.0, 0.0))
        assert adapter.action_delay == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Tests: Profile mapping
# ---------------------------------------------------------------------------


class TestProfileMapping:
    def test_build_profile_map_full(self, profile: MagicMock) -> None:
        page = _make_page()
        adapter = WorkdayBrowserAdapter(page, profile)
        m = adapter._build_profile_map()
        assert m["first_name"] == "Jane"
        assert m["last_name"] == "Doe"
        assert m["email"] == "jane@example.com"
        assert m["phone"] == "+1-555-0100"
        assert m["linkedin_url"] == "https://linkedin.com/in/janedoe"

    def test_build_profile_map_single_name(self) -> None:
        profile = _make_profile(full_name="Madonna")
        page = _make_page()
        adapter = WorkdayBrowserAdapter(page, profile)
        m = adapter._build_profile_map()
        assert m["first_name"] == "Madonna"
        assert m["last_name"] is None

    def test_build_profile_map_empty_name(self) -> None:
        profile = _make_profile(full_name="")
        page = _make_page()
        adapter = WorkdayBrowserAdapter(page, profile)
        m = adapter._build_profile_map()
        assert m["first_name"] is None
        assert m["last_name"] is None


# ---------------------------------------------------------------------------
# Tests: Step detection
# ---------------------------------------------------------------------------


class TestStepDetection:
    @pytest.mark.asyncio()
    async def test_detects_personal_info(self, profile: MagicMock) -> None:
        page = _make_page(automation_ids=[
            "legalNameSection_firstName",
            "legalNameSection_lastName",
            "email",
        ])
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        step = await adapter._detect_current_step()
        assert step == WizardStep.PERSONAL_INFO

    @pytest.mark.asyncio()
    async def test_detects_experience(self, profile: MagicMock) -> None:
        page = _make_page(automation_ids=["jobTitle", "company", "currentlyWorkHere"])
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        step = await adapter._detect_current_step()
        assert step == WizardStep.EXPERIENCE

    @pytest.mark.asyncio()
    async def test_detects_education(self, profile: MagicMock) -> None:
        page = _make_page(automation_ids=["school", "degree"])
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        step = await adapter._detect_current_step()
        assert step == WizardStep.EDUCATION

    @pytest.mark.asyncio()
    async def test_detects_review_via_submit_button(self, profile: MagicMock) -> None:
        page = _make_page(
            automation_ids=["review"],
            next_button_text="Submit Application",
        )
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        step = await adapter._detect_current_step()
        assert step == WizardStep.REVIEW

    @pytest.mark.asyncio()
    async def test_unknown_step_on_no_indicators(self, profile: MagicMock) -> None:
        page = _make_page(automation_ids=["random_field"])
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        step = await adapter._detect_current_step()
        assert step == WizardStep.UNKNOWN


# ---------------------------------------------------------------------------
# Tests: Field filling
# ---------------------------------------------------------------------------


class TestFieldFilling:
    @pytest.mark.asyncio()
    async def test_fill_shadow_field_via_locator(self, profile: MagicMock) -> None:
        loc = _make_locator(count=1, tag="input")
        page = _make_page(locator_map={
            WORKDAY_SELECTORS["first_name"]: loc,
        })
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._fill_shadow_field(
            WORKDAY_SELECTORS["first_name"], "Jane"
        )
        assert result is True
        loc.first.fill.assert_awaited_once_with("Jane")

    @pytest.mark.asyncio()
    async def test_fill_shadow_field_select(self, profile: MagicMock) -> None:
        loc = _make_locator(count=1, tag="select")
        page = _make_page(locator_map={
            WORKDAY_SELECTORS["state"]: loc,
        })
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._fill_shadow_field(
            WORKDAY_SELECTORS["state"], "California"
        )
        assert result is True
        loc.first.select_option.assert_awaited_once_with(label="California")

    @pytest.mark.asyncio()
    async def test_fill_shadow_field_locator_not_found_falls_through(
        self, profile: MagicMock
    ) -> None:
        """When locator count=0 and JS traversal also returns None, returns False."""
        loc = _make_locator(count=0)
        page = _make_page(locator_map={
            WORKDAY_SELECTORS["first_name"]: loc,
        })
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._fill_shadow_field(
            WORKDAY_SELECTORS["first_name"], "Jane"
        )
        assert result is False


# ---------------------------------------------------------------------------
# Tests: Resume upload
# ---------------------------------------------------------------------------


class TestResumeUpload:
    @pytest.mark.asyncio()
    async def test_upload_via_input(self, profile: MagicMock) -> None:
        upload_loc = _make_locator(count=1)
        page = _make_page(locator_map={
            WORKDAY_SELECTORS["resume_upload"]: upload_loc,
        })
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._upload_resume("/tmp/resume.pdf")
        assert result is True
        upload_loc.first.set_input_files.assert_awaited_once_with("/tmp/resume.pdf")

    @pytest.mark.asyncio()
    async def test_upload_returns_false_when_no_input(self, profile: MagicMock) -> None:
        page = _make_page()  # default: resume_upload locator count=0
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._upload_resume("/tmp/resume.pdf")
        assert result is False


# ---------------------------------------------------------------------------
# Tests: Navigation
# ---------------------------------------------------------------------------


class TestNavigation:
    @pytest.mark.asyncio()
    async def test_click_next_succeeds(self, profile: MagicMock) -> None:
        page = _make_page(has_next=True, next_button_text="Next")
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._click_next()
        assert result is True
        page.wait_for_load_state.assert_awaited()

    @pytest.mark.asyncio()
    async def test_click_next_stops_on_submit(self, profile: MagicMock) -> None:
        page = _make_page(has_next=True, next_button_text="Submit Application")
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._click_next()
        assert result is False

    @pytest.mark.asyncio()
    async def test_click_next_returns_false_when_no_button(self, profile: MagicMock) -> None:
        page = _make_page(has_next=False)
        # Also make the fallback selector return 0
        fallback_loc = _make_locator(count=0)
        original_locator = page.locator.side_effect

        def _locator(selector: str) -> MagicMock:
            if selector == WORKDAY_SELECTORS["next_button"]:
                return _make_locator(count=0)
            if "has-text" in selector:
                return fallback_loc
            return original_locator(selector)

        page.locator = MagicMock(side_effect=_locator)
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))
        result = await adapter._click_next()
        assert result is False


# ---------------------------------------------------------------------------
# Tests: Full apply flow
# ---------------------------------------------------------------------------


class TestApplyFlow:
    @pytest.mark.asyncio()
    async def test_single_page_flow(self, profile: MagicMock) -> None:
        """Single page with no next button -> fills and returns."""
        page = _make_page(has_next=False, automation_ids=[
            "legalNameSection_firstName",
            "legalNameSection_lastName",
            "email",
        ])
        # Make fallback also return nothing
        fallback_loc = _make_locator(count=0)

        def _locator(selector: str) -> MagicMock:
            if "has-text" in selector:
                return fallback_loc
            if selector == WORKDAY_SELECTORS["next_button"]:
                return _make_locator(count=0)
            if selector == WORKDAY_SELECTORS["resume_upload"]:
                return _make_locator(count=0)
            return _make_locator(count=1, tag="input")

        page.locator = MagicMock(side_effect=_locator)

        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))

        with patch.object(adapter, "_human_delay", new_callable=AsyncMock):
            with patch.object(adapter, "_inter_field_delay", new_callable=AsyncMock):
                result = await adapter.apply()

        assert isinstance(result, ApplicationResult)
        assert result.success is True
        assert result.needs_confirmation is True
        assert result.ats == "workday"
        assert len(result.screenshots) >= 1

    @pytest.mark.asyncio()
    async def test_stops_at_review_page(self, profile: MagicMock) -> None:
        """When we detect review step, stop immediately with needs_confirmation."""
        page = _make_page(
            automation_ids=["review"],
            next_button_text="Submit Application",
        )
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))

        with patch.object(adapter, "_human_delay", new_callable=AsyncMock):
            result = await adapter.apply()

        assert result.success is True
        assert result.needs_confirmation is True
        assert len(result.steps) == 1
        assert result.steps[0].step == WizardStep.REVIEW

    @pytest.mark.asyncio()
    async def test_apply_with_resume(self, profile: MagicMock) -> None:
        """Resume upload path is attempted."""
        upload_loc = _make_locator(count=1)
        page = _make_page(
            has_next=False,
            automation_ids=["legalNameSection_firstName"],
            locator_map={
                WORKDAY_SELECTORS["resume_upload"]: upload_loc,
            },
        )

        # Make fallback nav buttons missing
        fallback_loc = _make_locator(count=0)

        def _locator(selector: str) -> MagicMock:
            if selector == WORKDAY_SELECTORS["resume_upload"]:
                return upload_loc
            if "has-text" in selector:
                return fallback_loc
            if selector == WORKDAY_SELECTORS["next_button"]:
                return _make_locator(count=0)
            return _make_locator(count=1, tag="input")

        page.locator = MagicMock(side_effect=_locator)

        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))

        with patch.object(adapter, "_human_delay", new_callable=AsyncMock):
            with patch.object(adapter, "_inter_field_delay", new_callable=AsyncMock):
                result = await adapter.apply(resume_path="/tmp/resume.pdf")

        assert result.success is True
        upload_loc.first.set_input_files.assert_awaited_once_with("/tmp/resume.pdf")

    @pytest.mark.asyncio()
    async def test_never_auto_submits(self, profile: MagicMock) -> None:
        """The adapter must NEVER click a submit button."""
        page = _make_page(
            has_next=True,
            next_button_text="Submit Application",
            automation_ids=["legalNameSection_firstName"],
        )
        adapter = WorkdayBrowserAdapter(page, profile, action_delay=(0, 0))

        with patch.object(adapter, "_human_delay", new_callable=AsyncMock):
            with patch.object(adapter, "_inter_field_delay", new_callable=AsyncMock):
                result = await adapter.apply()

        # Should have stopped and returned needs_confirmation
        assert result.needs_confirmation is True
        assert result.success is True


# ---------------------------------------------------------------------------
# Tests: ApplicationResult properties
# ---------------------------------------------------------------------------


class TestApplicationResult:
    def test_fields_filled_merges_steps(self) -> None:
        result = ApplicationResult(
            success=True,
            steps=[
                StepResult(
                    step=WizardStep.PERSONAL_INFO,
                    fields_filled={"first_name": "Jane"},
                ),
                StepResult(
                    step=WizardStep.EXPERIENCE,
                    fields_filled={"job_title": "Engineer"},
                ),
            ],
        )
        assert result.fields_filled == {
            "first_name": "Jane",
            "job_title": "Engineer",
        }

    def test_fields_missed_concatenates(self) -> None:
        result = ApplicationResult(
            success=True,
            steps=[
                StepResult(
                    step=WizardStep.PERSONAL_INFO,
                    fields_missed=["phone"],
                ),
                StepResult(
                    step=WizardStep.EXPERIENCE,
                    fields_missed=["company"],
                ),
            ],
        )
        assert result.fields_missed == ["phone", "company"]

    def test_empty_result(self) -> None:
        result = ApplicationResult(success=False, error="timeout")
        assert result.fields_filled == {}
        assert result.fields_missed == []
        assert result.error == "timeout"


# ---------------------------------------------------------------------------
# Tests: Selector constants
# ---------------------------------------------------------------------------


class TestSelectors:
    def test_all_selectors_are_strings(self) -> None:
        for key, val in WORKDAY_SELECTORS.items():
            assert isinstance(key, str)
            assert isinstance(val, str)

    def test_critical_selectors_present(self) -> None:
        required = [
            "first_name", "last_name", "email", "phone",
            "resume_upload", "next_button",
        ]
        for key in required:
            assert key in WORKDAY_SELECTORS, f"Missing selector: {key}"
