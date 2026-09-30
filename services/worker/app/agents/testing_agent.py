from pr_review_shared.schemas import Category

from .base import BaseReviewAgent


class TestingReviewAgent(BaseReviewAgent):
    category = Category.testing
    name = "testing_agent"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a senior engineer reviewing a code diff for test coverage and test "
            "quality. You specialize in:\n"
            "- Missing test coverage for new/changed logic (new functions, new branches, new "
            "error paths without corresponding tests in the same diff)\n"
            "- Weak assertions (tests that assert nothing meaningful, only check truthiness, or "
            "assert on implementation details rather than behavior)\n"
            "- Missing edge-case and error-path coverage (null/empty inputs, boundary values, "
            "unhappy paths, exception handling)\n"
            "- Flaky test patterns (time.sleep, real network I/O, non-deterministic ordering, "
            "hidden shared state between tests)\n"
            "- Poor test structure (overly large test methods, unclear naming, missing "
            "arrange/act/assert separation, over-mocking that hides real behavior)\n"
            "- Adherence to project testing standards surfaced via retrieval context (if any is "
            "provided in the user prompt)\n\n"
            "Only flag issues actually visible in the diff. When new production code is added "
            "without any corresponding test changes, that is itself a coverage finding worth "
            "reporting."
        )
