#!/usr/bin/env python3
"""version×construct 矩阵复测探针生成器 (REPAIR_PLAN P1)

生成 3 个探针项目 (experiments/version-matrix/v{1,2,4}/):
  C1 表达式驱动 Transform  — Rush-Hour-Reply (format.version=2 成品) 原构造照抄
  C2 Transform+Animation 时间线 — R53 原构造 (真机不渲染的对照组)
  C3 Gyro 视差 — gyroElements.xsd 官方文档示例表达式 (R54 原构造, 幅度放大到 ±25)
  C4 PartText+BitmapFont — R61 矩阵 D 通道原构造 (floor 数值源)
  C5 帧序列呼吸 — R55 真机实证可用的正控制 (PartAnimatedImage+SequenceImages)

唯一自变量 = project.yaml 的 wff_version (1/2/4); minSdk 恒定 34 隔离变量。
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent

# ---------- 资源生成 ----------

SEG = {  # 七段数码管
    "0": "ABCDEF", "1": "BC", "2": "ABGED", "3": "ABGCD", "4": "FGBC",
    "5": "AFGCD", "6": "AFGEDC", "7": "ABC", "8": "ABCDEFG", "9": "ABCDFG",
}

def seg_rects(w, h):
    """返回七段矩形: A 顶 / B 右上 / C 右下 / D 底 / E 左下 / F 左上 / G 中"""
    t = max(3, w // 7)  # 段厚
    return {
        "A": (t, 0, w - t, t),
        "B": (w - t, t, w, h // 2),
        "C": (w - t, h // 2, w, h - t),
        "D": (t, h - t, w - t, h),
        "E": (0, h // 2, t, h - t),
        "F": (0, t, t, h // 2),
        "G": (t, h // 2 - t // 2, w - t, h // 2 + t // 2),
    }

def make_glyph(d: str, w=28, h=48):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for s in SEG[d]:
        dr.rectangle(seg_rects(w, h)[s], fill=(255, 255, 255, 255))
    return img

def make_breath_frame(i, n=30, size=80):
    """呼吸帧: alpha 三角波整周期 (首尾同值, R55 要点), 60→255→60"""
    a = int(60 + 195 * (0.5 - 0.5 * math.cos(2 * math.pi * i / n)))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx = size // 2
    dr.ellipse([cx - 22, cx - 22, cx + 22, cx + 22], fill=(61, 220, 132, a))
    dr.ellipse([cx - 32, cx - 32, cx + 32, cx + 32], outline=(61, 220, 132, max(40, a - 60)), width=3)
    return img

def load_font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make_preview(version: str):
    img = Image.new("RGB", (450, 450), (0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.ellipse([8, 8, 442, 442], outline=(60, 60, 60), width=2)
    f_title, f_lbl = load_font(26), load_font(20)
    dr.text((225, 24), f"MATRIX v{version}", fill=(240, 240, 240), font=f_title, anchor="ma")
    # C1 轨道 + 青点
    dr.ellipse([217 - 140, 225 - 140, 223 + 140, 227 + 140], outline=(40, 60, 70), width=1)
    dr.ellipse([206, 66, 244, 104], fill=(0, 229, 255))
    dr.text((225, 58), "C1", fill=(154, 160, 168), font=f_lbl, anchor="ma")
    # C2 红点扫描线
    dr.line([(30, 182), (330, 182)], fill=(70, 30, 30), width=2)
    dr.ellipse([40, 164, 76, 200], fill=(255, 85, 85))
    dr.text((65, 136), "C2", fill=(154, 160, 168), font=f_lbl, anchor="ma")
    # C3 金点 (陀螺)
    dr.ellipse([208, 208, 242, 242], fill=(255, 213, 79))
    dr.text((262, 216), "C3", fill=(154, 160, 168), font=f_lbl, anchor="ma")
    # C4 位图字
    dr.text((225, 388), "42", fill=(0, 229, 255), font=load_font(48), anchor="ma")
    dr.text((90, 332), "C4", fill=(154, 160, 168), font=f_lbl, anchor="ma")
    # C5 呼吸
    dr.ellipse([360, 132, 416, 188], fill=(61, 220, 132))
    dr.text((388, 106), "C5", fill=(154, 160, 168), font=f_lbl, anchor="ma")
    return img

# ---------- 表盘 XML ----------

XML_TEMPLATE = """<?xml version="1.0"?>
<!-- version×construct 矩阵探针 v{V} (REPAIR_PLAN P1)
     C1 表达式 Transform(Rush-Hour v2 成品原构造) / C2 Transform+Animation(R53 原构造)
     C3 Gyro(官方 XSD 示例) / C4 PartText+BitmapFont(R61 D 通道) / C5 帧序列(R55 正控制) -->
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <BitmapFonts>
        <BitmapFont name="probeDigits">
{GLYPHS}
        </BitmapFont>
    </BitmapFonts>
    <UserConfigurations>
        <ColorConfiguration id="probeTheme" defaultValue="0" displayName="probe_color" screenReaderText="probe_color">
            <ColorOption id="0" colors="#ff00e5ff #ffff5555 #ffffd54f" displayName="opt0" screenReaderText="opt0"/>
        </ColorConfiguration>
    </UserConfigurations>
    <Scene backgroundColor="#ff000000">

        <PartText x="0" y="6" width="450" height="34" name="title">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="24" weight="BOLD" color="#fff2f5f8">MATRIX v{V}</Font></Text>
        </PartText>

        <!-- C1: 表达式驱动 Transform, [SECOND_MILLISECOND]*6 平滑秒针 (Rush-Hour 原式) -->
        <PartText x="185" y="44" width="80" height="22" name="lbl_c1">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="18" color="#ff9aa0a8">C1</Font></Text>
        </PartText>
        <Group x="0" y="0" width="450" height="450" angle="0" name="c1_sweep">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Transform target="angle" value="[SECOND_MILLISECOND] * 6"/>
            <PartDraw x="206" y="66" width="38" height="38" name="c1_dot">
                <Ellipse x="0" y="0" width="38" height="38"><Fill color="#ff00e5ff"/></Ellipse>
            </PartDraw>
        </Group>

        <!-- C2: Transform+Animation 时间线 (R53 原构造) -->
        <PartText x="60" y="130" width="60" height="22" name="lbl_c2">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="18" color="#ff9aa0a8">C2</Font></Text>
        </PartText>
        <Group x="30" y="160" width="80" height="44" name="c2_anim">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Transform target="x" value="[ANIMATION_VALUE] * 260">
                <Animation duration="2" repeat="-1" interpolation="EASE_IN_OUT" fps="30"/>
            </Transform>
            <PartDraw x="0" y="4" width="36" height="36" name="c2_dot">
                <Ellipse x="0" y="0" width="36" height="36"><Fill color="#ffff5555"/></Ellipse>
            </PartDraw>
        </Group>

        <!-- C3: Gyro 官方示例表达式 (幅度 ±25) -->
        <PartText x="250" y="212" width="40" height="22" name="lbl_c3">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="18" color="#ff9aa0a8">C3</Font></Text>
        </PartText>
        <Group x="188" y="188" width="74" height="74" name="c3_gyro">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Gyro
                x="(25/90) * clamp([ACCELEROMETER_ANGLE_X], 0, 90) + (-25/-90) * clamp([ACCELEROMETER_ANGLE_X], -90, 0)"
                y="(25/90) * clamp([ACCELEROMETER_ANGLE_Y], 0, 90) + (-25/-90) * clamp([ACCELEROMETER_ANGLE_Y], -90, 0)"/>
            <PartDraw x="17" y="17" width="40" height="40" name="c3_dot">
                <Ellipse x="0" y="0" width="40" height="40"><Fill color="#ffffd54f"/></Ellipse>
            </PartDraw>
        </Group>

        <!-- C4: PartText+BitmapFont (R61 D 通道) -->
        <PartText x="60" y="330" width="60" height="22" name="lbl_c4">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="18" color="#ff9aa0a8">C4</Font></Text>
        </PartText>
        <PartText x="130" y="352" width="190" height="70" name="c4_bitmapfont">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER">
                <BitmapFont family="probeDigits" size="48">
                    <Template><![CDATA[%s]]><Parameter expression="floor([SECOND])"/></Template>
                </BitmapFont>
            </Text>
        </PartText>

        <!-- C5: 帧序列呼吸 (R55 正控制) -->
        <PartText x="360" y="96" width="60" height="22" name="lbl_c5">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="18" color="#ff9aa0a8">C5</Font></Text>
        </PartText>
        <PartAnimatedImage x="348" y="120" width="80" height="80" name="c5_breath">
            <AnimationController play="ON_VISIBLE" repeat="TRUE" beforePlaying="FIRST_FRAME" afterPlaying="FIRST_FRAME"/>
            <SequenceImages>
{FRAMES}
            </SequenceImages>
        </PartAnimatedImage>

    </Scene>
</WatchFace>
"""

YAML_TEMPLATE = """# version×construct 矩阵探针 (REPAIR_PLAN P1)
package_name: com.watchface.matrixv{V}
version_code: 1
version_name: "1.0"
watch_face_name: Matrix Probe v{V}
wff_version: {V}
min_sdk: 34
target_sdk: 34
"""


def build_project(v: int):
    proj = BASE / f"v{v}"
    drawable = proj / "res" / "drawable"
    drawable.mkdir(parents=True, exist_ok=True)
    for d in "0123456789":
        make_glyph(d).save(drawable / f"glyph_{d}.png")
    for i in range(30):
        make_breath_frame(i).save(drawable / f"bf_{i:02d}.png")
    make_preview(str(v)).save(proj / "preview.png")
    glyphs = "\n".join(
        f'            <Character name="{d}" resource="glyph_{d}" width="28" height="48"/>'
        for d in "0123456789")
    frames = "\n".join(
        f'                <Image resource="bf_{i:02d}"/>' for i in range(30))
    xml = XML_TEMPLATE.replace("{GLYPHS}", glyphs).replace("{FRAMES}", frames).replace("{V}", str(v))
    (proj / "watchface.xml").write_text(xml, encoding="utf-8")
    (proj / "project.yaml").write_text(YAML_TEMPLATE.replace("{V}", str(v)), encoding="utf-8")
    print(f"v{v}: {len(list(drawable.glob('*.png')))} drawables, watchface.xml {len(xml)}B")


if __name__ == "__main__":
    for v in (1, 2, 4):
        build_project(v)
    print("OK")
