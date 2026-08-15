"""
表盘预览图渲染器

根据 CDM 配置生成 384x384 PNG 预览图,
尽量还原实际表盘外观。
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math


def _parse_color(argb: str) -> tuple:
    """#ffRRGGBB → (R, G, B, A)"""
    a = int(argb[2:4], 16)
    r = int(argb[4:6], 16)
    g = int(argb[6:8], 16)
    b = int(argb[8:10], 16) if len(argb) > 8 else int(argb[6:8], 16)
    return (r, g, b, a)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取系统字体"""
    path = "/usr/share/fonts/truetype/chinese/"
    name = "NotoSansSC-Bold.otf" if bold else "NotoSansSC-Regular.otf"
    try:
        return ImageFont.truetype(path + name, size)
    except Exception:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except Exception:
            return ImageFont.load_default()


def render_preview(path: Path, cdm) -> None:
    """渲染表盘预览图"""
    size = 384
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    max_r = size // 2

    # ── 背景 ──
    bg = cdm.background
    if bg.type == "solid":
        br, bg_, bb, _ = _parse_color(bg.color)
        for r in range(max_r, 0, -1):
            t = r / max_r
            cr = int(br * (1 - t * 0.6))
            cg = int(bg_ * (1 - t * 0.6))
            cb = int(bb * (1 - t * 0.6))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(cr, cg, cb, 255))
    elif bg.type == "gradient" and bg.gradient_start and bg.gradient_end:
        sr, sg, sb, _ = _parse_color(bg.gradient_start)
        er, eg, eb, _ = _parse_color(bg.gradient_end)
        for r in range(max_r, 0, -1):
            t = 1 - r / max_r
            cr = int(sr + (er - sr) * t)
            cg = int(sg + (eg - sg) * t)
            cb = int(sb + (eb - sb) * t)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(cr, cg, cb, 255))
    else:
        draw.ellipse([0, 0, size, size], fill=(0, 0, 0, 255))

    # ── 数字表盘 ──
    if cdm.clock_type.value == "DIGITAL" and cdm.digital_time.enabled:
        dt = cdm.digital_time
        tr, tg, tb, _ = _parse_color(dt.font.color)

        font_size = int(dt.font.size * 0.7)  # 缩放适配预览
        font = _get_font(font_size, bold=(dt.font.weight.value == "BOLD"))
        text = "10:08"

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = cx - tw // 2
        ty = cy - th // 2 - 30
        draw.text((tx, ty), text, fill=(tr, tg, tb, 255), font=font)

        # 日期
        if cdm.date_display.enabled:
            dd = cdm.date_display
            dr, dg, db, _ = _parse_color(dd.font.color)
            dfont = _get_font(int(dd.font.size * 0.6))
            dtext = "08/15"
            dbbox = draw.textbbox((0, 0), dtext, font=dfont)
            dw = dbbox[2] - dbbox[0]
            draw.text((cx - dw // 2, cy + 40), dtext, fill=(dr, dg, db, 255), font=dfont)

        # 信息行
        if cdm.info_line.enabled:
            info = cdm.info_line
            ir, ig, ib, _ = _parse_color(info.font.color)
            ifont = _get_font(int(info.font.size * 0.6))
            itext = f"{info.label} 85%"
            ibbox = draw.textbbox((0, 0), itext, font=ifont)
            iw = ibbox[2] - ibbox[0]
            draw.text((cx - iw // 2, cy + 80), itext, fill=(ir, ig, ib, 255), font=ifont)

    # ── 模拟表盘 ──
    elif cdm.clock_type.value == "ANALOG" and cdm.analog_time.enabled:
        at = cdm.analog_time

        # 表盘外圈
        draw.ellipse([cx - 160, cy - 160, cx + 160, cy + 160],
                     outline=(200, 200, 200, 100), width=2)

        # 12个刻度
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            x1 = cx + math.cos(angle) * 150
            y1 = cy + math.sin(angle) * 150
            x2 = cx + math.cos(angle) * 140
            y2 = cy + math.sin(angle) * 140
            width = 3 if i % 3 == 0 else 1
            draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200, 200), width=width)

        # 时针 (指向 10 点)
        hr, hg, hb, _ = _parse_color(at.hour_hand_color)
        h_angle = math.radians(-60)
        hx2 = cx + math.cos(h_angle) * at.hour_hand_length * 0.7
        hy2 = cy + math.sin(h_angle) * at.hour_hand_length * 0.7
        draw.line([(cx, cy), (hx2, hy2)], fill=(hr, hg, hb, 255), width=6)

        # 分针 (指向 8 分)
        mr, mg, mb, _ = _parse_color(at.minute_hand_color)
        m_angle = math.radians(-48)
        mx2 = cx + math.cos(m_angle) * at.minute_hand_length * 0.7
        my2 = cy + math.sin(m_angle) * at.minute_hand_length * 0.7
        draw.line([(cx, cy), (mx2, my2)], fill=(mr, mg, mb, 255), width=4)

        # 秒针 (指向 32 秒)
        if at.second_hand_length > 0:
            sr, sg, sb, _ = _parse_color(at.second_hand_color)
            s_angle = math.radians(96)
            sx2 = cx + math.cos(s_angle) * at.second_hand_length * 0.7
            sy2 = cy + math.sin(s_angle) * at.second_hand_length * 0.7
            draw.line([(cx, cy), (sx2, sy2)], fill=(sr, sg, sb, 255), width=2)

        # 中心点
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(200, 200, 200, 255))

    # 圆形裁剪
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size, size], fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    result.save(path, "PNG", optimize=True)
