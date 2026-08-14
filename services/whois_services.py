import asyncio
import json
from typing import Any
from urllib import error, parse, request

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
    from ..api import (
        HEADERS,
        HTTP_TIMEOUT,
        USE_SYSTEM_PROXY,
        WHOIS_ALL_API_FAILED_MESSAGE,
        WHOIS_APIS,
    )
    from ..utils.whois_formatter import format_backup_whois, format_primary_whois
except ImportError:  # pragma: no cover - 兼容直接运行测试时的导入方式
    from api import (
        HEADERS,
        HTTP_TIMEOUT,
        USE_SYSTEM_PROXY,
        WHOIS_ALL_API_FAILED_MESSAGE,
        WHOIS_APIS,
    )
    from utils.whois_formatter import format_backup_whois, format_primary_whois


def _fetch_json_sync(url: str, headers: dict[str, str], timeout: int) -> Any:
    """在无 httpx 时使用标准库发起 JSON 请求。"""
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


async def _fetch_json(url: str) -> Any:
    """优先使用 httpx，缺失时回退到标准库。"""
    if httpx is not None:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=HTTP_TIMEOUT,
            trust_env=USE_SYSTEM_PROXY,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    return await asyncio.to_thread(_fetch_json_sync, url, HEADERS, HTTP_TIMEOUT)


def _is_primary_response(data: Any) -> bool:
    """判断主接口是否返回了 WHOIS 数据，而不是错误提示。"""
    if not isinstance(data, dict) or data.get("error"):
        return False

    return any(
        field in data
        for field in (
            "query",
            "domain",
            "tld",
            "isRegistered",
            "registrar",
            "status",
            "nameservers",
            "dates",
            "contacts",
            "meta",
        )
    )


def _get_backup_data(data: Any) -> dict[str, Any] | None:
    """提取备用接口的 data，并过滤接口错误响应。"""
    if not isinstance(data, dict) or data.get("error"):
        return None

    payload = data.get("data")
    if not isinstance(payload, dict):
        return None

    # 部分返回中 domain_status 位于 data 外层，统一放入格式化数据。
    if "domain_status" not in payload and "domain_status" in data:
        payload = {**payload, "domain_status": data["domain_status"]}

    return payload


async def fetch_whois_info(domain: str) -> str:
    """使用主用、备用接口查询域名 WHOIS 信息。"""
    if not isinstance(domain, str) or not domain.strip():
        return "❌ 请输入需要查询的域名。"

    domain = domain.strip()
    encoded_domain = parse.quote(domain, safe=".-_")

    for api in WHOIS_APIS:
        try:
            url = api["url"].format(encoded_domain)
            logger.info(f"[WHOIS-Query] 尝试使用源: {api['name']}")

            if httpx is not None:
                async with httpx.AsyncClient(
                    headers=HEADERS,
                    timeout=HTTP_TIMEOUT,
                    trust_env=USE_SYSTEM_PROXY,
                ) as client:
                    response = await client.get(url)
                    if response.status_code in {403, 429}:
                        logger.warning(
                            f"[WHOIS-Query] 源 {api['name']} 触发风控，正在尝试下一个..."
                        )
                        continue
                    response.raise_for_status()
                    data = response.json()
            else:
                data = await _fetch_json(url)

            if api["type"] == "primary" and _is_primary_response(data):
                return format_primary_whois(data)

            if api["type"] == "backup":
                backup_data = _get_backup_data(data)
                if backup_data is not None:
                    return format_backup_whois(backup_data)
        except (
            error.URLError,
            error.HTTPError,
            ValueError,
            TimeoutError,
            ConnectionError,
            json.JSONDecodeError,
        ) as exc:
            logger.error(f"[WHOIS-Query] 源 {api['name']} 请求出错: {exc}")
            continue
        except Exception as exc:
            logger.error(f"[WHOIS-Query] 源 {api['name']} 请求出错: {exc}")
            continue

    return WHOIS_ALL_API_FAILED_MESSAGE
