import httpx
import warnings
import re
import traceback
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# 屏蔽自签名证书警告
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

@register("ip_query", "TianLang Hacker", "查询 IP 地理位置及类型插件", "0.0.2")
class IPQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 优先级 1：ip-api.com (提供详细类型判断)
        self.primary_api = "http://ip-api.com/json/{}?fields=66846719"
        # 优先级 2：ipapi.co （当ip-api不可用时使用）
        self.backup_api = "https://ipapi.co/{}/json/"

    @filter.command("ip")
    async def ip_query(self, event: AstrMessageEvent):
        """查询 IP 信息及类型。用法: /ip <可选IP>"""
        
        # 确保用户提供了准确的 IP 地址
        raw_text = event.message_str.strip()
        match = re.search(r'^ip\s+(\S+)', raw_text, re.I)
        target_ip = match.group(1) if match else ""

        # 调用核心查询逻辑
        res_msg = await self.fetch_ip_info(target_ip)
        yield event.plain_result(res_msg)

    async def fetch_ip_info(self, ip: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36s"
        }

        # trust_env=False 无视系统代理; verify=False 解决证书问题
        async with httpx.AsyncClient(headers=headers, timeout=10, trust_env=False, verify=False) as client:
            
            # --- 尝试主接口 (ip-api.com) ---
            try:
                url = self.primary_api.format(ip)
                logger.info(f"[IP-Query] 正在请求主源: {url}")
                response = await client.get(url)
                response.raise_for_status() 
                data = response.json()
                
                if data.get("status") == "success":
                    return self.format_primary_res(data)
                else:
                    logger.error(f"[IP-Query] 主源业务逻辑失败: {data.get('message')}")
            except httpx.HTTPStatusError as e:
                logger.error(f"[IP-Query] 主源 HTTP 状态码异常: {e.response.status_code}")
            except httpx.ConnectError:
                logger.error(f"[IP-Query] 主源连接失败：DNS 解析错误或网络不可达")
            except httpx.TimeoutException:
                logger.error(f"[IP-Query] 主源请求超时")
            except Exception as e:
                # AI 审查建议：打印详细堆栈以供调试
                logger.error(f"[IP-Query] 主源未知异常: {str(e)}\n{traceback.format_exc()}")

            # --- 尝试备用接口 (ipapi.co) ---
            try:
                logger.info(f"[IP-Query] 正在切换至备用源...")
                url = self.backup_api.format(ip)
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                if not data.get("error"):
                    return self.format_backup_res(data)
            except Exception as e:
                logger.error(f"[IP-Query] 备用源查询也失败了: {str(e)}")

        return "❌ 查询失败：所有接口均无法连接。\n调试建议：请在终端查看 AstrBot 日志获取详细报错。"

    def format_primary_res(self, data: dict) -> str:
        """格式化主接口返回的数据"""
        ip_tags = []
        if data.get("mobile"): ip_tags.append("这个IP可能是蜂窝移动网络")
        if data.get("proxy"): ip_tags.append("这个IP可能是代理/VPN IP")
        if data.get("hosting"): ip_tags.append("这个IP可能是数据中心/机房IP")
        
        # 按照用户要求：使用换行连接标签
        tag_str = " \n ".join(ip_tags) if ip_tags else "这个IP可能是家庭宽带或者其他IP"

        # ip-api.com 返回的经纬度
        lat = data.get('lat', 0)
        lon = data.get('lon', 0)
        lat_dir = "北纬" if lat >= 0 else "南纬"
        lon_dir = "东经" if lon >= 0 else "西经"

        #ipapi.co 返回的经纬度
        latitude = data.get('latitude', 0)
        longitude = data.get('longitude', 0)
        lat_dir = "北纬" if latitude >= 0 else "南纬"
        lon_dir = "东经" if longitude >= 0 else "西经"
        
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
            f"坐标: {lat_dir}{lat}°, {lon_dir}{lon}°\n"
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
            f"坐标: {lat_dir}{latitude}°, {lon_dir}{longitude}°\n"
            f"该源不支持查看IP类型\n"
            f"------------------"
        )