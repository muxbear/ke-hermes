"""HTTP/HTTPS 请求系统工具，发送请求并返回结构化响应。"""

from typing import Any
from urllib.parse import urlparse

import httpx

# SSRF 防护：禁止访问的主机名
_BLOCKED_HOSTS: set[str] = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
# 响应体最大长度（字符数）
_MAX_RESPONSE_SIZE: int = 100_000
# 默认超时时间（秒）
_DEFAULT_TIMEOUT: int = 30


def _is_safe_url(url: str) -> bool:
    """检查 URL 是否使用 http/https 协议且未指向内网地址。"""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = (parsed.hostname or "").lower()
    return hostname not in _BLOCKED_HOSTS and not hostname.startswith("10.") and not hostname.startswith("192.168.")


def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """发送 HTTP/HTTPS 请求并返回响应。

    Args:
        url: 目标 URL（必须使用 http 或 https 协议）。
        method: HTTP 方法（GET、POST、PUT、DELETE、PATCH 等）。
        headers: 可选的自定义请求头，键值对形式。
        body: 可选的请求体字符串（用于 POST/PUT/PATCH）。
        timeout: 请求超时时间（秒），默认 30 秒。

    Returns:
        包含以下字段的字典：
            - status_code: HTTP 状态码
            - headers: 响应头键值对
            - body: 响应体字符串（过长时自动截断）
            - url: 最终请求 URL（跟随重定向后）
            - error: 错误信息（仅在失败时存在）
    """
    method = method.upper().strip()
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
        return {"error": f"不支持的 HTTP 方法：'{method}'", "status_code": 0, "headers": {}, "body": "", "url": url}

    if not _is_safe_url(url):
        return {
            "error": f"不安全的 URL：'{url}'。仅允许公网 http/https 地址，"
                     f"内网地址（localhost、127.0.0.1、私有 IP 段）已被拦截。",
            "status_code": 0,
            "headers": {},
            "body": "",
            "url": url,
        }

    if timeout > 120:
        timeout = 120
    elif timeout < 1:
        timeout = _DEFAULT_TIMEOUT

    try:
        req_headers = dict(headers) if headers else {}
        req_body: str | None = body

        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.request(
                method=method,
                url=url,
                headers=req_headers,
                content=req_body,
            )

        resp_headers = dict(response.headers)
        resp_body = response.text

        # 响应体过大时截断
        truncated = len(resp_body) > _MAX_RESPONSE_SIZE
        if truncated:
            resp_body = resp_body[:_MAX_RESPONSE_SIZE] + f"\n... [已截断，原始大小：{len(response.text)} 字符]"

        result: dict[str, Any] = {
            "status_code": response.status_code,
            "headers": resp_headers,
            "body": resp_body,
            "url": str(response.url),
        }
        if truncated:
            result["truncated"] = True
        return result

    except httpx.TimeoutException:
        return {"error": f"请求超时（{timeout} 秒）", "status_code": 0, "headers": {}, "body": "", "url": url}
    except httpx.InvalidURL:
        return {"error": f"无效的 URL：'{url}'", "status_code": 0, "headers": {}, "body": "", "url": url}
    except Exception as e:
        return {"error": f"请求失败：{e}", "status_code": 0, "headers": {}, "body": "", "url": url}


__all__ = ["http_request"]
