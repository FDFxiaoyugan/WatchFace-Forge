# TOOLS.md - Local Notes

## Android SDK Build-Tools

- 安装路径: `/home/z/my-project/tools/android-sdk/`
- Build-Tools 版本: 34.0.0
- aapt2: x86_64 only，ARM64 不支持。Docker 构建时使用。
- apksigner: bash 脚本 + JAR，跨平台 (需 Java JRE)
- zipalign: x86_64 only，已用纯 Python 替代 (pyzipalign.py)
- cmdline-tools 路径: `android-sdk/cmdline-tools/latest/bin/`

## WFF APK 构建 (纯 Python 方案)

- 实验代码: `/home/z/my-project/experiments/wff-apk-test/` (原始), `/home/z/my-project/experiments/wff-demo/` (Demo)
- 模板 APK 预编译: Docker 构建时用 aapt2 生成二进制 AXML + resources.arsc
- 运行时: 手动构造 ZIP 字节流 (不用 zipfile.ZipFile) + apksigner
- 签名密钥: `test.keystore` (开发用, pass: wfftest123, alias: wfftest)
- 验证状态: ✅ 全管线通过 (打包→对齐→签名→验证)
- 真机安装: 已修复 3 个安装失败问题 (uses-sdk/STORED/对齐)，待最终确认

### 关键踩坑
- Manifest 必须含 `<uses-sdk minSdkVersion="30" targetSdkVersion="34"/>`，否则默认 SDK 0 被拒
- `resources.arsc` 必须 ZIP_STORED + 4字节对齐 (Android R+ 要求)，DEFLATED 会报 error -124
- 不要用 pyzipalign + apksigner 两步走：apksigner 重签名会丢失 pyzipalign 的 extra field
- 正确做法：手动构造 ZIP，在 local header 和 central directory 都写 extra field (0xD935)

## Web Search / Web Reader

- 使用 `z-ai function -n web_search` 和 `z-ai function -n page_reader`
- 输出 JSON 到文件，用 Python 解析
- 注意：page_reader 返回的 HTML 含大量模板代码，需正则提取正文

## 项目服务器

- ARM 服务器: 8u16g, 无公网, ARM64 (计算节点)
- 日本 VPS: 1u1g, 公网 x86 (备用入口)
- 阿里云: 2u2g 3Mbps, 公网 x86 (待购, 公网入口)
