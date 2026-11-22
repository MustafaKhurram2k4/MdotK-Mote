"""User-agent and viewport gate. Backend check is a convenience, not spoof-proof security."""
from fastapi import Request

def classify_device(user_agent: str, width: int | None = None, touch_points: int = 0) -> str:
    ua = (user_agent or "").lower()
    if any(x in ua for x in ("ipad", "tablet", "kindle", "silk")):
        return "tablet"
    if "macintosh" in ua and touch_points > 1:
        return "tablet"
    android = "android" in ua
    mobile_tokens = ("iphone", "ipod", "mobile", "windows phone")
    if android and "mobile" not in ua:
        return "tablet"
    if any(t in ua for t in mobile_tokens) or (android and "mobile" in ua):
        return "phone"
    return "desktop"

def request_class(request: Request) -> str:
    return classify_device(request.headers.get("user-agent", ""))
