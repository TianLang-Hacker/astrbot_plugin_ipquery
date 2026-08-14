import re

from astrbot.api.event import AstrMessageEvent

from ..services.whois_services import fetch_whois_info


async def handle_whois(event: AstrMessageEvent):
    """处理 /whois 命令"""

    raw_text = event.message_str.strip()

    match = re.search(r"^whois\s+(\S+)", raw_text, re.IGNORECASE)
    target_whois = match.group(1) if match else ""

    # 用户没有输入查询目标
    if not target_whois:
        yield event.plain_result(
            "❌ 请提供需要查询的域名信息。\n\n"
            "用法：/whois <域名>\n"
            "例如：/whois github.com"
        )
        return

    result = await fetch_whois_info(target_whois)

    yield event.plain_result(result)
