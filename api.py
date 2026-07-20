# IP 查询 API 配置

IP_APIS = [
    {
        "name": "ip-api.com",
        "url": "http://ip-api.com/json/{}?fields=66846719",
        "type": "primary",
    },
    {
        "name": "snappytree镜像",
        "url": "https://is.snappytree.com/api/ipapi/{}",
        "type": "primary",
    },
    {
        "name": "ipapi.co备用",
        "url": "https://ipapi.co/{}/json/",
        "type": "backup",
    },
]

# HTTP 请求头
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# HTTP 请求超时时间（秒）
HTTP_TIMEOUT = 8

# 是否使用系统代理
# True：使用系统代理（如 Clash、Mihomo）
# False：直连
USE_SYSTEM_PROXY = True

# 查询失败提示
ALL_API_FAILED_MESSAGE = (
    "❌ 所有查询接口均已失效或达到频率上限。\n"
    "💡 建议：请稍后再试，或检查此查询目标是否已被 API 服务商限制。"
)
