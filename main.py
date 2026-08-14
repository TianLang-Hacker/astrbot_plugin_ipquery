from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

from .commands.ip import handle_ip
from .commands.whois import handle_whois


@register(
    "ip_query",
    "TianLang Hacker",
    "查询 IP 地理位置和 Whois 域名及类型的插件",
    "0.0.4",
)
class IPQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("ip")
    async def ip_query(self, event: AstrMessageEvent):
        async for result in handle_ip(event):
            yield result

    @filter.command("whois")
    async def whois_query(self, event: AstrMessageEvent):
        async for result in handle_whois(event):
            yield result
