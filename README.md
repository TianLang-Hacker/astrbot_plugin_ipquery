# IP Query

一个用于查询IP地理位置及类型的插件

---

### 特别声明

> **本插件的代码核心逻辑由 Google Gemini 生成。**

## 如何使用

/ip x.x.x.x 把x.x.x.x替换成你需要搜索的IP地址即可 例：/ip 8.8.8.8

## 支持

有什么建议欢迎提交 [Github Issue](https://github.com/TianLang-Hacker/astrbot_plugin_ipquery/issues)

#### 注：

- 如果挂系统代理的时候频繁出现请稍后再试，或检查此 IP 是否已被 API 服务商拉黑.如果使用的是Clash（Mihomo）工具，请在配置文件里添加以下规则：

```yaml
rules:
  - DOMAIN-SUFFIX,ip-api.com,DIRECT # 用于 ip-api.com 直连 IP
  - DOMAIN-SUFFIX,is.snappytree.com,DIRECT # 用于 ip-api.com镜像源直连 IP
  - DOMAIN-SUFFIX,ipapi.co,DIRECT # 用于 ipapi.co 直连 IP
```

- 如果使用的是其他代理工具建议自行寻找直连方法，核心逻辑就是将以下API URL加入白名单或者设置直连规则即可

```bash
ip-api.com
is.snappytree.com
ipapi.co
```

- 当然不妨就是有人喜欢用代理 IP 使用此服务，在 /AstrBot/data/plugins/astrbot_plugin_ipquery/main.py 第41行删除trust_env=True即可

```python
# async with httpx.AsyncClient(headers=headers, timeout=8, trust_env=True) as client: 修改成以下代码即可
async with httpx.AsyncClient(headers=headers, timeout=8) as client:
```
修改完成后在 Astrbot 后台 Astrbot 插件中心重载插件即可

## 更新日志

### version 0.0.3

- 修复了在Docker环境下API容易频繁 403 Forbidden 的报错（也许吧，毕竟我反正是测不出来了）

- 修改了经纬度显示的逻辑

### Version 0.0.2

- 修复了经纬度错误显示的问题