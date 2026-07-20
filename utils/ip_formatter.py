def format_primary_res(data: dict) -> str:
    """格式化主接口（ip-api.com / 镜像）返回的数据"""

    ip_tags = []

    if data.get("mobile"):
        ip_tags.append("这个IP可能是蜂窝移动网络")

    if data.get("proxy"):
        ip_tags.append("这个IP可能是代理/VPN IP")

    if data.get("hosting"):
        ip_tags.append("这个IP可能是数据中心/机房IP")

    tag_str = "\n".join(ip_tags) if ip_tags else "这个IP可能是家庭宽带或者其他IP"

    lat = data.get("lat", 0)
    lon = data.get("lon", 0)

    lat_dir = "北纬" if lat >= 0 else "南纬"
    lon_dir = "东经" if lon >= 0 else "西经"

    return (
        f"IP 查询结果 (主用源：ip-api.com):\n"
        f"------------------\n"
        f"查询 IP: {data.get('query')}\n"
        f"归属地: {data.get('country')} - {data.get('regionName')} - {data.get('city')}\n"
        f"国家/地区代码: {data.get('countryCode')}\n"
        f"大陆: {data.get('continent')}\n"
        f"运营商: {data.get('isp')}\n"
        f"时区: {data.get('timezone')}\n"
        f"组织: {data.get('org')}\n"
        f"AS号: {data.get('as')}\n"
        f"坐标: {lat_dir}{abs(lat)}°, {lon_dir}{abs(lon)}°\n"
        f"{tag_str}\n"
        f"------------------"
    )


def format_backup_res(data: dict) -> str:
    """格式化备用接口（ipapi.co）返回的数据"""

    latitude = data.get("latitude", 0)
    longitude = data.get("longitude", 0)

    lat_dir = "北纬" if latitude >= 0 else "南纬"
    lon_dir = "东经" if longitude >= 0 else "西经"

    return (
        f"IP 查询结果 (备用源：ipapi.co):\n"
        f"------------------\n"
        f"查询 IP: {data.get('ip')}\n"
        f"归属地: {data.get('country_name')} - {data.get('region')} - {data.get('city')}\n"
        f"国家/地区代码: {data.get('country_code')}\n"
        f"大陆: {data.get('continent_code')}\n"
        f"运营商: {data.get('isp')}\n"
        f"时区: {data.get('timezone')}\n"
        f"组织: {data.get('org')}\n"
        f"AS号: {data.get('asn')}\n"
        f"坐标: {lat_dir}{abs(latitude)}°, {lon_dir}{abs(longitude)}°\n"
        f"该源不支持查看IP类型\n"
        f"------------------"
    )