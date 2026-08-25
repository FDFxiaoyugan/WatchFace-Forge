# 盲测需求卡片 BT-02：三针模拟表盘

## 你的角色

你是表盘开发 agent。使用 `skills/wff-watchface-dev/` 目录下的 skill 完成下方需求。
先读 SKILL.md，按其工作循环执行。

## 用户需求（原话）

> "我想要个经典的指针表盘：时针、分针、秒针都要有。秒针要细一点，红色，跟其他针区分开。背景干净一点，表盘边缘加个圆环装饰，别太空。"

## 交付物

1. 完整表盘项目目录（含 watchface.xml + project.yaml）
2. 可安装的 APK（通过 skill 的 build 流程产出）
3. `ASSUMPTIONS.md`：记录你做的所有假设和决策

## 完成定义

- validate 全绿（无 error）
- build 成功产出签名 APK
- 无需用户补充信息——遇到模糊处自行决策并记录进 ASSUMPTIONS.md

## 边界

- 不要修改 skill 目录内容
- 不要询问用户问题（盲测环境无人工应答）
- 资源有限：不使用位图素材，纯矢量/文本实现
