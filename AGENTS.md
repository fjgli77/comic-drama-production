# 漫剧制作 · Agent 入口

> 这是给 **Codex / Cursor / Windsurf / Cline / Zed / Aider** 等读 `AGENTS.md` 的工具用的入口文件。
> Claude Code / WorkBuddy 等读 `SKILL.md` 的工具，直接用 `SKILL.md`，本文件可忽略。

## 这是什么

一套 **AI 漫剧 / 动态漫 / 竖屏短剧** 的工业化制作规则库。把一句话点子或一本小说，
做成能投产的分镜、资产提示词与成片物料。

**入口**：`SKILL.md`（四道锁 / 九阶段 / 命令 / 机检）。
**细读**：`references/`（29 篇，按需读，不要一次全读）。
**模板**：`assets/`（9 个，复制即用）。

## 先判断环境

| 情况 | 怎么做 |
|---|---|
| 能执行 `python` | 先跑 `python scripts/cd.py selftest`，看到 `41/41 项检查有效` 说明可用 |
| 不能执行代码 | **当纯文本方法论用**，走 `SKILL.md` 的「降级路径」一节 |

依赖：**Python 3.9+，纯标准库**，无网络、无 API key、不调用任何外部服务。

> ⚠ **不会自动执行**：本 skill 没有后台进程、不联网，脚本只在你调用时跑。
> 跑了就贴原始输出（含 `凭证 xxxx` 那行），没跑就直说"环境不支持命令"。
> **不许编造输出**——凭证由项目文件内容算出，用户复现一次就能识破。

## 最短上手

```
用户：帮我做一集漫剧，都市悬疑，60 秒

1. 读 SKILL.md 的「四道锁」，把形态/画幅/模型/平台问清（未确认不许动手）
2. python scripts/cd.py init ./新项目 建骨架（每集自动生成剧本/分镜/图片提示词三个文件）
3. 按 P1→P2→P3→P4→P5 走：故事 → 剧本 → 视觉设定 → 资产 → 分镜
4. python scripts/cd.py check ./新项目    FAIL 清零再往下
5. python scripts/cd.py pack ./新项目 --episode EP001 --model seedance-2.5
```

## 三条不能违反的约定

1. **Markdown 是唯一真相**。不建并行 JSON、不靠聊天记忆复述前情。
2. **锚点逐字复用**。角色脸、服装、锁面文字，跨镜跨集必须一字不差。
3. **机检 PASS ≠ 好看**。它只查确定性错误（结构、引用、算术、词根），审美判断在人工审查。

## 完整规则在哪

`SKILL.md` 是总纲；遇到具体问题按下表查：

| 问题 | 读 |
|---|---|
| 故事立不住、钩子不狠、人物是纸片人 | `references/01-story-engine.md` |
| 有原著要改编 | `references/02-novel-adaptation.md` |
| 台词写不好 | `references/03-script.md` 第三节（七维） |
| 人物提示词出图不像 | `references/26-figure-layouts.md` + `25-anime-character.md` |
| 特效写成发光雾 | `references/11-vfx-and-particles.md` |
| 打戏只有爆炸没有招式 | `references/12-action-and-fight.md` |
| 跨集人设崩 | `references/19-consistency-playbook.md` |
| 剪出来音画不同步 | `references/27-edit-and-delivery.md` |
| 被机检拦下不知道哪条 | `assets/机检项对照表.md` |

## 边界

不管真人实拍执行、不管纯插画出图、不管已成片的调色。管的是「点子或小说 → 可投产提示稿」这一段。
