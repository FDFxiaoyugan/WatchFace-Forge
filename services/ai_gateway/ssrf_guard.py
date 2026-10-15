"""BYOK base_url 出站防护（审计 S3 修复）。

无条件硬检查（所有模式生效）:
- 复核 HTTPS、无内嵌凭据、无 query/fragment（与 normalize_user_ai_config 一致）
- 主机名解析出的**全部** A/AAAA 地址不得落入私网/回环/链路本地/保留/
  组播/CGN 段；主机名是 IP 字面量时直接判定
- 解析失败 → 拒绝（fail-closed）

可选白名单（部署者收紧）:
- WF_AI_ALLOWED_HOSTS="api.openai.com,api.deepseek.com"（逗号分隔，
  支持 "*.example.com" 后缀通配）
- 配置后 hostname 必须命中白名单
- **WF_ENV=production 且未配置 → 默认拒绝**自定义 Base URL（复查 R3：
  生产环境显式收紧是部署前提，非可选项；development 未配置 = 允许任意
  通过硬检查的公网地址，保留单机 BYOK 可用性）

已知限制（第一阶段）:
- 校验与实际连接间存在 DNS rebinding TOCTOU 窗口；连接级 IP pinning 属
  后续工作。重定向面已闭合：AIGateway._call_openai 显式传入
  follow_redirects=False 的 httpx client（openai SDK 默认会跟随重定向）。
"""

import ipaddress
import os
import socket
from urllib.parse import urlparse

from . import AIConfigError

# 显式补充段（Python ipaddress 属性覆盖不了的）
_EXTRA_BLOCKED_V4 = [
    ipaddress.ip_network("100.64.0.0/10"),   # CGN / 运营商级 NAT
    ipaddress.ip_network("192.0.0.0/24"),    # IETF 协议赋值
    ipaddress.ip_network("198.18.0.0/15"),   # benchmarking
]


def _is_forbidden_ip(ip) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return True
    if ip.version == 4:
        return any(ip in net for net in _EXTRA_BLOCKED_V4)
    return False


def _resolve_all_ips(hostname: str) -> list:
    """getaddrinfo 全量解析（A/AAAA）。失败抛 OSError。"""
    results = []
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            infos = socket.getaddrinfo(hostname, None, family, socket.SOCK_STREAM)
        except socket.gaierror:
            continue
        for info in infos:
            sockaddr = info[4]
            addr = sockaddr[0]
            results.append(ipaddress.ip_address(addr))
    return results


def _hostname_allowed(hostname: str) -> bool:
    """白名单未配置 → True（仅硬检查生效）；配置了 → 精确/后缀通配匹配。"""
    raw = os.environ.get("WF_AI_ALLOWED_HOSTS", "").strip()
    if not raw:
        return True
    host = hostname.lower().rstrip(".")
    for entry in raw.split(","):
        entry = entry.strip().lower()
        if not entry:
            continue
        if entry.startswith("*."):
            suffix = entry[1:]  # ".example.com"
            if host.endswith(suffix):
                return True
        elif host == entry:
            return True
    return False


def _is_production() -> bool:
    return os.environ.get("WF_ENV", "development").strip().lower() == "production"


def assert_safe_base_url(base_url: str) -> None:
    """校验 BYOK base_url 的出站安全性；不安全时抛 AIConfigError。"""
    if not base_url:
        return
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise AIConfigError("自定义 Base URL 必须是 HTTPS 地址")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AIConfigError("自定义 Base URL 不能包含内嵌凭据/查询参数/片段")

    hostname = parsed.hostname
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None

    # 复查 R3: 生产模式白名单是部署前提——未配置即拒绝自定义 Base URL
    # （用户仍可用服务端默认 AI；仅 BYOK 自定义端点被收紧）。
    # 注意放在 DNS 解析之前：不给未配置白名单的生产实例做任意域名解析探测。
    if _is_production():
        raw = os.environ.get("WF_AI_ALLOWED_HOSTS", "").strip()
        if not raw:
            raise AIConfigError(
                "生产环境使用自定义 Base URL 需先配置 WF_AI_ALLOWED_HOSTS"
            )

    if literal is not None:
        if _is_forbidden_ip(literal):
            raise AIConfigError("自定义 Base URL 指向内部/保留地址，已被拒绝")
        ips = [literal]
    else:
        try:
            ips = _resolve_all_ips(hostname)
        except (socket.gaierror, OSError):
            raise AIConfigError("自定义 Base URL 的域名无法解析")
        if not ips:
            raise AIConfigError("自定义 Base URL 的域名没有可用地址")
        for ip in ips:
            if _is_forbidden_ip(ip):
                # 不回显解析出的地址，避免探测辅助
                raise AIConfigError(
                    "自定义 Base URL 解析到内部/保留地址，已被拒绝")

    if not _hostname_allowed(hostname):
        raise AIConfigError(
            "自定义 Base URL 的域名不在服务端允许列表（WF_AI_ALLOWED_HOSTS）")
