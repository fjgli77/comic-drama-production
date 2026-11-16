# 生态地图：GitHub 上的 AI 漫剧 Skill

> 采集日期 2026-11-15。数据来源：两个元清单（`UnderleveledBuilder/awesome-short-drama-skills` ★2332，其数据抓取于 2026-11-13；`jicky/awesome-short-drama-skills`）合并去重 102 条，再用 13 组 GitHub 搜索补漏，人工清洗噪声与误判后共 **192 个仓库**。
>
> 局限：星数为采集时数值，会变；大档分类由仓库描述关键词自动判定，边界条目可能出错；**我没有逐个跑过这些 skill**，只读了元数据与其中十余个的正文。这份地图回答「谁在做、做什么方向」，不回答「谁做得好」。

---

## 一、总量与分布

| 能力域 | 数量 | 判断 |
|---|---:|---|
| 全流程（剧本→分镜→提示词） | 54 | 最拥挤，同质化最严重 |
| 分镜 / 镜头设计 | 41 | 数量多，但多数停在「分镜脚本」 |
| 角色 / 资产 / 一致性 | 29 | 第二密集 |
| 视频提示词（Seedance / H3 / 可灵） | 23 | 时效性最强，跟着模型换代 |
| 编剧 / 改编 | 19 | 拼方法论，不拼工具 |
| 元清单（收录别人） | 10 | 看全景最省力 |
| 平台 / 应用（可部署） | 5 | 不是 skill，是完整产品 |
| 打戏 / 动作 | 4 | **稀缺**，且全是单人作品 |
| 写作方法论 / 去 AI 味 | 3 | 少但通用 |
| 服装 / 造型 | 2 | **极度稀缺** |
| 场景 / 美术 | 1 | **几乎空白** |
| 特效 / 粒子 | **0** | **全生态没有专门 skill** |
| 武器 / 道具 | **0** | **完全没有** |
| 表情 / 动作板 | **0** | **完全没有** |

一句话概括：**上半身挤爆，下半身空着。**

---

## 一·补、分阶段分布与第三方实测

上面的分类是「做什么形态」，元清单另有一套「按创作阶段」的统计（86 个 skill，2026-11-13）。
两套一起看，才知道**哪一段真的没人做**。

| 阶段 | 数量 | 判断 |
|---|---:|---|
| 视频 / 图像提示词 | 57 | 最挤，且随模型换代快速过期 |
| 分镜 / 镜头设计 | 48 | 挤，但多数停在「分镜脚本」不出图 |
| 剧本 / 对白 | 43 | 挤，拼方法论 |
| 人物 / 角色资产 | 29 | 中 |
| 审稿 / 质检 / 去 AI 味 | 29 | 中，去 AI 味刚起来 |
| 结构 / 集纲 / 钩子 | 26 | 中 |
| 改编（小说→剧本） | 22 | 中 |
| **出片 / 配音 / 剪辑** | **17** | **最空的一段** |
| 选题 / IP 评估 | 6 | 绝对数最少 |

**结论**：生态呈纺锤形——中间（分镜、提示词）极挤，两头（选题、出片）都空。
所有人都想做"生成",很少有人做"生成完之后怎么办"。

### 第三方双盲实测（仅供参考，不是排行榜）

元清单作者做过三轮评审（Opus 与 GPT 双盲）：

| 轮次 | 结论 |
|---|---|
| 写剧本 | 全胜：`zenstory-ai/drama-skills`、`shanyin-screenwriting-master`、`screenwriting-skills`、`emma-screenwriting-skills` |
| 定选题 | 前三：`Chinese-WebNovel-Skill`、`webnovel-writer`、`ai-short-drama`（Hao0321） |
| 60 集骨架 | 前四：`hongguo-shortdrama-screenwriting`、`emma-screenwriting-skills`、`Chinese-WebNovel-Skill`、`short-drama-factory` |

**怎么用**：如果你手上是「小说→分集→剧本」这前半段，上面几个的编剧方法论比本 skill 厚，
可以互补；本 skill 的强项在后半段（资产 → 分镜 → 提示词 → 机检 → 字幕）。

**局限**：只评产出文本、不测出图；样本量小；不是绝对排名。别把"全胜"当结论，当线索。

---

## 二、六个观察

### 1. 全流程占近三成，但内容高度雷同

54 个「全流程」里，主线几乎都是同一条：

```
句子 → 剧本 → 分镜 → 关键帧提示词 → 视频提示词 → 成片
```

差别只在于：接到哪个视频模型（Seedance 2.0/2.5、MiniMax H3、可灵、Veo）、有没有机检、文档用 Markdown 还是 JSON、有没有接 ComfyUI。

**真正的差异不在流程，在流程之外**——谁定义了失败模式、谁有一致性机制、谁把「资产怎么造」讲清楚了。

### 2. 星数与质量不成正比

星数榜前列里，有相当一部分是**元清单**（收录别人的清单），不是 skill 本身。`blader/humanizer`（★6.9 万）是通用去 AI 味工具，与漫剧只有间接关系；`Dujltqzv/Some-Many-Books`（★2.6 万）是书籍收藏列表。

挑 skill 时，星数只能当「有没有人用过」的粗筛，不能当质量指标。

### 3. 下半身是真的空

这是这份地图最有价值的发现。192 个仓库里：

| 方向 | 数量 | 谁在做 |
|---|---:|---|
| 服装设定板 | 2 | `XiaoLuo` 的服装拆解、`lmy414/ai-chan-sheets` 的立绘补全 |
| 场景资产 | 1 | `zhouwei713` 的中式宏大场景 |
| 打戏 | 4 | 全部是单人作品，且都偏「写提示词」 |
| 武器 | 0 | — |
| 道具 | 0 | — |
| 表情 / 动作板 | 0 | — |
| 特效 / 粒子 | 0 | — |

原因不难猜：**这几样不产生「新流程」，只产生「更细的约束」**。做全流程容易显得完整，做服装板要面对「模型画不出扣子」这种脏活。

但这正是成片质量的差距所在——观众记不住你的分镜表，记得住那个人的袖子在第 8 集变了。

### 4. 格式已经事实统一

约八成仓库是 `SKILL.md` + `references/*.md` 的 Agent Skill 结构，能直接装进 Claude Code / Codex / WorkBuddy。少数是 prompt 集或完整应用。

**这意味着内容可以互相搬。** 差异不在文件格式，在每篇文档里的判断密度。

### 5. 视频提示词这一档半衰期最短

23 个里有 20 个绑定具体模型。模型一换代，提示词语法就废一半。

反过来，`01-story-engine`、`04-visual-bible`、`19-consistency` 这类**不依赖模型的文档**，才是长期资产。

写 skill 时的取舍：**依赖模型的部分尽量薄、尽量晚写；不依赖模型的部分尽量厚。**

### 6. 「一致性」被反复声称，很少被真正实现

过半仓库在描述里写「角色一致性」。实际做法多数是：把同一段人物描述复制到每个提示词里。

这是最弱的一种做法——它只保证「文字一样」，不保证「图一样」。真正管用的三层是：

```
锚点逐字复用（文字层） → 参考图槽位（图像层） → 连续性锁（跨镜校验层）
```

三层都做的，我看到的不到五个。

---

## 三、这个 skill 的位置判断

对照 `references/` 现有 21 篇：

| 我的文档 | 生态里同类 | 判断 |
|---|---:|---|
| `06-costume-assets` 服装板 | 2 | **差异化优势**，可继续加厚 |
| `07-expression-and-pose` 表情动作板 | 0 | **独家** |
| `08-scene-assets` 场景九宫格 | 1 | **独家**（机位矩阵别处没有） |
| `10-weapon-assets` 武器板 | 0 | **独家** |
| `11-vfx-and-particles` 特效粒子 | 0 | **独家**，「去水五律」别处没有 |
| `12-action-and-fight` 打戏 | 4 | 持平偏好，轨迹图工作流独有 |
| `19-consistency-playbook` 一致性 | 声称很多，做全的少 | 优势，三层齐全 |
| `01-story-engine` / `03-script` 剧本 | 19 | 红海，不占优 |
| `13`–`15` 分镜 / 关键帧 / 视频提示词 | 41 + 23 | 红海，且时效性强 |
| `27-edit-and-delivery` 剪辑与交付 | **17** | **差异化**，生态最空的一段 |
| `25-anime-character` 二次元词法 | 散落在提示词类里 | 有优势：没人把「动漫脸 vs 写实脸」讲清 |
| `26-figure-layouts` 图式矩阵 | 无 | **独家**，别人只有一个版式 |
| `srt` 字幕骨架生成 | 有工具无方法论 | 优势：直接把「镜长→字幕」打通 |

**结论：不要在全流程上跟人比完整，在「资产怎么造」上比细。**

3.6 之后，这个判断要加一句：**下半身（出片/剪辑）比上半身（编剧）更值得投入**。
生态里 43 个人在写剧本，17 个人在做剪辑，而观众的差评永远来自后半段——
音画不同步、字幕截断、响度忽大忽小。

54 个人在做「一句话到成片」，只有 0 个人在做「这件衣服的扣子在第 8 集不该变」。

---

## 四、值得精读的十个

按「读完能改自己 skill」的标准挑，不按星数。

| 仓库 | 为什么值得读 |
|---|---|
| `zenstory-ai/drama-skills` | 规则四级、Markdown 单一真相、REF/PLAN 四态。架构上最成熟 |
| `lixiaoxiao9888-create/manju-laoli-skill` | 规则来自真实生成的废片，不是推演。禁令失效三改法、道具光效零描写 |
| `ZzzAloong/fight-scene-director` | 轨迹图工作流：先出站位图/轨迹图，再按图写提示词 |
| `zhurui0523/XiaoLuo-AI-Drama-Skill` | 服装板「拆解不设计」、十二表情、十五动作 |
| `lmy414/ai-chan-sheets` | 立绘 → 三视图/表情/服装的**自动补全**，工程化程度高 |
| `eternityspring/shuohao-skills` | 拆角色 → 改编大纲 → 场景道具美术设定 → 剧本 → 分镜，分工最清晰 |
| `LearnPrompt/awesome-seedance` | 800+ 条提示词案例，近 500 次跨模型复测。做提示词时的实测库 |
| `alchaincyf/seedance-skill` | 白模驱动：用 `scene.json` 渲染白模参考视频做几何体检，思路独特 |
| `nigo-studio/ai-film-skills` | 从实际动作片《CROW LINE》流程拆出，不是纸上推演 |
| `mengxiujie/ManjuForge` | 7 个记忆文件 + 22 项一致性检查，连载视角 |

---

## 五、全量清单（192）

星数为采集时数值，`0` 表示新仓库或未采集到。

### 全流程（54）

从一句话或一本小说一路跑到分镜、提示词甚至成片。竞争最激烈的一档。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 1 | `zenstory-ai/drama-skills` | 4210 | 短剧/漫剧全链路：拆小说、开发、剧本、角色资产、分镜、图/视频提示词、审查 |
| 2 | `liangdabiao/Seedance2-Storyboard-Generator` | 2854 | 把小说或故事改成多集视频剧本和分镜，产出 Seedance 2.0 提示词 |
| 3 | `lixiaoxiao9888-create/manju-laoli-skill` | 2090 | 漫剧老李：AIGC 漫剧导演全流程，门控剧本、资产锁定、分镜、投喂提示词、规则化质检 |
| 4 | `LingGuoAI/LingGuo-Drama` | 1667 | 灵果短剧：一站式 AI 短剧/漫剧平台，剧本生成、角色场景道具提取与出图、分镜和帧提示词、视频生成，FFmpeg 合成成片 |
| 5 | `zhanghao123vip/ai-manju-skills` | 816 | 21 个题材的 AI 漫剧全流程 Skill：一句点子生成企划案、资产图提示词、分集剧本、分镜与视频提示词。可用于 Claude Code、 |
| 6 | `liangdabiao/smy-seedance-storyboard` | 245 | 故事 → 上美影复古手绘风格的短剧制作文档：剧本、分镜、资产生图提示词，附完整示例项目 |
| 7 | `suihe1/short-drama-production` | 200 | 短剧生产总控：小说大纲/人物/剧本、导演分镜、提示词、声音资产、粗剪与 QC（默认 16:9） |
| 8 | `wyuzhi/qisi-video-remix` | 194 | 视频创意改编：参考视频 → 剧本 → 分镜 → 分段生成提示词 |
| 9 | `62656456/ai-film-skills` | 132 | 21 个独立模块：短剧制作、分镜导演、角色资产、国风/科幻等视觉风格导演，附 3D 预演 |
| 10 | `LuoJiangYong/muse-video-skill` | 85 | 虚拟剧组：导演/编剧/摄影/美术/特效/声音六角色协作，创意 → 剧本、分镜、美术、提示词，38 个案例技法库 |
| 11 | `senmanx/novel-to-manju` | 78 | 小说转漫剧全流程：爆款改文 → 剧本 → 人物/场景三视图 → 分镜 → 视频提示词 |
| 12 | `AharaOoO/acheng-director-skill` | 67 | Acheng 导演引擎：剧本、分镜、文戏五轨表演、打戏因果链、特效与资产，编译成 MiniMax H3 / Seedance 提示词 |
| 13 | `BaYue-SYJ/shuixian-manju-skills` | 46 | 水仙的漫剧6件套，灵感来源于shuohao-skills |
| 14 | `jxshow/jingju-skills` | 45 | 鲸剧：AI 漫剧全流程，大纲、人设一致性、分集剧本、分镜、图/视频提示词、ComfyUI 批量出图 |
| 15 | `UncleWang2088/short-drama-director` | 35 | 短剧导演专家包：剧本创作、平台标准审稿、镜头级分镜与表演指导，输出 Seedance 提示词 |
| 16 | `lixiaoxiao9888-create/manju-laoli-skill-legacy` | 33 | 漫剧老李 Skill 旧版归档：V5.0.2（AI漫剧全流程整合包）+ 空间导演转换器 V3。仅供回溯参考，新用户请使用主仓库 manju- |
| 17 | `mengxiujie/ManjuForge` | 32 | 漫剧/短剧连载引擎：一句话 → 剧本、分镜、配音、提示词，7 个记忆文件 + 22 项一致性检查防人设崩坏 |
| 18 | `cyuanxv/ai-mandrama-skills` | 30 | AI 漫剧/短剧端到端制作 Claude Code Skills 包(Dreamina + edge-tts + ffmpeg) |
| 19 | `Arch-Dog/video-prompt-engineer` | 25 | 面向 Seedance 的 AI 短剧分镜 Agent Skill：把已审核剧本与资产转换为可执行的视频提示词表。 |
| 20 | `niuhuoshan/generate-comic-drama-video` | 22 | ai漫剧生成、漫画剧生成、全流程自动生成skills |
| 21 | `Coconah/AI-Short-Drama-Agent-Skill` | 21 | 短剧编剧 AI Agent SOP |
| 22 | `djyy1031/ai-comic-drama-director-skills` | 21 | AI 漫剧导演：剧本 + 已有资产 → Seedance 2.0/2.5 分镜组提示词，含人物表演、导演摄影、场景资产、站位图、连续性与声音 |
| 23 | `shyman159/seedance-prompts-skill` | 21 | 专业的 Seedance 2.0 AI 视频脚本与分镜提示词生成 Claude Skill：把文章/故事转为标准剧本、资产提示词与分镜，含 |
| 24 | `liuxiao20051106-prog/ai-manga-drama` | 18 | AI 漫剧工坊：一句创意到成片的八步流程，任务卡剧本、角色参考图库、风格锚、分镜、图/视频提示词、配音字幕与合成终检 |
| 25 | `SyberSister/short-drama-adapter-skill` | 16 | （描述为空，待核） |
| 26 | `way928745-collab/Hermes_Script_Cool` | 12 | 一站式短剧全链路 AI 创作 Skill。工作流：素材蒸馏 → 剧本创作 → 分镜脚本 → 剧本元素拆解 → 人物音色配置 → 视频提示词生 |
| 27 | `sanxsnr/ai-short-drama-from-zero` | 10 | AI短剧从0到1｜零基础完成你的第一部剧面向零基础新人的AI短剧制作Skill：从灵感、小说改编、剧本与分镜，到角色场景提示词、Seedan |
| 28 | `chengbenchao/storyboard-prompt` | 8 | 短剧分镜自动化工作流skill：剧本→分镜表→提示词生成，适配Seedance 2.0 |
| 29 | `nhanhxxm2can9351-glitch/script-to-storyboard` | 7 | 剧本转AI短剧高精度分镜提示词生成器（Skill）· Script to AI Short-Drama Storyboard Prompt |
| 30 | `Weeexiao/skills` | 6 | AI 短剧制作 Agent Skills 合集：剧本、分镜、提示词、资产、成片，按分类存放 |
| 31 | `Ye-Zayne/zhang-yimou-skill` | 6 | 张艺谋电影语言研究与短剧创作 Skill：从灵感到导演设定、原创剧本、彩色分镜与视频提示词。 |
| 32 | `huang20cheng-blip/muki-ai-drama-skills` | 5 | 一套面向 AI 短剧制作的 Codex Skills 工作流，覆盖剧本审校与改编、人物与场景提取、角色/场景提示词、Seedance 分镜生 |
| 33 | `MR-TianYuSun/ai-comic-drama-producer` | 5 | Ai漫剧统筹与规划专家（大语言模型SKILL） |
| 34 | `xiaosheng-01/manju-pipeline-v3` | 5 | 漫剧/AI动态漫/国漫短剧全流程制作Skill 3.0 |
| 35 | `Vallykrie/short-drama-finder-skill` | 3 | 🎬 AI agent skill to find the full series of any viral short drama, mic |
| 36 | `nicoxnicooo-lang/novel-to-anime-drama-skill` | 2 | 小说转AI动漫短剧工业化流水线skill |
| 37 | `QwenchC/manju-gen` | 2 | 适用于openclaw智能体的本地AI漫剧生成Skill（需要ComfyUI） |
| 38 | `ruijiaang-lab/ai-manju-visual-director` | 2 | AI 漫剧视觉导演 - 中文优先的导演插件与 Agent Skill 包 |
| 39 | `zhu5859243-free/hongguo-shortdrama-screenwriting` | 2 | 红果/抖音爆款短剧编剧：短剧工厂引擎 + 《短剧编剧第一课》01–10 期方法论 |
| 40 | `aimerfeng/omniboard-ai-comic-drama` | 1 | OmniBoard AI 漫剧制作画布：面向漫剧团队、IP 方、短剧编导、视觉创作者的AI 漫剧制作指南与 OmniBoard AI Ski |
| 41 | `Amouren7/ai-drama-production` | 1 | Agent技能：AI 短剧与漫剧制作方案生成器 skill — AI drama & motion comic producti |
| 42 | `kuang18075-arch/ai-comic-drama-pipeline` | 1 | Codex skill for an end-to-end AI comic drama pipeline: story, episodes |
| 43 | `lyd420/novel-to-drama-skill` | 1 | （描述为空，待核） |
| 44 | `momo5213/live-action-drama-16x9` | 1 | 16:9 真人精品短剧：剧本分析、分镜运镜、光影与细微表演、视频提示词、连续性审查 |
| 45 | `Alwzc/alphadrama-short-drama-skill` | 0 | 竖屏短剧全流程：网文或剧本改成 60 秒一集的节拍和台词，三视图锁角色，拆 12–18 镜 9:16 分镜，按镜头类型分给不同视频模型写提示词 |
| 46 | `Git-Nicolai/manju-scriptwriter` | 0 | AI ??/?????????? Skill - for TRAE |
| 47 | `gold3bear/ai-manju-skill` | 0 | （描述为空，待核） |
| 48 | `HEYD66/manju-production-skills` | 0 | AI manju production Codex skills and sample workbooks |
| 49 | `hlyhf/drama-studio` | 0 | Unified drama-creation control skill for AI agents — S-grade short/com |
| 50 | `icelikey/shuzhi-manju-skill` | 0 | ????:?? AI ??????????? Skill |
| 51 | `manju39850-debug/Manju` | 0 | Aspiring Software Developer & AI Enthusiast Showcasing Projects ,Skill |
| 52 | `qingwei77/ai-comic-drama-storyboard-skill` | 0 | （描述为空，待核） |
| 53 | `stimQQ/ai-short-drama` | 0 | Turn a story into a finished short drama / AI comic drama episode — co |
| 54 | `xiajixi76-beep/ai-manjue-production-skills` | 0 | Unified AI manju and cinematic short-video production skills |

### 编剧·改编（19）

剧本、改编、钩子、付费卡点、审稿。差异不在工具，在方法论。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 55 | `chatfire-AI/huobao-drama` | 17338 | 火宝短剧：一句话生成完整短剧，从剧本到成片全自动 |
| 56 | `dramaclaw/dramaclaw` | 7699 | 通用 AIGC 视频引擎：剧本到成片一条流水线，覆盖漫剧、广告、电商、乙游 |
| 57 | `shuyu-labs/BigBanana-AI-Director` | 2449 | BigBanana AI 导演：短剧/漫剧一站式平台，「剧本 → 资产 → 关键帧」工业化流程 |
| 58 | `lixiaoxiao9888-create/short-drama-factory` | 592 | 抖音/红果短剧工业化编剧：一句创意或一部网文 → 60–100 集带付费卡点的剧本，配钩子、断章、反转公式和机检规则 |
| 59 | `zhlmi/narrative-to-screen-reader` | 135 | 把手上的故事翻译成影视开发语言：快速诊断、编剧改编读本、导演视听读本、演员读本、制片摘要 |
| 60 | `Vi7QY/screenwriter-skill` | 108 | 短剧/漫剧剧本审稿：红果 Top100 操盘经验蒸馏的 38 条规则 |
| 61 | `rorojiao/drama-adapt-skill` | 68 | 网文改编漫剧剧本 Claude Code Skill - 五阶段全自动工作流，一键将网络小说改编为标准漫剧剧本 |
| 62 | `mudden2380078550-creator/write-chinese-long-screenplay` | 23 | Narrative Harness：中文小说与剧本创作的本地状态工具，旧版长剧本写作模板保留在 legacy/ |
| 63 | `ciel-oliver/analyze-hit-novel` | 19 | 爆款小说拆文：把爆款小说/漫剧拆成可验证的叙事系统，供改编参考 |
| 64 | `zhlmi/screenplay-review-checklist` | 16 | 对抗式剧本踩雷诊断：拿 37 条判据只给你的故事找问题 |
| 65 | `steve21985031/Siray-IdeaValidator-Skills` | 15 | Siray漫剧套件A类核心Skill - Idea Validator Pro (剧本商业评估专家) |
| 66 | `SumOneHK/short-drama-scriptwriter` | 15 | 剧本创作skill |
| 67 | `SumOneHK/tiktok-short-drama` | 13 | 出海剧本创作skill |
| 68 | `SSRYLJRSS/drama-script-writing` | 12 | AI短剧剧本撰写 Skill - 把真实社会热点事件改编成AI短剧剧本的完整S0-S7流水线（多案例糅合/序幕炸裂/对话驱动/题材不限/自动 |
| 69 | `egguy886/write-screenplay-skill` | 11 | 小说/设定转商业剧本，国内短剧与出海微短剧双模式 |
| 70 | `snoopyrain/vpick-short-video-agent` | 10 | VPick Short Video Agent — 5-stage short-drama production flow (script |
| 71 | `adoria111/emma-screenwriting-skills` | 7 | 艾玛短剧技能组：结构拆解、改编、选题迭代、期待设计、逐集钩子、集纲扩写、对白诊断、剧本删减 |
| 72 | `annalyseg805-blip/aisee-comic-to-drama` | 6 | 把漫画/图片剧情改编为真人短剧视频的 Agent Skill |
| 73 | `Cailing0501/short-drama-script-revision-framework` | 5 | AI短剧/漫剧剧本修改与润色系统框架 - Claude Code Skill |

### 角色·资产（29）

人物设定、三视图、角色一致性。生态里第二密集的方向。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 74 | `HBAI-Ltd/Toonflow-app` | 21721 | Toonflow：开源 AI 短剧/漫剧平台，剧本、智能分镜、角色场景资产、图像和视频生成，无限画布 + Agent |
| 75 | `eternityspring/shuohao-skills` | 6616 | 短剧制作 skill 集：拆角色、改编大纲、场景与道具美术设定、剧本、分镜 |
| 76 | `ArcReel/ArcReel` | 6500 | 可自部署视频工作台：小说/剧本 → 角色场景道具资产、分镜、视频和剪映草稿，含跨镜头一致性与费用追踪 |
| 77 | `0xsline/short-drama` | 1622 | 短剧编剧全流程：选题立项、故事骨架、四层反派人物、带钩子和付费卡点的分集目录、逐集剧本、五维评分自检和合规审核，可切出海英文格式 |
| 78 | `Shanyin-ai/shanyin-screenwriting-master` | 1493 | 山音超级编剧大师：概念超短片、叙事短片、长片、多集剧集四种格式的人物、大纲、场景拆解和完整剧本 |
| 79 | `alibaba/lumenx` | 1481 | 阿里 LumenX Studio：小说到动态视频的短漫剧一站式生产，剧本分析、角色定制、分镜、视频合成 |
| 80 | `shijue-aid/aid-studio` | 1420 | AID Studio：可自部署的 AI 漫剧/短剧创作平台，剧本、角色场景资产、分镜、图片与视频生成、配音和成片预览，也能做短片和漫画 |
| 81 | `liyue-aigc/seedance-2-5-video-director` | 797 | Seedance 2.5 视频导演：提示词、脚本、诊断、人物锁定、续写、编辑、转场 |
| 82 | `VanGong1999/screen-creative-skills` | 510 | 影视策划与评估：小说/IP 评估、情节点拆解、人物小传与关系、大纲、小说改编短剧或长剧 |
| 83 | `zhaihao118/Micro-Drama-Skills` | 336 | 短剧全流程自动化：剧本、角色设计、分镜、出图出视频与提交 |
| 84 | `phileiny/h3-storyboard-skill` | 197 | MiniMax H3 分镜拆解与角色表演设计 |
| 85 | `oiuv/ai-short-drama` | 48 | 雪风爽剧：一句话补全创作需求，按爽点模型写分集剧本并同步角色/场景/道具档案，再拆镜写 Seedance 2.0 提示词 |
| 86 | `chengbenchao/short-drama-script` | 43 | 短剧剧本生成Skill：小说/IP自动改编为标准横/竖屏短剧剧本，包含梗概/人设/分集大纲/逐集正文/卡点标注 |
| 87 | `Work-Fisher/fisher-storylens` | 41 | 面向 Z-Image、Qwen-Image 2.1 与 MiniMax H3 的短剧制作 Skill：角色与场景提示词、图片确认、15秒分镜 |
| 88 | `zhangxiansheng-888/chuanzhang-ai-shortdrama-skills` | 39 | 船长AI视界 AI 短剧制作技能集：大纲、角色、参考图、场景、剧本、分镜 |
| 89 | `JohnKeating1997/spark-video` | 34 | 一句梗概 → 剧本、分镜、角色/场景/道具一致性、渲染、逐镜 AI 质检到成片 mp4，每阶段设确认关卡 |
| 90 | `nigo-studio/ai-film-skills` | 27 | 从 AI 动作片《CROW LINE》流程拆出的 skill：Seedance 2.5 参考生视频提示词导演，三联角色设定图保持跨镜一致 |
| 91 | `jlam00-dev/hardcore-director` | 22 | 硬核导演：影视与 AI 视频总控，按阶段路由编剧/短剧、角色场景、分镜、Seedance 2.5/Wan 3.0/H3 提示词、声音与剪辑模块 |
| 92 | `ilkaydemiralay/vision_art_creator` | 17 | 影视部门式 skill 包：编剧、导演、角色、美术、摄影、分镜、镜头表、提示词、声音、剪辑，由总监 skill 调度和质检 |
| 93 | `babicat4242-svg/seedance-2-5-prompting` | 16 | Seedance 2.5 提示词：参考素材角色绑定、30 种运镜定义与冲突规则、R2V/白模、局部编辑与延长、多轮修改流程 |
| 94 | `daguaid341-cpu/write-30-second-storyboards` | 11 | Rui-Skills：漫剧与真人剧独立制作，默认30秒分镜；支持小说改编、大纲、人物与场景道具设定、剧本、角色资产管理，以及ANERNEQ（ |
| 95 | `e06084/claude-screenwriting` | 10 | 编剧知识引擎：把 Vogler/McKee/救猫咪落成 Obsidian 故事 wiki，15-beat 节奏、三层角色卡、结构诊断 |
| 96 | `senmanx/s-level-comic-character` | 9 | S级漫剧3D写实角色概念设计 Skill：输入小说片段，自动提取人物与道具，输出4套标准化AI绘画提示词（3D全身/真人全身/GPT-A半身 |
| 97 | `z2x7d54/ai-drama-director-skill` | 8 | AI短剧导演 Skill · AI Short Drama Director Skill 8.0：剧本转分镜、人物空间、镜头衔接、情感表演、 |
| 98 | `ouyangevan/codex-short-drama-pipeline-skill` | 6 | AI 短剧流水线 Codex Skill：从创意、角色、分镜和提示词到 QC 与发布包 · AI short-drama productio |
| 99 | `ayase0307/ai-comic-drama` | 2 | Agent Skill: turn novels/stories into character-consistent AI comic dr |
| 100 | `89694021-hue/xiaolei-ai-comic-drama-lite` | 1 | 面向普通用户的 Codex AI 漫剧 Skill：小说拆集、人物卡、分镜与逐镜提示词；免费开源，无需 API Key，不要求编程。 |
| 101 | `jiaxinmmhh/novel-to-consistent-drama-stills` | 0 | 小说文档 → 人物证据与三视图定稿 → 高光故事板 → 参考图优先的固定人物剧图 Skill |
| 102 | `jodancain/ai-manju-pipeline` | 0 | AI 漫剧制作管线 skill：故事节奏、角色设定表、场景尺度、道具状态、时间戳与镜头检查 |

### 服装·造型（2）

服装设定板、换装、立绘补全。**全生态只有这 2 个**，且都不专攻「跨集服装演进」。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 103 | `lmy414/ai-chan-sheets` | 568 | AI 娘立绘的横版完整设定图补全：拆解为三视图/表情/服装，输入立绘输出设定板 |
| 104 | `zhurui0523/XiaoLuo-AI-Drama-Skill` | 523 | 小逻系列：剧本分析、原创改编、分镜脚本、角色三视图/服装/表情、场景布局 |

### 场景·美术（1）

场景母版、空间一致性。**真正做场景资产的只有 1 个**，九宫格与机位矩阵在生态里没有对手。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 105 | `zhouwei713/chinese-epic-scene-director` | 15 | 中国式宏大场景：把一句设定扩写成仙侠/神话短片故事，建连续性台账，按镜头成对输出图片和视频提示词 |

### 分镜（41）

镜头设计、运镜、镜头表。数量最多的实用档，但多数只到「分镜脚本」，不落地到可生成。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 106 | `Forget-C/Jellyfish` | 7179 | AI 短剧端到端工作台：剧本输入、结构化分镜、一致性管理、视频生成 |
| 107 | `popopo-99/zy-cinematic-realism` | 684 | 造梦师：把剧本、故事或场景想法开发成有动机的叙事关键帧，编译成各生图模型的原生提示词，支持连续组图与结果修复 |
| 108 | `Shanyin-ai/shanyin-director-master` | 636 | 山音超级导演大师：剧本 → 导演定调、节奏规划、剧本微调、分镜拆解，输出九列分镜表（xlsx），内置类型片导演风格模板 |
| 109 | `A-cat-with-carrots/OnlyShot` | 411 | 神仙鱼短剧流水线：一句话 → 剧本、分镜、分镜图、视频、剪辑五步，沉淀 17 种失败模式 |
| 110 | `machina-exm/film-studio-skills` | 174 | 剧本 → 锁定、可直接生成的镜头：7 个 skill 复刻商业 AI 视频制作流程 |
| 111 | `woodfantasy/Seedance-ShotDesign-Skills` | 136 | Seedance 2.5 镜头设计 |
| 112 | `SlavaSexton/ComfyUI-Agent-Kit` | 123 | 驱动本地 ComfyUI 出图出视频，附 Seedance、MiniMax H3 视频提示词 skill：多镜头分镜、参考素材标注、翻车排查 |
| 113 | `zyz254009-crypto/script-to-shootable-storyboard` | 119 | 使用 Codex 开发的剧本转可拍分镜 Skill，在 Codex 中运行效果最佳，支持 Seedance、真人/混合制作与二次开发。 |
| 114 | `xixihhhh/ai-short-drama-skill` | 99 | Dramake：文字转 AI 短剧，串起剧本、分镜、配音、剪辑与质检，适配抖音/红果和横竖屏，自带 evals |
| 115 | `Hao0321/ai-short-drama` | 81 | 把「重生、逆袭、隐藏大佬」等题材编译成有爽点和追更钩子的连载：题材调研、故事架构、镜头时间线、连续性校验 |
| 116 | `doublesq97-ui/su-ai-short-drama` | 70 | 中文 AI 短剧编剧、导演、选角与分镜协作 Codex Skills（女频 / 男频双版本） |
| 117 | `mwddmmde12-del/storyboard-artist` | 57 | 专业分镜师 Skill：脚本→电影级分镜→Veo 3.1 & 即梦 Seedance 2.0 提示词 |
| 118 | `10291124jcjc-dotcom/ai-science-series` | 54 | AI 科普短剧 Skill：外星人陪你打赌，查证 + 剧情架构 + 自动出即梦分镜和视频提示词 · Realistic two-charac |
| 119 | `Yvelinmoon/ai-manga-drama` | 39 | ai-manga-drama Claude Code Skill - AI漫剧导演，完整漫剧制作流水线：镜头规划→分镜图→视频生成→视频合并 |
| 120 | `AGI-Ruby/ai-GPT_Image2-Seedance_2.0-video-skills` | 37 | Reusable Codex skills for GPT Image 2 storyboards, Seedance 2.0 video |
| 121 | `kevinchin12/storyboard-director` | 37 | 故事 → 分镜脚本，子代理并行生成逐镜线稿，HTML 审片板返修指定镜头，确认后汇总成按镜头排序的视频提示词 |
| 122 | `muxia0396/novel-to-ai-short-drama-skill` | 35 | 从导演视角把小说改编成 AI 短剧：分镜、运镜、表演调度与时长 |
| 123 | `fanchengchen1-collab/super-director` | 28 | 🎬 超级导演系统 · A director's judgment installed into Claude — 光影/分镜/调度图/节奏/ |
| 124 | `anyhui/video-storyboard-gen-skill` | 27 | 中文视频分镜与 AI 视频提示词 Skill：故事结构、逐镜脚本、Seedance/即梦提示词、确定性 CLI 与发布校验 |
| 125 | `SoloEnt-AI/5min-drama-contest` | 27 | 五分钟短剧剧本：一步一问锁定赛道、立意、结构原型和前 30 秒开场，四幕卡点大纲 → 正式剧本 → 分镜脚本 |
| 126 | `tttg2010/tj-short` | 26 | Codex / WorkBuddy 短剧带货 Skill：salpx 生成分镜首帧，salpx Wan 3.0 直出 2–30 秒视频（多图 |
| 127 | `wumajiehechuan-lab/hermes-tvc-pipeline` | 26 | Hermes Agent 双 Skill 组合：TVC 广告创意导演 + 故事板生成器。tvc-director v4.0 产出结构化镜头列 |
| 128 | `MIKA6941/Comfy-H3-Director` | 21 | MiniMax H3 漫剧导演：网文改分镜、核心/龙套资产分级、文戏长镜与武戏快切、动作连续性锁定、尾帧接力，一次出整集提示词 |
| 129 | `wddxh/ShortVideoDirector` | 21 | 4 个子代理协作，把故事创意转成视频分镜和资产提示词，可调用即梦 CLI 出图、提交视频任务 |
| 130 | `yanshangcha01/libtv-shortdrama-storyboard` | 21 | LibTV 男频短剧 AI 分镜工作流：输入剧本自动分析爽感、拆锚点与分镜、批量建 LibTV 节点（生图/生视频）。生成按钮留给用户。任何 |
| 131 | `dafenq/DirectorFrame-AI` | 19 | **DirectorFrame AI** 是一款面向漫剧、短剧和小说改编的 AI 分镜生产桌面应用。它基于无限画布、导演 DSL、Promp |
| 132 | `vvlife/FreeVideoSkill` | 18 | 🎬 综合视频创作全流程Skill · 免费Agnes AI API · 支持短剧/漫剧/商业广告/UGC口播 · 剧本→分镜→资产→关键帧→ |
| 133 | `buluslan/seedance-video-script` | 16 | Seedance 2.5 视频分镜提示词生成 Skill for Agent · 把商业意图+素材转成可直接用的视频脚本prompt · T |
| 134 | `luanyi824-hash/xiaxia` | 15 | 夏夏：把确认剧本转成带时长预算、机位焦段、真实光源、调度与动作因果的导演分镜，可编译为 Seedance 2.5 任务 |
| 135 | `wwaa34682-lab/novel-to-short-drama-skill` | 15 | 小说→AI短剧 7步流水线通用技能（改编/验收/压节奏/分镜/资产/分镜图/图生视频） · Novel-to-AI-short-drama |
| 136 | `10291124jcjc-dotcom/ai-fable-series` | 14 | AI 动物寓言短剧 Skill：智者动物拆穿日常习惯和广告套路，查证 + 固定开头公式 + 自动出即梦分镜和视频提示词 · 2D anima |
| 137 | `jis60224/ai-comic-skills` | 13 | 小白新手也能用这个skill创作出ai漫剧。从剧本到分镜到剪辑出片。 |
| 138 | `1647371283/cineflow-skill` | 11 | 影流 CineFlow v2.0 · 全流程AI影视创作引擎（12大路径）。触发：我要做/想做/帮我做+视频/短片/短剧/故事/剧本/分镜/ |
| 139 | `rfdiosuao/Yuhang-ManJu` | 8 | 面向 AI 视频创作的镜头运动、风格库与提示词模板 Skill |
| 140 | `zcx960/seedance-storyboard` | 7 | 把剧本文字一键转成 Seedance/即梦 文生视频分镜脚本 · A Claude Skill that turns screenplay |
| 141 | `ouxxyy/storyboard-scavenger` | 6 | AI 视频分镜与提示词生成 Skill：创意转七要素分镜，提供 Kling／Seedance 工作流和运镜参考。AI video story |
| 142 | `TateZhouSiu/create-storyboard-skill` | 6 | Codex skill for continuity-first storyboard packages for Image 2 and S |
| 143 | `xiaosheng-01/manju-storyboard` | 1 | AI manhua-drama storyboard skill v2.1.4 (self-contained; SKILL.md + re |
| 144 | `guhy9muzhi-cyber/ai-manju-director` | 0 | Codex Skill for turning Chinese stories into AI comic-drama storyboard |
| 145 | `Konamiu/skills` | 0 | AI 短剧的 Claude Code skills：storyloom 写剧本，manju 拍剧（分镜、出图、配音、剪辑、真人模式） |
| 146 | `ohmyopictures-cmyk/short-drama-starter` | 0 | AI 短剧新手七条规则：60 秒五段节拍、一个提示词只写一个镜头、六种入门运镜、锁住人脸、提示词固定顺序、生成前先确认花费 |

### 视频提示词（23）

Seedance / H3 / 可灵 的提示词工程。模型换代快，这一档时效性最强。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 147 | `dexhunter/seedance2-skill` | 4475 | 为 Seedance 2.0 生成高质量视频提示词 |
| 148 | `xuanyustudio/LocalMiniDrama` | 2438 | 本地运行的 AI 短剧/漫剧工具：故事到成片，项目数据存在本机，图片和视频走云端 API，已接入 Seedance 2 |
| 149 | `liangdabiao/make-prompt-seedance2` | 764 | Seedance 2.0 结构化提示词写法与通用 skill |
| 150 | `smixs/visual-skills` | 671 | AI 电影导演：Murch 剪辑、走位、蒙太奇等戏剧法则 + Seedance 精确提示词语法 |
| 151 | `jnMetaCode/ai-shortfilm-prompts` | 533 | 把任意想法变成电影感、可直接投喂模型的视频提示词 |
| 152 | `nutllwhy/seedance-tvc-director` | 345 | A Seedance 2.5 TVC director Skill for 15s, 30s and custom commercial v |
| 153 | `T8mars/minimax-h3-prompt-skill-T8` | 334 | MiniMax H3 / Seedance 2.0 视频提示词案例库与可安装 skill，附视频浏览器 |
| 154 | `SwotAtmk/infinite-creation` | 331 | 提交小说或剧本，用本地 ComfyUI + MiniMax H3 + Agent 自动连续生产视频，不限时长 |
| 155 | `YvonneMovingon/short-drama-skills` | 101 | LuxReal 生产验证的短剧提示词：叙事拆解、情绪刻画、动态描述、剧情拆分、视频提示词润色 |
| 156 | `lixiaoxiao9888-create/forest-laoli-h3` | 72 | 漫剧老李 · MiniMax H3（海螺 3.0）短剧全流程 Skill v2.1.1 · forest-laoli-h3 — 剧本→资产→ |
| 157 | `alchaincyf/seedance-skill` | 63 | 白模驱动的 Seedance 工作台：用 scene.json 渲染白模参考视频并做几何体检，可从照片反解白模，按白模几何写提示词 |
| 158 | `mini-yifan/open-source-video-gen-skill` | 40 | Vibe Video：在 AutoDL 上跑开源 MiniMax H3 出片，短剧模板串起 Brief、分集概要、剧本台词、美术和视频，含 H3 提示词 |
| 159 | `kianaliang-dev/drama-director-skill` | 34 | One API key, two calls: GPT Image 2 + Seedance 2.0 comic-drama workflo |
| 160 | `Susanzz101/Susan-AI-Video-Prompt-skill` | 17 | Susan-AI视频提示词生成智能体，专为AI视频生成设计，主用于生成高质量AI视频提示词。目前支持沉浸式吃播、服装展示、口播带货、产品演示 |
| 161 | `YourAiBuddyJie/minimax-h3-director-suite` | 11 | Codex skills for directing and running MiniMax H3 short-drama projects |
| 162 | `Taomitown/douyin-transcript-exporter` | 10 | Doubao 漫剧制作技能集 一套面向 抖音漫剧工业化生产 的豆包工作台技能（Skill）集，覆盖从写小说到出图提示词的完整链路，支持 一条 |
| 163 | `prepfinders/seedance2-api` | 5 | Seedance 2.0 API Guide · ByteDance AI Video Generation Model with Mult |
| 164 | `kaixiong055-debug/ai-drama-skills-avs-refmod` | 2 | Production-ready AI drama skills for MiniMax H3 & ComfyUI: novel-to-st |
| 165 | `Loser2643307956/ai-manju` | 1 | Codex Skill for local MiniMax H3 AI animated shorts with FFmpeg and lo |
| 166 | `Vanclife/DirectorReady-ai-comic-drama-prompt-skill` | 1 | 提示词公开 |
| 167 | `liangyunbin/lybskill` | 0 | Lightweight AI comic-drama shot design, prompt compilation, continuity |
| 168 | `liuyanjunjsj/yuh-h3-prompt-skill` | 0 | YUH Studio canvas x MiniMax H3 drama prompt skill (optional): novel-to |
| 169 | `wuluqi-cg/ai-manju-skill` | 0 | AI 漫剧 Skill - generate .docx with asset prompts, video prompts, screen |

### 打戏·动作（4）

动作编排、交锋因果、轨迹图。**仅 4 个，全是单人作品**，且都偏「写提示词」而非「设计动作因果」。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 170 | `liyue-aigc/seedance-2-5-fight-director` | 125 | Seedance 2.5 高燃打戏导演：提示词与诊断 |
| 171 | `qualsenWeb/fight-video-create-skill` | 110 | AI 打戏设计：从打斗构思到剧情、动作、分镜，带招式校验和参考库 |
| 172 | `irenerachel/fight-prompt-director` | 80 | AI 打戏提示词：角色差异化动作、交锋因果链、跨镜连续性，出高强度/慢节奏/中间型三版，适配 Seedance 与 H3 |
| 173 | `ZzzAloong/fight-scene-director` | 34 | 多画风打戏设计：动作编排、空间调度、镜头与特效规则，可先出站位图/轨迹图生图词，再按轨迹写视频提示词 |

### 特效·粒子（0）

**这一档是空的。** 192 个仓库里没有一个专门做特效/粒子/光效。相关内容都散落在全流程里，通常只有一两句话（「特效要华丽」）。这也是 `11-vfx-and-particles.md` 里「去水五律」只能自己从生成结果反推的原因。

### 写作·方法论（3）

去 AI 味、文风、编剧理论。可跨题材复用。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 174 | `KKKKhazix/human-writing` | 4586 | 活人感写作：让 AI 写的中文像具体的人在说话，适合打磨对白和旁白 |
| 175 | `Nanako0129/sepia` | 3809 | 面向小说的去 AI 味：修复叙事结构，按场合匹配文风规则，方法来自 StoryScope 论文 |
| 176 | `jtydhr88/screenwriting-skills` | 2060 | 编剧理论最系统的一套：结构、Truby、场景、对白、剧集圣经、编剧室，含日韩法美与中国戏曲案例 |

### 平台·应用（5）

完整可部署平台，不是 skill，仅供对照。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 177 | `waooAI/waoowaoo` | 14856 | AI 影视 Agent 工作台（预览版）：图片与视频创作，从短片到真人可控成片 |
| 178 | `yi1108/printfilm` | 7427 | PRINTFILM：AI 短视频营销与 AI 短剧创作平台 |
| 179 | `Stonewuu/ai-fusion-video` | 1760 | 融光：基于 Agent 的全流程 AI 短剧/漫剧/视频创作平台（Java + AgentScope） |
| 180 | `VanGong1999/juben` | 186 | multi-agent platform for short-drama planning, writing & evaluation — |
| 181 | `yunbanfengwu/novelcomic` | 1 | Novel + comic-drama generation platform driven by skills, knowledge an |

### 其他（1）

分类存疑或描述缺失，需逐个核。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 182 | `ldmsapp76-max/seedance-storyboard-skill` | 17 | （描述为空，待核） |

### 元清单（10）

元清单（收录别人，本身不是 skill），用来看全景最省力。

| # | 仓库 | ★ | 说明 |
|---:|---|---:|---|
| 183 | `blader/humanizer` | 68881 | 按维基百科「Signs of AI writing」清单去除 AI 写作痕迹 |
| 184 | `LearnPrompt/awesome-seedance` | 2531 | Seedance 2.5/2.0 提示词库：800+ 条可追溯原帖的案例、近 500 次跨模型复测，附 skill |
| 185 | `UnderleveledBuilder/awesome-short-drama-skills` | 2332 | AI 短剧 · 漫剧 Skill（技能包）精选：剧本、改编、分镜、Seedance / 可灵 / MiniMax 视频提示词，千问、豆包、龙 |
| 186 | `OSideMedia/higgsfield-ai-prompt-skill` | 916 | Higgsfield 平台提示词：MCSLA 公式、Seedance 2.5 多参考导演、表演指导、Soul ID 角色一致性、镜头清单与失败诊断 |
| 187 | `cclank/lanshu-awesome-ai-video-kit` | 454 | 企业 AI 视频项目工具包：Seedance/可灵提示词、分镜、模型选择与调试，附 600 多条 prompt 和方法论 |
| 188 | `wuwangzhang1216/DirectorSKILL` | 357 | AI 拍片：镜头清单、关键帧与视频提示词，内置斯皮尔伯格等 20 种导演风格 |
| 189 | `AtlasCloudAI/awesome-seedance-2.5-prompts-skills` | 268 | Seedance 2.5 提示词库 + skill：按 T2V/R2V/I2V 选路线、Seedream 故事板、多参考与镜头连续性设计 |
| 190 | `zlbigger/story-video-director` | 35 | 把任意故事变成图片素材、分镜、中文视听提示词与 API 调用清单 |
| 191 | `leynos/visual-storytelling-skills` | 11 | 从文字到画面：场景清单、镜头设计、视频模型提示词、视频生成 |
| 192 | `OakcoderX/awesome-agent-skills` | 2 | 苏格拉底式故事诊断：对小说、剧本、分集大纲先提几种对立解释，拿原文证据和反例检验，再给最小改动，也可以判不用改 |

---

## 怎么用这份清单

1. **要架构灵感** → 读「全流程」前五名与第四节那十个
2. **要补短板** → 看「服装 / 场景 / 打戏 / 武器 / 特效」五档，人少但差距大
3. **要提示词案例** → 「视频提示词」档，先核对模型版本，半年前的可能已失效
4. **要对照自己的 skill** → 先看第三节的位置判断，再决定往哪加厚
