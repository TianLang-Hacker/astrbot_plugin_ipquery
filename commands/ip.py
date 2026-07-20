import re

from astrbot.api.event import AstrMessageEvent

from ..services.ip_services import fetch_ip_info


async def handle_ip(event: AstrMessageEvent):
    """处理 /ip 命令"""

    raw_text = event.message_str.strip()

    match = re.search(r"^ip\s+(\S+)", raw_text, re.IGNORECASE)
    target_ip = match.group(1) if match else ""

    # 用户没有输入查询目标
    if not target_ip:
        yield event.plain_result(
            "❌ 请提供需要查询的 IP 地址、IPv6 地址或域名。\n\n"
            "用法：/ip <IP地址或域名>\n"
            "例如：/ip 8.8.8.8\n"
            "例如：/ip 2400:3200::1\n"
            "例如：/ip example.com"
        )
        return

    result = await fetch_ip_info(target_ip)

    yield event.plain_result(result)
