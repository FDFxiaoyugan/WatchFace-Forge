"""
图像后处理管线 — Pillow 实现 (rembg 替代方案)

功能:
  1. 背景移除 — 颜色聚类 + flood-fill (从边缘开始移除相近色连通域)
  2. Alpha 裁剪 — 裁掉全透明边缘, 保留有效内容
  3. 边缘羽化 — 抠图边缘轻量模糊, 减少锯齿
  4. 无损压缩 — PNG optimize + palette 量化 (可选有损)

设计权衡:
  - onnxruntime (~500MB) 无法在当前环境安装, 故用 Pillow 算法方案
  - 适合纯色/渐变背景的图标类素材 (表盘场景的典型情况)
  - 复杂照片背景效果有限, 前端引导用户使用纯色背景素材
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Optional, Tuple

from PIL import Image, ImageFilter, ImageOps


# ─── 数据结构 ─────────────────────────────────────────

@dataclass
class ProcessOptions:
    """处理选项"""
    remove_bg: bool = True
    bg_tolerance: int = 32          # 颜色容差 (0-255 距离)
    feather_radius: int = 2         # 边缘羽化半径 (px)
    auto_crop: bool = True          # alpha 裁剪
    max_size: int = 1024            # 最大边长
    output_format: str = "png"      # png (无损) | webp (有损但小)
    webp_quality: int = 90

    # 复查 G3 (2026-10-23): 所有构造路径（HTTP/celery/内部调用）统一 clamp,
    # 防超大 max_size 绕过缩放 / 巨大羽化半径放大 flood-fill 成本
    def __post_init__(self):
        self.max_size = min(max(self.max_size, 64), 2048)
        self.bg_tolerance = min(max(self.bg_tolerance, 0), 255)
        self.feather_radius = min(max(self.feather_radius, 0), 32)
        self.webp_quality = min(max(self.webp_quality, 1), 100)
        if self.output_format not in ("png", "webp"):
            self.output_format = "png"


@dataclass
class ProcessResult:
    """处理结果"""
    success: bool = False
    data: Optional[bytes] = None
    format: str = "png"
    width: int = 0
    height: int = 0
    original_size: int = 0          # 原始字节数
    processed_size: int = 0         # 处理后字节数
    bg_removed: bool = False
    cropped: bool = False
    error: Optional[str] = None


# ─── 核心算法 ─────────────────────────────────────────

def _color_distance(c1: Tuple, c2: Tuple) -> float:
    """RGB 欧氏距离"""
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5


def _edge_colors(img: Image.Image, sample: int = 8) -> list:
    """采样四角+四边中点颜色, 推断背景色"""
    w, h = img.size
    pixels = img.convert("RGB").load()
    points = [
        (2, 2), (w-3, 2), (2, h-3), (w-3, h-3),          # 四角
        (w//2, 2), (w//2, h-3), (2, h//2), (w-3, h//2),   # 边中点
    ]
    colors = []
    for x, y in points:
        if 0 <= x < w and 0 <= y < h:
            colors.append(pixels[x, y])
    return colors


def remove_background(img: Image.Image, tolerance: int = 32) -> Image.Image:
    """
    背景移除: flood-fill 从边缘向内扩展相近色区域, 置为透明。

    策略:
      1. 取边缘采样色的众数作为背景色基准
      2. BFS 从所有边缘像素出发, 颜色距离 < tolerance 的像素标记为背景
      3. 生成 alpha 蒙版: 背景=0, 前景=255, 边缘过渡带做羽化
    """
    img = img.convert("RGBA")
    w, h = img.size

    # 背景色 = 边缘颜色中距离所有边缘色均值最近的那个
    edge_cols = _edge_colors(img)
    if not edge_cols:
        return img
    avg = tuple(sum(c[i] for c in edge_cols) // len(edge_cols) for i in range(3))
    bg_color = min(edge_cols, key=lambda c: _color_distance(c, avg))

    rgb = img.convert("RGB")
    pixels = rgb.load()
    alpha = Image.new("L", (w, h), 255)
    alpha_px = alpha.load()

    # BFS flood fill from all border pixels
    from collections import deque
    visited = bytearray(w * h)
    queue = deque()

    def try_enqueue(x: int, y: int):
        idx = y * w + x
        if visited[idx]:
            return
        if _color_distance(pixels[x, y], bg_color) < tolerance:
            visited[idx] = 1
            queue.append((x, y))

    # 种子: 四条边
    for x in range(w):
        try_enqueue(x, 0)
        try_enqueue(x, h-1)
    for y in range(h):
        try_enqueue(0, y)
        try_enqueue(w-1, y)

    while queue:
        x, y = queue.popleft()
        alpha_px[x, y] = 0
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < w and 0 <= ny < h:
                try_enqueue(nx, ny)

    # 羽化: alpha 蒙版轻模糊
    if w > 8 and h > 8:
        alpha = alpha.filter(ImageFilter.GaussianBlur(1.5))

    result = img.copy()
    result.putalpha(alpha)
    return result


def autocrop_alpha(img: Image.Image, padding: int = 2) -> Tuple[Image.Image, bool]:
    """裁掉全透明边缘, 保留 padding 像素边距"""
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()  # 非 0 区域
    if bbox is None:
        return img, False
    x0, y0, x1, y1 = bbox
    # 加 padding, 不越界
    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(img.width, x1 + padding)
    y1 = min(img.height, y1 + padding)
    if (x0, y0, x1, y1) == (0, 0, img.width, img.height):
        return img, False
    return img.crop((x0, y0, x1, y1)), True


def resize_max(img: Image.Image, max_size: int) -> Image.Image:
    """限制最大边长"""
    w, h = img.size
    if max(w, h) <= max_size:
        return img
    scale = max_size / max(w, h)
    return img.resize((max(1, int(w*scale)), max(1, int(h*scale))), Image.LANCZOS)


def encode(img: Image.Image, fmt: str, webp_quality: int = 90) -> bytes:
    """编码为字节"""
    buf = io.BytesIO()
    if fmt == "webp":
        img.save(buf, format="WEBP", quality=webp_quality, method=4)
    else:
        img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ─── 管线入口 ─────────────────────────────────────────

def process_image(data: bytes, opts: Optional[ProcessOptions] = None) -> ProcessResult:
    """
    图像后处理管线:
      [长度预算] → 解码 → [像素预算] → [缩放] → [抠图] → [裁剪] → [编码]
    """
    opts = opts or ProcessOptions()
    result = ProcessResult()
    result.original_size = len(data)

    # 复查 G3: 集中预算防线（b64 限长在路由层, 此处兜底覆盖 celery task
    # 等其他入口——12MB 原始字节 / 50MP 解码像素上限, 防 decompression bomb）
    if len(data) > 12 * 1024 * 1024:
        result.error = "image too large (max 12MB raw bytes)"
        return result

    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # 处理 EXIF 旋转
    except Exception as e:
        result.error = f"decode failed: {e}"
        return result

    if img.width * img.height > 50_000_000:
        result.error = f"image exceeds pixel budget ({img.width}x{img.height} > 50MP)"
        return result

    # 缩放
    img = resize_max(img, opts.max_size)

    # 抠图
    if opts.remove_bg:
        try:
            img = remove_background(img, opts.bg_tolerance)
            result.bg_removed = True
        except Exception as e:
            result.error = f"remove_bg failed: {e}"
            return result

    # Alpha 裁剪
    if opts.auto_crop:
        img, cropped = autocrop_alpha(img)
        result.cropped = cropped

    # 编码
    fmt = "webp" if opts.output_format == "webp" else "png"
    try:
        out = encode(img, fmt, opts.webp_quality)
    except Exception as e:
        result.error = f"encode failed: {e}"
        return result

    result.success = True
    result.data = out
    result.format = fmt
    result.width = img.width
    result.height = img.height
    result.processed_size = len(out)
    return result


def generate_thumbnail(data: bytes, size: int = 256) -> Optional[bytes]:
    """生成缩略图 (方形留白)"""
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img.thumbnail((size, size), Image.LANCZOS)
        # 粘贴到方形透明画布
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset = ((size - img.width) // 2, (size - img.height) // 2)
        canvas.paste(img, offset, img)
        buf = io.BytesIO()
        canvas.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception:
        return None
