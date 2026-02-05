import httpx
import warnings
import re
import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# 屏蔽自签名证书警告
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

@register("ip_query", "TianLang Hacker", "查询 IP 地理位置及类型插件", "0.0.3")
class IPQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 定义多个 API 源以应对频率限制
        self.apis = [
            {"name": "ip-api.com", "url": "http://ip-api.com/json/{}?fields=66846719", "type": "primary"},  #主要源
            {"name": "snappytree镜像", "url": "https://is.snappytree.com/api/ipapi/{}", "type": "primary"}, # ip-api 镜像源
            {"name": "ipapi.co备用", "url": "https://ipapi.co/{}/json/", "type": "backup"}, #备用源  ipapi.co
        ]

    @filter.command("ip")
    async def ip_query(self, event: AstrMessageEvent):
        """查询 IP 信息。用法: /ip <IP>"""
        raw_text = event.message_str.strip()
        match = re.search(r'^ip\s+(\S+)', raw_text, re.I)
        target_ip = match.group(1) if match else ""

        res_msg = await self.fetch_ip_info(target_ip)
        yield event.plain_result(res_msg)

    # 定义一个 UA 伪装成浏览器尝试绕过拦截
    async def fetch_ip_info(self, ip: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        #trust_env=True 以使用系统代理设置，如果代理IP经常被封禁建议关闭或者直接在Clash（Mihomo）配置文件添加API URL的直连再或者直接删除trust_env参数
        async with httpx.AsyncClient(headers=headers, timeout=8, trust_env=True) as client:
            for api in self.apis:
                try:
                    url = api["url"].format(ip)
                    logger.info(f"[IP-Query] 尝试使用源: {api['name']}")
                    
                    response = await client.get(url)
                    
                    # 如果遇到频率限制 (429) 或 拒绝访问 (403)，立即换源
                    if response.status_code in [403, 429]:
                        logger.warning(f"[IP-Query] 源 {api['name']} 触发风控，正在尝试下一个...")
                        continue
                    
                    response.raise_for_status()
                    data = response.json()

                    # 根据源类型匹配对应的 format 函数
                    if api["type"] == "primary":
                        # 镜像源通常和 ip-api 结构一致
                        if data.get("status") == "success" or "query" in data:
                            return self.format_primary_res(data)
                    else:
                        # 备用源 ipapi.co
                        if not data.get("error"):
                            return self.format_backup_res(data)

                except Exception as e:
                    logger.error(f"[IP-Query] 源 {api['name']} 请求出错: {str(e)}")
                    continue # 失败了尝试列表中的下一个

        return "❌ 所有查询接口均已失效或达到频率上限。\n💡 建议：请稍后再试，或检查此 IP 是否已被 API 服务商拉黑。"

    def format_primary_res(self, data: dict) -> str:
        """格式化主接口返回的数据"""
        ip_tags = []
        if data.get("mobile"): ip_tags.append("这个IP可能是蜂窝移动网络")
        if data.get("proxy"): ip_tags.append("这个IP可能是代理/VPN IP")
        if data.get("hosting"): ip_tags.append("这个IP可能是数据中心/机房IP")
        
        tag_str = " \n ".join(ip_tags) if ip_tags else "这个IP可能是家庭宽带或者其他IP"

        # 处理经纬度及方向
        lat = data.get('lat', 0)
        lon = data.get('lon', 0)
        # 修复逻辑：在这里统一计算方向，避免 format 函数内部变量冲突
        lat_dir = "北纬" if lat >= 0 else "南纬"
        lon_dir = "东经" if lon >= 0 else "西经"

        return (
            f"IP 查询结果 (主用源：ip-api.com):\n"
            f"------------------\n"
            f"查询 IP: {data.get('query')}\n"
            f"归属地: {data.get('country')} - {data.get('regionName')} - {data.get('city')}\n"
            f"国家\\地区代码: {data.get('countryCode')}\n"
            f"大陆: {data.get('continent')}\n"
            f"运营商: {data.get('isp')}\n"
            f"时区: {data.get('timezone')}\n"
            f"组织: {data.get('org')}\n"
            f"AS号: {data.get('as')}\n"
            f"坐标: {lat_dir}{abs(lat)}°, {lon_dir}{abs(lon)}°\n"
            f"{tag_str}\n"
            f"------------------"
        )

    def format_backup_res(self, data: dict) -> str:
        """格式化备用接口返回的数据"""
        # 修复：在函数作用域内定义这些变量，防止 NameError
        latitude = data.get('latitude', 0)
        longitude = data.get('longitude', 0)
        lat_dir = "北纬" if latitude >= 0 else "南纬"
        lon_dir = "东经" if longitude >= 0 else "西经"
        
        return (
            f"IP 查询结果 (备用源：ipapi.co):\n"
            f"------------------\n"
            f"查询 IP: {data.get('ip')}\n"
            f"归属地: {data.get('country_name')} - {data.get('region')} - {data.get('city')}\n"
            f"国家\\地区代码: {data.get('country_code')}\n"
            f"大陆: {data.get('continent_code')}\n"
            f"运营商: {data.get('isp')}\n"
            f"时区: {data.get('timezone')}\n"
            f"组织: {data.get('org')}\n"
            f"AS号: {data.get('asn')}\n"
            f"坐标: {lat_dir}{abs(latitude)}°, {lon_dir}{abs(longitude)}°\n"
            f"该源不支持查看IP类型\n"
            f"------------------"
        )