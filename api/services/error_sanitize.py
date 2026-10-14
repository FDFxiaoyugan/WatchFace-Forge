"""Client-facing error sanitization (fixes audit: internal exceptions leaked
to API responses via ``str(exc)``).

Policy:
- Unhandled exceptions NEVER return their raw message to clients. The client
  gets a stable generic message plus a short ``request_id``; the full
  traceback is logged server-side (logger ``watchface_forge.errors``).
- Known deployment/tool failures are matched by substring and mapped to
  fixed, actionable messages that contain no server paths or secrets.
- ValueError from validated user-input paths is intentionally NOT routed
  through here: callers surface it as an input error, because those messages
  originate from our own validation code (fixed strings, no paths).
"""

import logging
import uuid

logger = logging.getLogger("watchface_forge.errors")

# (substring in str(exc), safe client message). Order matters: first match wins.
_KNOWN_TOOL_ERRORS: list[tuple[str, str]] = [
    (
        "apksigner not found",
        "签名工具不可用：服务器缺少 Android 构建工具，请配置 ANDROID_HOME / APKSIGNER",
    ),
    (
        "precompiled template is incomplete",
        "构建资源缺失：Android 构建工具不可用且预编译模板不完整",
    ),
    (
        "keystore",
        "签名密钥配置无效：请检查 keystore 路径、密码与 alias 配置",
    ),
    (
        "aapt2",
        "aapt2 资源编译失败：构建环境异常或资源非法",
    ),
]

_GENERIC_TEMPLATE = "构建失败（内部错误 {request_id}，详见服务端日志）"


def safe_client_error(exc: Exception, context: str = "") -> tuple[str, str]:
    """Return ``(client_message, request_id)`` for an unhandled exception.

    ``context`` is a short server-side tag (e.g. ``"build:ab12cd34"``) that is
    logged together with the traceback — it must not contain user input.
    """
    request_id = uuid.uuid4().hex[:12]
    text = str(exc) or exc.__class__.__name__
    for pattern, safe_msg in _KNOWN_TOOL_ERRORS:
        if pattern in text:
            logger.warning(
                "known build failure in %s [request_id=%s]: %s",
                context, request_id, text,
            )
            return safe_msg, request_id
    logger.exception(
        "unhandled error in %s [request_id=%s]", context, request_id,
    )
    return _GENERIC_TEMPLATE.format(request_id=request_id), request_id
