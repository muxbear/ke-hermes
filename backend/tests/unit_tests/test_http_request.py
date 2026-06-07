import pytest
from agent.tools.http_request import _is_safe_url, http_request


class TestIsSafeUrl:
    def test_https_url_is_safe(self):
        assert _is_safe_url("https://example.com/api") is True

    def test_http_url_is_safe(self):
        assert _is_safe_url("http://api.example.com/v1") is True

    def test_ftp_url_is_not_safe(self):
        assert _is_safe_url("ftp://files.example.com") is False

    def test_file_url_is_not_safe(self):
        assert _is_safe_url("file:///etc/passwd") is False

    def test_localhost_is_blocked(self):
        assert _is_safe_url("http://localhost:8000/api") is False

    def test_127_0_0_1_is_blocked(self):
        assert _is_safe_url("https://127.0.0.1:8080/admin") is False

    def test_private_10_network_is_blocked(self):
        assert _is_safe_url("http://10.0.0.1/api") is False

    def test_private_192_168_network_is_blocked(self):
        assert _is_safe_url("http://192.168.1.1/api") is False


class TestHttpRequestValidation:
    def test_unsupported_method_returns_error(self):
        result = http_request(url="https://example.com", method="TRACE")
        assert "error" in result
        assert "不支持的 HTTP 方法" in result["error"]
        assert result["status_code"] == 0

    def test_unsafe_url_returns_error(self):
        result = http_request(url="http://localhost:3000/test")
        assert "error" in result
        assert "不安全的 URL" in result["error"]

    def test_invalid_url_returns_error(self):
        result = http_request(url="not-a-valid-url")
        assert "error" in result


class TestHttpRequestIntegration:
    def test_get_request(self):
        result = http_request(url="https://httpbin.org/get", method="GET")
        assert result["status_code"] == 200
        assert "httpbin.org/get" in result["url"]
        assert len(result["body"]) > 0
        assert isinstance(result["headers"], dict)

    def test_get_with_headers(self):
        result = http_request(
            url="https://httpbin.org/headers",
            method="GET",
            headers={"X-Custom-Header": "test-value"},
        )
        assert result["status_code"] == 200
        assert "X-Custom-Header" in result["body"] or "x-custom-header" in result["body"].lower()

    def test_post_request(self):
        result = http_request(
            url="https://httpbin.org/post",
            method="POST",
            body='{"key": "value"}',
            headers={"Content-Type": "application/json"},
        )
        assert result["status_code"] == 200
        assert "key" in result["body"]

    def test_put_request(self):
        result = http_request(
            url="https://httpbin.org/put",
            method="PUT",
            body="test body",
        )
        assert result["status_code"] == 200

    def test_delete_request(self):
        result = http_request(
            url="https://httpbin.org/delete",
            method="DELETE",
        )
        assert result["status_code"] == 200

    def test_returns_structured_response(self):
        result = http_request(url="https://httpbin.org/get")
        assert "status_code" in result
        assert "headers" in result
        assert "body" in result
        assert "url" in result
        assert isinstance(result["status_code"], int)
        assert isinstance(result["headers"], dict)
        assert isinstance(result["body"], str)
        assert isinstance(result["url"], str)

    def test_404_response(self):
        result = http_request(url="https://httpbin.org/status/404")
        assert result["status_code"] == 404

    def test_redirect_follows(self):
        result = http_request(url="https://httpbin.org/redirect/1", method="GET")
        assert result["status_code"] == 200

    def test_timeout_handling(self):
        result = http_request(
            url="https://httpbin.org/delay/5",
            method="GET",
            timeout=2,
        )
        assert "error" in result
        assert "超时" in result["error"]
