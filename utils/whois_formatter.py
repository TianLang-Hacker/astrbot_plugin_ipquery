from datetime import datetime
from pathlib import Path
from typing import Any


def _load_status_map() -> dict[str, str]:
    """读取 WHOIS 状态码汉化表。"""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 兼容
        try:
            import tomli as tomllib
        except ModuleNotFoundError:
            return {}

    try:
        with (Path(__file__).with_name("status_map.toml")).open("rb") as file:
            mapping = tomllib.load(file)
    except (OSError, ValueError):
        return {}

    return {
        str(status): str(translation)
        for status, translation in mapping.items()
        if isinstance(translation, str)
    }


STATUS_MAP = _load_status_map()


def _display(value: Any) -> str:
    """将空值显示为字面量 null，避免 WHOIS 结果中出现 None。"""
    if value is None:
        return "null"
    if isinstance(value, str):
        return value if value.strip() else "null"
    if isinstance(value, (list, tuple)):
        if not value:
            return "null"
        return ", ".join(_display(entry) for entry in value)
    return str(value)


def _field(data: dict[str, Any], key: str) -> str:
    return _display(data.get(key))


def _format_date(value: Any) -> str:
    """将 WHOIS 日期格式化为 yyyy年 MM月dd日 HH:mm:ss。"""
    displayed = _display(value)
    if displayed == "null":
        return displayed

    date_text = displayed
    if date_text.endswith("Z"):
        date_text = f"{date_text[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(date_text)
        return parsed.strftime("%Y年 %m月%d日 %H:%M:%S")
    except ValueError:
        # 对无法解析的异常日期，至少按要求去除末尾的 Z。
        return displayed[:-1] if displayed.endswith("Z") else displayed


def _format_status(value: Any) -> str:
    def translate(status: Any) -> str:
        displayed = _display(status)
        return STATUS_MAP.get(displayed, displayed)

    if isinstance(value, (list, tuple)):
        if not value:
            return "null"
        return ", ".join(translate(status) for status in value)
    if isinstance(value, str):
        displayed = _display(value)
        if displayed == "null":
            return displayed
        return ", ".join(translate(status.strip()) for status in displayed.split(","))
    return _display(value)


def format_primary_whois(data: dict[str, Any]) -> str:
    """格式化 who-dat.as93.net 返回的 WHOIS 数据。"""
    registrar = data.get("registrar") or {}
    dates = data.get("dates") or {}
    contacts = data.get("contacts") or {}
    registrant = contacts.get("registrant") or {}
    meta = data.get("meta") or {}
    nameservers = data.get("nameservers") or []

    nameserver_lines = []
    for nameserver in nameservers:
        nameserver = nameserver if isinstance(nameserver, dict) else {}
        nameserver_lines.extend(
            (
                f"  名称: {_field(nameserver, 'name')}",
                f"  IPv4: {_field(nameserver, 'ipv4')}",
                f"  IPv6: {_field(nameserver, 'ipv6')}",
            )
        )
    nameserver_text = "\n".join(nameserver_lines) if nameserver_lines else "  null"

    return (
        "WHOIS 查询结果 (主用源：who-dat.as93.net):\n"
        "------------------\n"
        f"查询: {_field(data, 'query')}\n"
        f"域名: {_field(data, 'domain')}\n"
        f"顶级域名: {_field(data, 'tld')}\n"
        f"是否已注册: {_field(data, 'isRegistered')}\n"
        "\n"
        "注册商:\n"
        f"  名称: {_field(registrar, 'name')}\n"
        f"  IANA ID: {_field(registrar, 'ianaId')}\n"
        f"  URL: {_field(registrar, 'url')}\n"
        f"  WHOIS 服务器: {_field(registrar, 'whoisServer')}\n"
        f"状态: {_format_status(data.get('status'))}\n"
        "\n"
        "名称服务器:\n"
        f"{nameserver_text}\n"
        "\n"
        "日期:\n"
        f"  创建时间: {_format_date(dates.get('created'))}\n"
        f"  更新时间: {_format_date(dates.get('updated'))}\n"
        f"  到期时间: {_format_date(dates.get('expires'))}\n"
        "\n"
        "注册人:\n"
        f"  姓名: {_field(registrant, 'name')}\n"
        f"  组织: {_field(registrant, 'organization')}\n"
        f"  邮箱: {_field(registrant, 'email')}\n"
        f"  电话: {_field(registrant, 'phone')}\n"
        f"  注册商隐私保护: {_field(registrant, 'redacted')}\n"
        "\n"
        "元数据:\n"
        f"  数据来源协议: {_field(meta, 'source')}\n"
        f"  服务器: {_field(meta, 'server')}\n"
        f"  是否缓存: {_field(meta, 'cached')}\n"
        "------------------"
    )


def format_backup_whois(data: dict[str, Any]) -> str:
    """格式化 v2.xxapi.cn 返回的 WHOIS 数据。"""
    return (
        "WHOIS 查询结果 (备用源：v2.xxapi.cn):\n"
        "------------------\n"
        f"域名: {_field(data, 'domain_name')}\n"
        f"状态: {_format_status(data.get('domain_status'))}\n"
        f"注册时间: {_format_date(data.get('registration_time'))}\n"
        f"到期时间: {_format_date(data.get('expiration_time'))}\n"
        f"注册人: {_field(data, 'registrant')}\n"
        f"注册人邮箱: {_field(data, 'registrant_contact_email')}\n"
        f"注册商 URL: {_field(data, 'registrar_url')}\n"
        f"DNS 服务器: {_field(data, 'dns_serve')}\n"
        "------------------"
    )
