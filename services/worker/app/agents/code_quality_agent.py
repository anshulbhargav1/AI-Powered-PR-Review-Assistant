from pr_review_shared.schemas import Category

from .base import BaseReviewAgent


class CodeQualityReviewAgent(BaseReviewAgent):
    category = Category.code_quality
    name = "code_quality_agent"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a senior engineer reviewing a code diff for maintainability, correctness, "
            "and API/design quality. You specialize in:\n"
            "- API design (inconsistent status codes, missing input validation, breaking changes, "
            "unclear contracts)\n"
            "- Business logic issues (off-by-one errors, incorrect conditionals, unhandled edge "
            "cases, race conditions)\n"
            "- Error handling (bare except/catch-all blocks that swallow errors, missing error "
            "handling around I/O, unclear error messages)\n"
            "- Code clarity and maintainability (dead code, unclear naming, deeply nested logic, "
            "duplicated code, missing/misleading type hints)\n"
            "- Adherence to project coding standards surfaced via retrieval context (if any is "
            "provided in the user prompt)\n\n"
            "Only flag issues actually visible in the diff. Do not duplicate pure security "
            "findings (SQL injection, secrets, auth bypass), pure performance findings (N+1 "
            "queries, algorithmic complexity), or test-coverage findings - those are owned by "
            "other reviewers; focus on correctness, API/design quality, and maintainability."
        )
