"""
WFF Compiler — CDM → WFF XML 转换器

将 CDM JSON 模型编译为 WFF (Watch Face Format) XML，
然后通过 wff-builder 构建为 APK。

编译管线:
  CDM JSON → WatchFaceCDM (Pydantic) → WFF XML (string) → wff-builder → APK

用法:
  from compiler.wff.compiler import WFFCompiler
  compiler = WFFCompiler()
  wff_xml = compiler.compile(cdm_dict)
  apk_path = compiler.build_apk(cdm_dict, output_dir)
"""

from __future__ import annotations

import json
import shutil
import tempfile
import os
from pathlib import Path
from typing import Optional

from schema.cdm.models import (
    WatchFaceCDM,
    ClockType,
    DigitalTime,
    AnalogTime,
    DateDisplay,
    InfoLine,
    Background,
    FontStyle,
    FontWeight,
    HorizontalAlign,
    DataSource,
)

# WFF Builder 引擎路径
WFF_BUILDER_PATH = Path(__file__).parent.parent.parent / "wff-builder" / "wff_builder.py"
WFF_BUILDER_DIR = Path(__file__).parent.parent.parent / "wff-builder"


class WFFCompiler:
    """CDM → WFF XML 编译器"""

    CANVAS_SIZE = 450

    def compile(self, cdm: WatchFaceCDM | dict) -> str:
        """将 CDM 模型编译为 WFF XML 字符串

        Args:
            cdm: WatchFaceCDM 对象或 dict

        Returns:
            WFF XML 字符串
        """
        if isinstance(cdm, dict):
            cdm = WatchFaceCDM.model_validate(cdm)

        lines = []
        lines.append('<?xml version="1.0"?>')
        lines.append(f'<WatchFace width="{self.CANVAS_SIZE}" height="{self.CANVAS_SIZE}">')

        # Metadata
        lines.append(f'  <Metadata key="CLOCK_TYPE" value="{cdm.clock_type.value}"/>')
        lines.append(f'  <Metadata key="PREVIEW_TIME" value="{cdm.metadata.preview_time}"/>')

        # Scene
        bg_color = cdm.background.color
        lines.append(f'  <Scene backgroundColor="{bg_color}">')

        # Background
        self._emit_background(lines, cdm.background)

        # Time display
        if cdm.clock_type == ClockType.DIGITAL and cdm.digital_time.enabled:
            self._emit_digital_clock(lines, cdm.digital_time)
        elif cdm.clock_type == ClockType.ANALOG and cdm.analog_time.enabled:
            self._emit_analog_clock(lines, cdm.analog_time)

        # Date
        if cdm.date_display.enabled:
            self._emit_date(lines, cdm.date_display)

        # Info line (battery/heart rate)
        if cdm.info_line.enabled:
            self._emit_info_line(lines, cdm.info_line)

        lines.append('  </Scene>')
        lines.append('</WatchFace>')

        return '\n'.join(lines) + '\n'

    # ─── 片段生成 ──────────────────────────────────────

    def _emit_background(self, lines: list, bg: Background):
        """生成背景层"""
        if bg.type == "solid":
            # backgroundColor 已在 Scene 上声明, 这里不需要额外元素
            pass
        elif bg.type == "image" and bg.image_resource:
            lines.append(f'    <PartImage x="0" y="0" width="{self.CANVAS_SIZE}" height="{self.CANVAS_SIZE}"'
                         f' resource="drawable/{bg.image_resource}"/>')

    def _emit_digital_clock(self, lines: list, dt: DigitalTime):
        """生成数字时钟"""
        pos = dt.position
        font = dt.font
        align = dt.align.value

        lines.append(f'    <DigitalClock x="0" y="0" width="{self.CANVAS_SIZE}" height="{self.CANVAS_SIZE}">')

        # Active mode (bright)
        lines.append(f'      <TimeText format="{dt.format}" hourFormat="SYNC_TO_DEVICE"'
                     f' align="{align}" x="{pos.x}" y="{pos.y}" width="{pos.width}" height="{pos.height}" alpha="255">')
        lines.append(f'        <Variant mode="AMBIENT" target="alpha" value="0"/>')
        lines.append(self._format_font_tag(font, indent=8))
        lines.append('      </TimeText>')

        # Ambient mode (dim)
        ambient_font = FontStyle(
            family=font.family, size=font.size, weight=FontWeight.THIN, color=dt.ambient_color
        )
        lines.append(f'      <TimeText format="{dt.format}" hourFormat="SYNC_TO_DEVICE"'
                     f' align="{align}" x="{pos.x}" y="{pos.y}" width="{pos.width}" height="{pos.height}" alpha="0">')
        lines.append(f'        <Variant mode="AMBIENT" target="alpha" value="255"/>')
        lines.append(self._format_font_tag(ambient_font, indent=8))
        lines.append('      </TimeText>')

        lines.append('    </DigitalClock>')

    def _emit_analog_clock(self, lines: list, at: AnalogTime):
        """生成模拟时钟 (指针表盘)"""
        # 使用 PartDraw 绘制指针
        # 时针
        lines.append(f'    <PartDraw x="0" y="0" width="{self.CANVAS_SIZE}" height="{self.CANVAS_SIZE}">')
        lines.append(f'      <Variant mode="AMBIENT" target="alpha" value="0"/>')
        lines.append(f'      <DrawList>')
        lines.append(f'        <DrawOval x="{at.center_x - 4}" y="{at.center_y - 4}" width="8" height="8" color="{at.hour_hand_color}"/>')
        lines.append(f'        <DrawOval x="{at.center_x - 4}" y="{at.center_y - 4}" width="8" height="8" color="{at.hour_hand_color}"/>')
        lines.append(f'      </DrawList>')
        lines.append('    </PartDraw>')
        # 注意: 完整的指针表盘需要更复杂的绘制逻辑
        # 这里先输出基本结构, 后续迭代完善

    def _emit_date(self, lines: list, dd: DateDisplay):
        """生成日期显示"""
        pos = dd.position
        font = dd.font
        align = dd.align.value

        # 构建 Template
        params = '\n'.join(f'                        <Parameter expression="{p.wff_expression}"/>'
                           for p in dd.params)

        lines.append(f'    <PartText x="{pos.x}" y="{pos.y}" width="{pos.width}" height="{pos.height}">')
        lines.append(f'      <Variant mode="AMBIENT" target="alpha" value="0"/>')
        lines.append(f'      <Text align="{align}">')
        lines.append(self._format_font_tag(font, indent=8))
        lines.append(f'        <Template>{dd.format}')
        if params:
            lines.append(params)
        lines.append('        </Template>')
        lines.append('      </Text>')
        lines.append('    </PartText>')

    def _emit_info_line(self, lines: list, info: InfoLine):
        """生成信息行 (电量/心率)"""
        pos = info.position
        font = info.font
        align = info.align.value

        template = f'{info.label} %s{info.suffix}'

        lines.append(f'    <PartText x="{pos.x}" y="{pos.y}" width="{pos.width}" height="{pos.height}">')
        lines.append(f'      <Variant mode="AMBIENT" target="alpha" value="0"/>')
        lines.append(f'      <Text align="{align}">')
        lines.append(self._format_font_tag(font, indent=8))
        lines.append(f'        <Template>{template}')
        lines.append(f'                        <Parameter expression="{info.data_source.wff_expression}"/>')
        lines.append('        </Template>')
        lines.append('      </Text>')
        lines.append('    </PartText>')

    # ─── 工具 ──────────────────────────────────────────

    def _format_font_tag(self, font: FontStyle, indent: int = 6) -> str:
        """生成 Font 标签"""
        pad = ' ' * indent
        return (f'{pad}<Font family="{font.family}" size="{font.size}"'
                f' weight="{font.weight.value}" slant="NORMAL" color="{font.color}"/>')

    # ─── APK 构建 ──────────────────────────────────────

    def build_apk(self, cdm: WatchFaceCDM | dict, output_dir: Optional[str] = None,
                  preview_path: Optional[str] = None) -> Path:
        """编译 CDM → WFF XML → 构建 APK

        Args:
            cdm: CDM 模型或 dict
            output_dir: 输出目录 (默认临时目录)
            preview_path: 预览图路径 (默认自动生成)

        Returns:
            APK 文件路径
        """
        if isinstance(cdm, dict):
            cdm = WatchFaceCDM.model_validate(cdm)

        # 1. 编译 WFF XML
        wff_xml = self.compile(cdm)

        # 2. 准备项目目录
        if output_dir:
            proj_dir = Path(output_dir)
        else:
            proj_dir = Path(tempfile.mkdtemp(prefix="wff_build_"))

        proj_dir.mkdir(parents=True, exist_ok=True)

        # 3. 写入项目文件
        self._write_project_yaml(proj_dir, cdm)
        (proj_dir / "watchface.xml").write_text(wff_xml, encoding='utf-8')

        # 4. 预览图
        if preview_path:
            shutil.copy(preview_path, proj_dir / "preview.png")
        else:
            # 自动生成预览图
            self._generate_preview(proj_dir / "preview.png", cdm)

        # 5. 调用 wff-builder
        return self._invoke_builder(proj_dir)

    def _write_project_yaml(self, proj_dir: Path, cdm: WatchFaceCDM):
        """写入 project.yaml"""
        content = f"""package_name: {cdm.metadata.package_name}
version_code: {cdm.metadata.version_code}
version_name: "{cdm.metadata.version_name}"
watch_face_name: {cdm.metadata.name}
wff_version: 1
"""
        (proj_dir / "project.yaml").write_text(content)

    def _generate_preview(self, path: Path, cdm: WatchFaceCDM):
        """生成简单的预览图"""
        from PIL import Image, ImageDraw, ImageFont
        size = 384
        img = Image.new("RGBA", (size, size), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        cx, cy = size // 2, size // 2

        # 渐变背景
        bg = cdm.background
        if bg.color:
            r = int(bg.color[2:4], 16)
            g = int(bg.color[4:6], 16)
            b = int(bg.color[6:8], 16)
        else:
            r, g, b = 0, 0, 0

        for radius in range(size // 2, 0, -1):
            t = radius / (size // 2)
            cr = int(r * t)
            cg = int(g * t)
            cb = int(b * t)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                        fill=(cr, cg, cb, 255))

        # 时间文字
        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.otf", 72
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.otf", 28
            )
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        time_text = "10:08"
        bbox = draw.textbbox((0, 0), time_text, font=font_large)
        tw = bbox[2] - bbox[0]
        draw.text(((size - tw) // 2, cy - 60), time_text,
                 fill=(0, 245, 255, 255), font=font_large)

        date_text = "08/15"
        bbox2 = draw.textbbox((0, 0), date_text, font=font_small)
        dw = bbox2[2] - bbox2[0]
        draw.text(((size - dw) // 2, cy + 30), date_text,
                 fill=(170, 170, 170, 255), font=font_small)

        img.save(path, "PNG", optimize=True)

    def _invoke_builder(self, proj_dir: Path) -> Path:
        """调用 wff_builder.py build"""
        import subprocess

        env = os.environ.copy()
        env["ANDROID_HOME"] = env.get("ANDROID_HOME",
                                      "/home/z/my-project/tools/android-sdk")

        result = subprocess.run(
            ["python3", str(WFF_BUILDER_PATH), "build", str(proj_dir)],
            capture_output=True, text=True, env=env, cwd=str(WFF_BUILDER_DIR)
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"wff-builder failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        # 查找生成的 APK
        apk_name = f"{proj_dir.name}-watchface.apk"
        apk_path = proj_dir / apk_name
        if not apk_path.exists():
            # 搜索 APK 文件
            apks = list(proj_dir.glob("*.apk"))
            if apks:
                apk_path = apks[0]
            else:
                raise FileNotFoundError(f"APK not found in {proj_dir}")

        return apk_path


if __name__ == "__main__":
    # 测试: 编译 demo CDM
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from schema.cdm.models import (
        WatchFaceCDM, WatchFaceMetadata, DigitalTime, FontStyle,
        FontWeight, Position, DateDisplay, InfoLine, DataSource
    )

    cdm = WatchFaceCDM(
        metadata=WatchFaceMetadata(
            name="Test Digital",
            package_name="com.watchface.test",
            version_code=1,
        ),
        clock_type=ClockType.DIGITAL,
        digital_time=DigitalTime(
            format="HH:mm",
            position=Position(x=0, y=120, width=450, height=120),
            font=FontStyle(size=100, weight=FontWeight.BOLD, color="#ff00F5FF"),
        ),
        date_display=DateDisplay(
            format="%s/%s",
            params=[DataSource.MONTH, DataSource.DAY],
        ),
        info_line=InfoLine(
            label="BAT",
            data_source=DataSource.BATTERY_PERCENT,
        ),
    )

    compiler = WFFCompiler()
    xml = compiler.compile(cdm)
    print(xml)
