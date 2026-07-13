class GitHubWebhookValidator:
    def validate(self, headers: dict[str, str], body: bytes) -> bool:
        raise NotImplementedError

    def extract_event_type(self, headers: dict[str, str]) -> str | None:
        raise NotImplementedError
