import httpx
import warnings
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

@register("ip_query", "TianLang Hacker", "查询 IP 地理位置及类型插件", "0.0.1")
class IPQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 优先级 1：ip-api.com (提供详细类型判断)
        self.primary_api = "http://ip-api.com/json/{}?fields=66846719"
        # 优先级 2：ipapi.co (HTTPS 协议)
        self.backup_api = "https://ipapi.co/{}/json/"

    @filter.command("ip")
    async def ip_query(self, event: AstrMessageEvent):
        """查询 IP 信息及类型。用法: /ip <可选IP>"""
        
        # --- 核心处理部分 ---
        raw_message = event.message_str.strip()
        parts = raw_message.split()
        
        # 如果长度大于 1 (例如 "ip 1.1.1.1")，取最后一部分作为 IP
        # 如果长度等于 1 (例如 "ip")，传空字符串给接口查询服务器本机 IP
        if len(parts) > 1:
            target_ip = parts[-1]
        else:
            target_ip = ""
        
        # 过滤掉可能的指令词（防止用户输入 "ip ip"）
        if target_ip.lower() == "ip":
            target_ip = ""
            
        logger.info(f"解析到的目标 IP: '{target_ip}'")
        # --------------------
        
        res_msg = await self.fetch_ip_info(target_ip)
        yield event.plain_result(res_msg)

    async def fetch_ip_info(self, ip: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
        }

        # 添加 verify=False 彻底解决 Docker 环境下可能缺失根证书的问题
        async with httpx.AsyncClient(headers=headers, timeout=8, trust_env=False, verify=False) as client:
            # --- 尝试第一个源 (ip-api.com) ---
            try:
                url = self.primary_api.format(ip)
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return self.format_primary_res(data)
            except Exception as e:
                logger.warning(f"IP主接口请求失败，尝试备用接口: {e}")

            # --- 尝试第二个源 (ipapi.co) ---
            try:
                url = self.backup_api.format(ip)
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("error"):
                        return self.format_backup_res(data)
            except Exception as e:
                logger.error(f"IP备用接口也失败了: {e}")

        return "❌ 查询失败：所有接口均无法连接，请检查格式或稍后重试。"

    def format_primary_res(self, data: dict) -> str:
        """格式化主接口返回的数据"""
        ip_tags = []
        if data.get("mobile"): ip_tags.append("这个IP可能是蜂窝移动网络")
        if data.get("proxy"): ip_tags.append("这个IP可能是代理/VPN IP")
        if data.get("hosting"): ip_tags.append("这个IP可能是数据中心/机房IP")
        
        tag_str = " \n ".join(ip_tags) if ip_tags else "这个IP可能是家庭宽带或者其他IP"
        
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
            f"坐标: 北纬{data.get('lat')}°, 东经{data.get('lon')}°\n"
            f"{tag_str}\n"
            f"------------------"
        )

    def format_backup_res(self, data: dict) -> str:
        """格式化备用接口返回的数据"""
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
            f"坐标: 北纬{data.get('latitude')}°, 东经{data.get('longitude')}°\n"
            f"该源不支持查看IP类型\n"
            f"------------------"
        )