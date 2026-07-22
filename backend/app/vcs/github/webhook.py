import hashlib
import hmac


class GitHubWebhookValidator:
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def validate(self, headers: dict[str, str], body: bytes) -> bool:
        signature = headers.get("x-hub-signature-256", "")
        if not self._secret or not signature.startswith("sha256="):
            return False
        expected = "sha256=" + hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    def extract_event_type(self, headers: dict[str, str]) -> str | None:
        return headers.get("x-github-event")
