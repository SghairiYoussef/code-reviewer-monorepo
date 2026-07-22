import hashlib
import hmac

from app.vcs.github.provider import GitHubProvider
from app.vcs.github.webhook import GitHubWebhookValidator


def test_github_signature_validation() -> None:
    body = b'{"action":"opened"}'
    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    validator = GitHubWebhookValidator("secret")

    assert validator.validate({"x-hub-signature-256": signature}, body)
    assert not validator.validate({"x-hub-signature-256": "sha256=bad"}, body)


def test_parse_pull_request_event() -> None:
    provider = GitHubProvider()
    payload = {
        "action": "opened",
        "number": 7,
        "installation": {"id": 99},
        "repository": {
            "id": 123,
            "full_name": "acme/widgets",
            "html_url": "https://github.com/acme/widgets",
        },
        "pull_request": {
            "title": "Improve widgets",
            "body": None,
            "base": {"sha": "base"},
            "head": {"sha": "head"},
        },
    }
    event = provider.parse_webhook_event(
        {"x-github-event": "pull_request", "x-github-delivery": "delivery"}, payload
    )

    assert event is not None
    assert event.provider_host == "github.com"
    assert event.repository_id == "123"
    assert event.installation_id == 99
    assert event.base_sha == "base"


def test_irrelevant_action_is_ignored() -> None:
    provider = GitHubProvider()
    assert (
        provider.parse_webhook_event({"x-github-event": "pull_request"}, {"action": "closed"})
        is None
    )
