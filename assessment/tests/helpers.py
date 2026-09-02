"""Test helpers — a FakeFetcher so probe scoring is exercised against canned
responses without touching the network. (Lives in tests/, never in production.)"""
from harness.fetch import Fetched


class FakeFetcher:
    """Maps URL -> Fetched. Unmapped URLs return a connection-error artifact."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.calls = []

    def get(self, url: str, accept=None, user_agent=None) -> Fetched:
        self.calls.append((url, accept) if user_agent is None
                          else (url, accept, user_agent))
        # A per-UA response map lets a test serve a different answer to a
        # different client identity: responses[(url, user_agent)] wins.
        if user_agent is not None and (url, user_agent) in self.responses:
            return self.responses[(url, user_agent)]
        if url in self.responses:
            return self.responses[url]
        return Fetched(
            requested_url=url, final_url=url, status=None, headers={}, body="",
            error="no fake response registered",
        )


def fetched(url, status=200, headers=None, body="", error=None):
    """Build a Fetched with lowercased headers, the way build_fetched would."""
    norm = {k.lower(): v for k, v in (headers or {}).items()}
    return Fetched(
        requested_url=url,
        final_url=url,
        status=status,
        headers=norm,
        body=body,
        error=error,
        content_type=norm.get("content-type", "").split(";")[0].strip(),
    )
