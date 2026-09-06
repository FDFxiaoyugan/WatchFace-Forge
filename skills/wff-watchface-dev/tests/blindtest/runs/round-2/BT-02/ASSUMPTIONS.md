# ASSUMPTIONS.md — BT-02 经典指针表盘

## 任务
用户需求（原话）："我想要个经典的指针表盘：时针、分针、秒针都要有。秒针要细一点，红色，跟其他针区分开。背景干净一点，表盘边缘加个圆环装饰，别太空。"

## 设计决策

### 画布与全局
- **画布尺寸：450×450**（圆心 225,225）。依据：SKILL.md 画布尺寸说明中 450 对应 Pixel Watch 2 / Galaxy Watch 6+，且 analog-hands 配方使用 450。作为无目标机型的通用经典表盘，选 450 覆盖较新机型。
- **CLOCK_TYPE=ANALOG**，PREVIEW_TIME=10:08:32（经典表盘预览惯例，时针/分针/秒针均可见且不重叠）。
- **背景：`#ff0a0d12`**（近黑的深蓝黑，干净、低亮度，适合 AOD，且能让白色指针和银色圆环清晰衬托）。

### 表盘装饰（背景图 dial_bg.png）
- **"边缘圆环装饰"**：绘制两条同心圆环——
  - 外环：半径 214、线宽 5、银白色（#EBEBF2，alpha 235），距表盘边缘约 8px；
  - 内环：半径 204、线宽 1.5、暗银灰（#9696A5，alpha 95），作为外环的呼应层次。
- **"别太空"**：在圆环内加 60 个刻度（经典腕表刻度布局）——
  - 整点刻度 12 个：半径 186→206、线宽 6、亮白；
  - 分钟刻度 48 个：半径 196→206、线宽 2、暗银灰（alpha 160）。
- 背景图用 **Pillow 绘制**（透明底 RGBA，4× 超采样抗锯齿后缩放到 450×450），整体保持"干净"（纯线条、无多余元素），以 `<PartImage resource="dial_bg"/>` 引用。

### 指针（Pillow 生成三张白色剪影 PNG，XML 用 tintColor 染色）
- 指针无法用纯矢量（R25：三针必须图片资源），故用 Pillow 绘制"指向 12 点"的白色细长多边形/线条，透明底。
- **时针 hand_hour.png**：22×115，底端宽 22、尖端收敛为尖角；`tintColor #fff2f2f6`（近白）。
  - XML 放置：x=214 y=110 w=22 h=115，pivotX=0.5 pivotY=1.0 → 旋转中心 = (225,225) 圆心，针长 115。
- **分针 hand_minute.png**：16×165，比时针更长更细；`tintColor #ffededf2`。
  - XML 放置：x=217 y=60 w=16 h=165，pivot=(225,225)，针长 165。
- **秒针 hand_second.png**：8×235，**极细**（线宽 3），带尾部配重小圆（距 pivot 下方 32px、半径 6）与尖端小圆，`tintColor #ffff3b30`（**红色**，与白色时分针明显区分）。
  - 因秒针有尾部（配重悬在 pivot 下方 40px），pivotY=195/235≈**0.8298**（不在图片底端），旋转中心仍精确落在 (225,225)。
  - `<Sweep frequency="10"/>` 平滑扫秒；AMBIENT 模式 `<Variant target="alpha" value="0"/>` 隐藏秒针（省电 + AOD 规范）。

### 中心盖（XML 矢量）
- 白色盖帽 Ellipse 22×22（#ffededf2）+ 红色圆心 Ellipse 8×8（#ffff3b30），覆盖三针 pivot 交叠点，且红色圆心呼应红色秒针。

### AOD（AMBIENT）策略
- 背景图 alpha：255 → AMBIENT 40（大幅变暗省电）。
- 时针/分针 alpha：255 → AMBIENT 35（变暗但仍可读）。
- 秒针：AMBIENT 隐藏（alpha 0）。
- 中心盖：255 → AMBIENT 40。

### 素材生成方式
- 全部用 Pillow 生成，4–6× 超采样后 LANCZOS 缩放到目标尺寸以获得抗锯齿；手/针/圆环/刻度均为矢量绘制，无外部字体依赖（本表盘无文字）。
- preview.png：450×450 完整渲染 10:08:32 的静态预览图（背景 + 三针 + 中心盖），与运行时布局一致。

## 构建环境与打包
- 官方 XSD 校验（wff-validator.jar）需要 **Java 17**（class file 61.0），沙箱默认 Java 11 无法运行；已下载 Temurin JRE 17 并指向其 java 执行校验。
- 完整 aapt2 编译链路需要 `$ANDROID_HOME/build-tools/34.0.0/aapt2` **且** `$ANDROID_HOME/platforms/android-34/android.jar`；已下载 build-tools 34.0.0 与 android-34 平台并放入 workspace/tools/android-sdk。
- **重要踩坑（见 skill 知识层反馈）**：wff_builder.py 的 project.yaml 解析器只按行解析 `key: value`，**不支持列表**，`extra_drawables:` 列表会被静默忽略 → 指针/表盘 PNG 不会自动进包。解决办法：构建前把 `res/drawable/*.png` 预置进 `_build/res/drawable/`（builder 不会清空该目录），再由 aapt2 compile/link 打进 APK。项目内附 `prebuild_assets.sh` 复现该步骤。
- 最终 APK：`analogclassic-watchface.apk`，含 AndroidManifest.xml、res/drawable/{dial_bg,hand_hour,hand_minute,hand_second,preview}.png、res/raw/watchface.xml、res/xml/watch_face_info.xml、resources.arsc（STORED+4 字节对齐），v1+v2+v3 签名验证 PASS。

## 关于 recipes.md analog-hands 配方坐标的说明（假设）
- 配方示例的时针 x=215 y=100 h=200 / 分针 x=218 y=60 h=240 若按 pivotY=1.0 计算，旋转中心落在 y=300/300，**不在圆心 225**；秒针 x=221 y=40 h=280 中心在 y=320。skill 未明确说明手部坐标与圆心的换算关系。
- 我采用**几何上自洽**的做法：把每根针的 pivot（旋转中心）精确放在圆心 (225,225)（即 x=225−w/2、y=225−h 或按 pivotY 反推），保证三针同轴、绕表盘中心旋转。这是本表盘的关键假设之一。

---

## validate 修复轮数

- **16 规则初筛**（`python wff-builder/wff_builder.py validate`）：第 1 次执行即 **20/20 PASS**，0 error 0 warning，无需修复。
- **官方 XSD 校验**（`java -jar vendor/google-watchface/tools/wff-validator.jar 5 watchface.xml`）：第 1 次提交即 **PASSED**（valid against watch face format version #5）。
  - 说明：官方校验器首次因沙箱 **Java 11 太旧（需 Java 17）** 无法启动，属于环境问题而非 XML 问题；安装 JRE 17 后首次校验即通过。
- **总计 validate 执行轮数：1 轮（两级均一次通过，XML 零修复）。**
- （构建阶段另做过 3 次 build 迭代，均非 validate 问题：①无 apksigner ②无 android.jar 导致 aapt2 回退、drawables 缺失 ③补齐环境后成功——详见上文"构建环境与打包"。）

---

## skill 知识层反馈

### 实际用到的 skill 文件
1. `SKILL.md` —— 工作流（理解需求→选配方→写 XML→两级验证→构建）、project.yaml 规范、画布尺寸、构建约束与 keystore 信息。
2. `references/pitfalls.md` —— R01/R02/R03/R04/R08/R10/R17/R19/R21/R22/R23/R24/R25（三针图片资源、tintColor）、R26-R30、构建约束 BC1-BC6。
3. `references/recipes.md` —— 配方 2（analog-hands）结构、Hand 的 pivot 语义、Sweep 用法、AMBIENT 变体模式。
4. `references/elements.md` —— PartDraw/Arc/Ellipse/Stroke/Fill 嵌套方向、AnalogClock 与三针属性、Variant 用法。
5. `references/expressions.md` —— （本表盘未用到动态表达式，仅参考数据源说明）。
6. `examples/minimal-digital/` —— 确认 450 画布 + AMBIENT 双模式写法的真机验证先例。

### 想找但 skill 里没有 / 找不到的信息
1. **"怎么把指针/表盘 PNG 真正打进 APK"**：skill 说 `resource` 指向 res/drawable 图片、project.yaml 有 `extra_drawables`，但没说明 (a) wff_builder 的 project.yaml 解析器只支持单值 `key: value`，**列表项会被静默忽略**；(b) 无 aapt2+android.jar 时走"预编译 ARM 模板"回退，**只打包 preview.png，额外 drawables 全部丢失**。这导致我花费最多时间排查，最后只能靠"构建前预置 `_build/res/drawable/`"绕过。**建议**：在 SKILL.md/pitfalls 中写明 extra_drawables 的限制与替代方案（或让 builder 支持列表解析）。
2. **aapt2 可用的前置条件**：skill 只写了"aapt2 仅 x86_64"，未提及还需要 `$ANDROID_HOME/platforms/android-34/android.jar`（aapt2 link 的 `-I` 参数）与 Build-Tools 34.0.0 并存，否则 builder 静默回退 ARM 模板。建议补充完整环境清单与"回退模式会丢资源"的警告。
3. **wff-validator.jar 的 Java 版本要求**：skill 未注明官方校验器需要 Java 17+（class file 61.0），沙箱默认 Java 11 会直接 LinkageError。建议在 SKILL.md 环境小节写明 `java -version ≥ 17`。
4. **preview.png 尺寸歧义**：init 输出提示"add a 384x384 preview image"，而画布配方是 450×450。两处口径不一致；我按 450×450 生成并验证可用，但建议统一。
5. **带尾部（配重）秒针的 pivot 计算**：skill 只给了"竖直针 pivotY=1.0 在底端"的简单情形，未给出 pivot 不在图片边缘（如秒针尾部悬在 pivot 下方）时的 pivotY 推算方法与示例坐标。建议补一个带配重秒针的完整示例。
6. **Hand 坐标与圆心的换算约定**：recipes.md analog-hands 配方的手部坐标按 pivotY=1.0 反推旋转中心在 y=300（非圆心 225），skill 未解释这是近似还是其他约定。我选择"pivot 精确落圆心"的自洽方案，建议在文档中明确规范。

---

## 修复记录（2026-09-06）：秒针错位修复

### 问题
用户反馈实际设备截屏中秒针略有错位。经像素级分析，根因是三张指针 PNG 的**左右抗锯齿不对称**：

- 原 hand_second.png 主体线每行 alpha 为 `[0,0,86,255,255,170,0,4]`，左边缘 alpha=86、右边缘 alpha=170，alpha 质心 x=4.163（图片几何中心为 4.0），偏移 **+0.163px**。
- 时针、分针在尖端细处有类似的 +0.5px bbox 偏移（主体粗处对称）。
- 原因：原始素材用 Pillow `ImageDraw` 在偶数宽度画布上绘制，`rectangle`/`polygon` 的右边界为 inclusive，导致线右侧多占 1 个超采样像素，LANCZOS 缩放下进一步放大不对称。
- 后果：`pivotX=0.5` 绕图片几何中心 x=4.0 旋转，但指针视觉轴线在 x≈4.16，秒针旋转后不经过表盘圆心 (225,225)，在细秒针上肉眼可见错位。

### 修复方案
改用 **numpy 精确光栅化 + 16× 超采样 + BOX（平均池化）降采样** 重新生成三张指针：

- 所有绘制使用半开区间 `[x0, x1)`，边界数学精确；
- 多边形用扫描线算法按像素中心求交，不依赖 PIL 绘制边界行为；
- 降采样用 reshape+mean（BOX filter），对偶数宽度天然左右对称。

修复后验证（APK 内实际资源）：

| 图片 | 尺寸 | alpha 质心 x | 几何中心 | 偏移 | 最大左右 alpha 差 |
|---|---|---|---|---|---|
| hand_second.png | 8×235 | 4.0000 | 4.0 | +0.0000 | 0 |
| hand_hour.png | 22×115 | 11.0000 | 11.0 | +0.0000 | 0 |
| hand_minute.png | 16×165 | 8.0000 | 8.0 | +0.0000 | 0 |

秒针主体线每行 alpha 现为 `[0,0,127,255,255,127,0,0]`，左右边缘均为 127，完全对称。

### 重新构建
- preview.png 用新指针重新渲染（10:08:32）；
- `prebuild_assets.sh` 预置素材 → `wff_builder.py build` 重新打包；
- 16 规则初筛 20/20 PASS，官方 XSD 校验通过（XML 未改动）；
- APK 签名 v1+v2+v3 验证 PASS。

### 经验补充（skill 反馈）
7. **指针素材必须保证左右 alpha 对称**：在偶数宽度画布上用 PIL `ImageDraw` 绘制细线时，inclusive 边界会导致左右抗锯齿不对称，肉眼可见为指针错位。建议 skill 的 recipes/pitfalls 中提醒：指针素材应用精确光栅化或奇数宽度画布，并在交付前做 alpha 质心校验（`centroid_x == width/2`）。
