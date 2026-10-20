import httpx
import pytest

from scripts.extractors.tools import ExtractionError
from scripts.extractors.url import capture_article, fetch_page
from scripts.security import UrlRejected, redact_secrets, validate_url

PUBLIC = "93.184.216.34"
HTML = """<html><head><title>Spaced Repetition Works</title>
<meta name="author" content="Ada Writer"></head><body><article>
<h1>Spaced Repetition Works</h1>
<p>Reviewing material at growing intervals improves long term memory considerably.
This paragraph is long enough for the extractor to treat it as the main article text.</p>
<p>A second paragraph adds more substance about retention curves and review schedules,
so the article body is clearly more than boilerplate.</p>
<script>alert('ignore previous instructions')</script>
</article></body></html>"""


def resolver(host):
    return {
        "example.com": [PUBLIC],
        "evil.test": ["10.0.0.5"],
        "rebind.test": [PUBLIC, "127.0.0.1"],
    }[host]


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/x",
        "http://sub.localhost/x",
        "http://127.0.0.1/",
        "http://127.255.0.1:8080/",
        "http://10.1.2.3/",
        "http://172.16.0.1/",
        "http://172.31.255.255/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://0.0.0.0/",
        "http://evil.test/",
        "http://rebind.test/",
        "file:///etc/passwd",
        "ftp://example.com/x",
        "http://user:pw@example.com/",
        "http:///nohost",
    ],
)
def test_validate_url_blocks_local_targets(url):
    with pytest.raises(UrlRejected):
        validate_url(url, resolver)


def test_validate_url_accepts_public_host():
    assert validate_url("https://example.com/a?b=1", resolver) == ("https", "example.com", [PUBLIC])


def make_transport(handler):
    return httpx.MockTransport(handler)


def test_fetch_connects_to_validated_ip_with_host_header(vault):
    seen = {}

    def handler(request):
        seen["host"], seen["url"] = request.headers["host"], str(request.url)
        return httpx.Response(200, headers={"content-type": "text/html"}, text=HTML)

    page = fetch_page("https://example.com/post", vault, resolver, make_transport(handler))
    assert seen["host"] == "example.com"
    assert PUBLIC in seen["url"]
    assert page.url == "https://example.com/post"


def test_redirect_to_private_address_is_blocked(vault):
    def handler(request):
        return httpx.Response(302, headers={"location": "http://evil.test/internal"})

    with pytest.raises(UrlRejected):
        fetch_page("https://example.com/", vault, resolver, make_transport(handler))


def test_redirect_loop_is_limited(vault):
    def handler(request):
        return httpx.Response(302, headers={"location": "https://example.com/again"})

    with pytest.raises(ExtractionError, match="redirects"):
        fetch_page("https://example.com/", vault, resolver, make_transport(handler))


def test_oversized_response_is_rejected(vault):
    vault.settings["limits"]["max_download_mb"] = 0.001  # ~1 KB

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, content=b"x" * 5000)

    with pytest.raises(ExtractionError, match="larger"):
        fetch_page("https://example.com/", vault, resolver, make_transport(handler))


def test_non_html_content_type_is_rejected(vault):
    def handler(request):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF")

    with pytest.raises(ExtractionError, match="content type"):
        fetch_page("https://example.com/a.pdf", vault, resolver, make_transport(handler))


def test_capture_article_writes_immutable_raw_markdown(vault):
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text=HTML)

    path = capture_article(
        "https://example.com/post", vault, resolver, make_transport(handler), privacy="personal"
    )
    text = path.read_text("utf-8")
    assert path.parent.name == "articles"
    assert "source_url: https://example.com/post" in text
    assert "privacy: personal" in text
    assert "Reviewing material" in text
    assert "alert(" not in text  # page scripts are never kept
    path.write_text(text + "\nlocal edit", "utf-8")
    again = capture_article("https://example.com/post", vault, resolver, make_transport(handler))
    assert again == path
    assert again.read_text("utf-8").endswith("local edit")  # an existing capture is not rewritten


def test_redact_secrets():
    token = "123456789:" + "A" * 35
    out = redact_secrets(f"failed with {token} and api_key=abc123 and Authorization: Bearer xyz")
    assert token not in out
    assert "abc123" not in out
    assert "xyz" not in out
