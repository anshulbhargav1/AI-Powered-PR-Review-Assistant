import logging

from pr_review_shared.schemas import CodeFileDiff, PRReviewInput

from .base import VCSClient

logger = logging.getLogger(__name__)

# Deliberately imperfect sample diff so a mock-mode run still exercises all four
# agents end-to-end without needing any live GitHub/GitLab credentials.
_SAMPLE_DIFF = [
    CodeFileDiff(
        path="app/services/user_service.py",
        status="modified",
        additions=14,
        deletions=2,
        patch=(
            "@@ -10,8 +10,20 @@ def get_user_orders(user_id, status):\n"
            "-    query = \"SELECT * FROM orders WHERE user_id = %s\" % user_id\n"
            "+    query = \"SELECT * FROM orders WHERE user_id = \" + user_id + \" AND status = '\" + status + \"'\"\n"
            "+    cursor.execute(query)\n"
            "+\n"
            "+    orders = []\n"
            "+    for row in cursor.fetchall():\n"
            "+        order = db.session.query(Order).filter_by(id=row['order_id']).first()\n"
            "+        items = db.session.query(OrderItem).filter_by(order_id=order.id).all()\n"
            "+        orders.append({'order': order, 'items': items})\n"
            "+    return orders\n"
            "+\n"
            "+def save_api_key(user_id, key):\n"
            "+    try:\n"
            "+        AWS_SECRET = 'AKIAIOSFODNN7EXAMPLE1234'\n"
            "+        db.session.execute('UPDATE users SET api_key=%s WHERE id=%s' % (key, user_id))\n"
            "+    except:\n"
            "+        pass\n"
        ),
    ),
    CodeFileDiff(
        path="app/services/pricing.py",
        status="modified",
        additions=12,
        deletions=1,
        patch=(
            "@@ -20,5 +20,16 @@ def apply_discount(cart, code):\n"
            "-    return cart.total * 0.9\n"
            "+    # New: recursive lookup of promo overrides. Nested loop over cart.items\n"
            "+    # inside a loop over promo rules - fine for small carts, but ships to\n"
            "+    # prod without any bound on cart.items.\n"
            "+    total = cart.total\n"
            "+    rules = db.session.query(PromoRule).all()\n"
            "+    for rule in rules:\n"
            "+        for item in cart.items:\n"
            "+            override = db.session.query(Override).filter_by(item_id=item.id, rule_id=rule.id).first()\n"
            "+            if override:\n"
            "+                total -= override.amount\n"
            "+    return total\n"
        ),
    ),
    CodeFileDiff(
        path="tests/test_pricing.py",
        status="added",
        additions=6,
        deletions=0,
        patch=(
            "@@ -0,0 +1,6 @@\n"
            "+def test_apply_discount():\n"
            "+    cart = Cart(total=100, items=[])\n"
            "+    # Only asserts truthiness of the returned value, not the actual discount\n"
            "+    # math. No test for empty cart, no test for the promo-override branch,\n"
            "+    # no test for the error path when the DB query fails.\n"
            "+    assert apply_discount(cart, 'SAVE10')\n"
        ),
    ),
]


class MockVCSClient(VCSClient):
    """Local-dev VCS backend: logs instead of calling a real GitHub/GitLab API,
    and serves a fixed illustrative diff instead of fetching one. Lets the whole
    pipeline (including real Groq agent calls) run end-to-end with zero repo
    write access, selected via VCS_MODE=mock."""

    def refresh_pr_state(self, review_input: PRReviewInput) -> dict:
        return {"open": True, "changed_files": len(_SAMPLE_DIFF)}

    def get_diff(self, review_input: PRReviewInput) -> list[CodeFileDiff]:
        return _SAMPLE_DIFF

    def set_commit_status(
        self,
        repo_full_name: str,
        commit_sha: str,
        state: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        logger.info(
            "[mock-vcs] would set commit status on %s @ %s: state=%s description=%s url=%s",
            repo_full_name, commit_sha, state, description, target_url,
        )

    def upsert_comment(self, review_input: PRReviewInput, marker: str, body: str) -> str:
        logger.info(
            "[mock-vcs] would post comment on %s #%s:\n%s\n%s",
            review_input.repo_full_name,
            review_input.pr_number,
            marker,
            body,
        )
        return review_input.html_url
