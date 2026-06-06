"""System tool that returns the current date and time with optional timezone and format."""

from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

# Common timezone aliases for convenience
_TIMEZONE_ALIASES: dict[str, str] = {
    "北京时间": "Asia/Shanghai",
    "上海": "Asia/Shanghai",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "cst": "Asia/Shanghai",
    "纽约": "America/New_York",
    "new york": "America/New_York",
    "est": "America/New_York",
    "edt": "America/New_York",
    "伦敦": "Europe/London",
    "london": "Europe/London",
    "gmt": "Etc/GMT",
    "utc": "Etc/UTC",
    "东京": "Asia/Tokyo",
    "tokyo": "Asia/Tokyo",
    "jst": "Asia/Tokyo",
    "巴黎": "Europe/Paris",
    "paris": "Europe/Paris",
    "柏林": "Europe/Berlin",
    "berlin": "Europe/Berlin",
    "悉尼": "Australia/Sydney",
    "sydney": "Australia/Sydney",
    "洛杉矶": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
}


def _resolve_timezone(tz: str) -> ZoneInfo | None:
    """Resolve a timezone name or alias to a ZoneInfo object. Returns None if invalid."""
    if not tz:
        return None
    key = tz.strip().lower()
    if key in _TIMEZONE_ALIASES:
        key = _TIMEZONE_ALIASES[key].lower()
    if key in available_timezones():
        return ZoneInfo(key)
    # Try case-insensitive match
    for name in available_timezones():
        if name.lower() == key:
            return ZoneInfo(name)
    return None


def get_datetime(
    timezone: str = "Asia/Shanghai",
    format: str = "%Y-%m-%d %H:%M:%S",
) -> dict:
    """Return the current date and time, optionally in a specified timezone and format.

    Args:
        timezone: IANA timezone name (e.g. 'Asia/Shanghai', 'America/New_York', 'UTC').
                  Also accepts common aliases like '北京时间', 'EST', 'GMT'.
        format: strftime format string. Default is '%Y-%m-%d %H:%M:%S'.

    Returns:
        A dict with keys:
            - datetime: Formatted datetime string
            - timezone: Resolved timezone name
            - iso: ISO 8601 formatted datetime
            - timestamp: Unix timestamp (float)
            - weekday: Day of week in Chinese (星期一-星期日)
    """
    tz_info = _resolve_timezone(timezone)
    if tz_info is None:
        available_list = sorted(available_timezones())[:10]
        return {
            "error": f"Invalid timezone: '{timezone}'. "
                     f"Use an IANA timezone name like 'Asia/Shanghai', 'America/New_York', or 'UTC'. "
                     f"First 10 available: {available_list}",
            "datetime": "",
            "timezone": timezone,
            "iso": "",
            "timestamp": 0.0,
            "weekday": "",
        }

    now = datetime.now(tz_info)
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_cn = weekday_names[now.weekday()]

    return {
        "datetime": now.strftime(format),
        "timezone": str(tz_info),
        "iso": now.isoformat(),
        "timestamp": now.timestamp(),
        "weekday": weekday_cn,
    }


__all__ = ["get_datetime"]
