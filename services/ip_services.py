import asyncio
import json
import warnings
from typing import Any
from urllib import error, request

try:
    import httpx
except ImportError:  # pragma: no cover - 兼容无 httpx 环境
    httpx = None

try:
    from astrbot.api import logger
except ImportError:  # pragma: no cover - 兼容测试环境
    class _Logger:
        @staticmethod
        def info(message: str) -> None:
            pass

        @staticmethod
        def warning(message: str) -> None:
            pass

        @staticmethod
        def error(message: str) -> None:
            pass

    logger = _Logger()

try:
    from ..api import ALL_API_FAILED_MESSAGE, HEADERS, HTTP_TIMEOUT, IP_APIS, USE_SYSTEM_PROXY
    from ..utils.ip_formatter import format_backup_res, format_primary_res
except ImportError:  # pragma: no cover - 兼容直接运行测试时的导入方式
    from api import ALL_API_FAILED_MESSAGE, HEADERS, HTTP_TIMEOUT, IP_APIS, USE_SYSTEM_PROXY
    from utils.ip_formatter import format_backup_res, format_primary_res

warnings.filterwarnings("ignore", message="Unverified HTTPS request")


def _fetch_json_sync(url: str, headers: dict[str, str], timeout: int) -> Any:
    """在无 httpx 时使用标准库发起 JSON 请求。"""
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


async def _fetch_json(url: str, headers: dict[str, str], timeout: int) -> Any:
    """优先使用 httpx，缺失时回退到标准库。"""
    if httpx is not None:
        async with httpx.AsyncClient(headers=headers, timeout=timeout, trust_env=USE_SYSTEM_PROXY) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    return await asyncio.to_thread(_fetch_json_sync, url, headers, timeout)


async def fetch_ip_info(ip: str) -> str:
    """查询 IP、IPv6 或域名的地理位置与网络类型。"""
    if not isinstance(ip, str) or not ip.strip():
        return "❌ 请输入需要查询的 IP 地址、IPv6 地址或域名。"

    ip = ip.strip()

    for api in IP_APIS:
        try:
            url = api["url"].format(ip)
            logger.info(f"[IP-Query] 尝试使用源: {api['name']}")

            if httpx is not None:
                async with httpx.AsyncClient(headers=HEADERS, timeout=HTTP_TIMEOUT, trust_env=USE_SYSTEM_PROXY) as client:
                    response = await client.get(url)
                    if response.status_code in {403, 429}:
                        logger.warning(f"[IP-Query] 源 {api['name']} 触发风控，正在尝试下一个...")
                        continue
                    response.raise_for_status()
                    data = response.json()
            else:
                data = await _fetch_json(url, HEADERS, HTTP_TIMEOUT)

            if api["type"] == "primary":
                if data.get("status") == "success" or "query" in data:
                    return format_primary_res(data)
            else:
                if not data.get("error"):
                    return format_backup_res(data)
        except (error.URLError, error.HTTPError, ValueError, TimeoutError, ConnectionError, json.JSONDecodeError) as exc:
            logger.error(f"[IP-Query] 源 {api['name']} 请求出错: {exc}")
            continue
        except Exception as exc:
            logger.error(f"[IP-Query] 源 {api['name']} 请求出错: {exc}")
            continue

    return ALL_API_FAILED_MESSAGE
