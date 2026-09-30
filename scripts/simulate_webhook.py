#!/usr/bin/env python3
"""Posts a sample GitHub/GitLab webhook payload at the local webhook-gateway to trigger a
full PRReviewWorkflow run end-to-end, without needing real repo credentials.

With VCS_MODE=mock (the default), the worker serves a fixed illustrative diff and logs
comments instead of posting them, so this is enough to exercise the whole pipeline -
including real Groq LLM calls - purely locally.

Zero third-party dependencies on purpose, so it runs with any system `python3`.

Usage:
    python3 scripts/simulate_webhook.py --provider github
    python3 scripts/simulate_webhook.py --provider gitlab --gateway-url http://localhost:8000
"""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

SAMPLES_DIR = pathlib.Path(__file__).parent / "sample_payloads"

# action -> sample payload filename suffix ("" reuses the base opened/open sample)
_GITHUB_ACTIONS = {"opened": "", "synchronize": "_synchronize", "closed": "_closed"}
_GITLAB_ACTIONS = {"open": "", "update": "_update", "close": "_close"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["github", "gitlab"], default="github")
    parser.add_argument("--gateway-url", default="http://localhost:8000")
    parser.add_argument(
        "--action",
        default=None,
        help="github: opened|synchronize|closed (default opened). "
        "gitlab: open|update|close (default open).",
    )
    args = parser.parse_args()

    if args.provider == "github":
        action = args.action or "opened"
        if action not in _GITHUB_ACTIONS:
            parser.error(f"--action for github must be one of {sorted(_GITHUB_ACTIONS)}")
        payload_path = SAMPLES_DIR / f"github_pull_request{_GITHUB_ACTIONS[action]}.json"
        headers = {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"}
        url = f"{args.gateway_url}/webhooks/github"
    else:
        action = args.action or "open"
        if action not in _GITLAB_ACTIONS:
            parser.error(f"--action for gitlab must be one of {sorted(_GITLAB_ACTIONS)}")
        payload_path = SAMPLES_DIR / f"gitlab_merge_request{_GITLAB_ACTIONS[action]}.json"
        headers = {"Content-Type": "application/json"}
        url = f"{args.gateway_url}/webhooks/gitlab"

    payload = json.loads(payload_path.read_text())
    body = json.dumps(payload).encode()

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"{resp.status} {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"{e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Could not reach {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
