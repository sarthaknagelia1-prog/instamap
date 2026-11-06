import asyncio

from backend.main import RequestSecurityMiddleware


def test_request_body_limit_catches_chunked_requests_without_content_length():
    async def run_request():
        messages = iter([
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"5678", "more_body": False},
        ])
        sent = []

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        async def app(scope, receive, send):
            while (await receive()).get("more_body"):
                pass
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        scope = {
            "type": "http", "method": "POST", "path": "/upload", "headers": [],
            "query_string": b"", "scheme": "http", "http_version": "1.1",
            "server": ("test", 80), "client": ("test", 1234), "root_path": "",
        }
        middleware = RequestSecurityMiddleware(app, max_body_bytes=5, trusted_origins=[])
        await middleware(scope, receive, send)
        return sent

    sent = asyncio.run(run_request())
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413

