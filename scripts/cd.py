#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""漫剧制作 · 机检与工具链

只做确定性工作：解析 Markdown、核对引用、算术、词根扫描。
不判断创作好坏（那是审查的事）。

子命令：
  init     建项目骨架
  check    分层检查（S 结构 / R 引用 / X 执行 / A 资产 / C 合规 / M 模型 / Q 条件）
  estimate 时长折算
  pack     从分镜生成投喂稿骨架
  board    渲染单页看板

零依赖，Python 3.9+。
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

MINIMUM_PYTHON = (3, 9)

# ---------------------------------------------------------------- 常量

SHOT_MIN, SHOT_MAX = 2.0, 8.0
LINE_HEADROOM = 0.4          # 台词镜收口余量（语速改真实值后不再叠厚）
# 中文对白的「可发声字/秒」。多家实测口径在 3.5~5 之间：
# 旁白 3.5~4、日常对白 3.5~4、激烈 4~4.8、4.5 以上只是极端上限。
# 旧值 5.5/5.8 会让折算时长偏短三成，配音必然赶词或截断。
DEFAULT_CPS = 4.0
PAUSE = 0.45                 # 句末留白
LINE_MAX_CHARS = 15          # 单句台词上限（9:16 竖屏基准）
# 画幅分档：同一条规则不能两档通吃。
# 9:16 竖屏＝快节奏，句子要短、镜头可以更碎；
# 16:9 横屏＝半精品，有呼吸空间，句子可以长一点、镜长下限也高一点。
FORMAT_TUNING = {
    "9:16": {"line_max": 15, "shot_min": 1.2, "cps": 4.2},
    "16:9": {"line_max": 20, "shot_min": 2.0, "cps": 3.7},
    "21:9": {"line_max": 20, "shot_min": 2.0, "cps": 3.7},
    "4:3":  {"line_max": 18, "shot_min": 2.0, "cps": 3.8},
    "1:1":  {"line_max": 16, "shot_min": 1.5, "cps": 4.0},
    "3:4":  {"line_max": 16, "shot_min": 1.5, "cps": 4.0},
}


def spec_ar(cfg):
    return str((cfg.get("spec", {}) or {}).get("aspect_ratio", "") or "未定")


def tune(cfg, key, default):
    """按画幅取阈值。未登记的画幅回落到默认值。"""
    ar = str((cfg.get("spec", {}) or {}).get("aspect_ratio", ""))
    return FORMAT_TUNING.get(ar, {}).get(key, default)
TOLERANCE = 0.15             # 时长偏差容忍

# 模型规格：名称别名 -> (单段上限秒, 参考位上限, 是否在服役)
# 数据核验 2026-11-15，详见 references/22-model-matrix.md
# 模型档案 · 32 个主流模型。
# 两个维度：① 能力参数（时长/参考图/音频/画幅）② 提示词范式（A~E）。
# 参数是**保守上限**，用途是拦住超长镜与超量参考图；官方改版后请改这里，别改检查逻辑。
# 范式比型号稳定：模型换代时范式往往不变，先认范式再认型号。
MODEL_PROFILE = {
    # ---- 视频 · 范式 A：结构化分段（分段 + 时间轴 + 分字段） ----
    "seedance-2.5": dict(kind="video", vendor="字节 / 即梦", dur=30, refs=50, alive=True,
                         paradigm="A", audio=True, aspect="9:16,16:9,1:1",
                         note="多模态参考能力最强；七段式原生适配"),
    "seedance-2.0": dict(kind="video", vendor="字节 / 即梦", dur=15, refs=12, alive=True,
                         paradigm="A", audio=True, aspect="9:16,16:9",
                         aliases=["seedance-2.0-mini"]),
    "minimax-h3": dict(kind="video", vendor="MiniMax / 海螺", dur=15, refs=12, alive=True,
                       paradigm="A", audio=True, aspect="9:16,16:9",
                       aliases=["h3", "hailuo-3", "海螺3"],
                       note="三字段 / 六段式；词根极敏感，否定词会被画出来"),
    "kling-3.0": dict(kind="video", vendor="快手 可灵", dur=15, refs=5, alive=True,
                      paradigm="A", audio=True, aspect="9:16,16:9,1:1",
                      aliases=["kling3", "kling-2.5", "可灵"]),
    "wan-3.0": dict(kind="video", vendor="阿里 通义万相", dur=30, refs=15, alive=True,
                    paradigm="A", audio=True, aspect="9:16,16:9",
                    aliases=["wan3", "万相"]),
    "vidu-q2": dict(kind="video", vendor="生数 Vidu", dur=10, refs=4, alive=True,
                    paradigm="A", audio=False, aspect="9:16,16:9",
                    aliases=["vidu"]),
    "dreamina": dict(kind="video", vendor="字节 即梦", dur=12, refs=4, alive=True,
                     paradigm="A", audio=True, aspect="9:16,16:9", aliases=["即梦"]),
    # ---- 视频 · 范式 B：自然语言散文（一段连续描述，不写字段） ----
    "veo-3.1": dict(kind="video", vendor="Google", dur=8, refs=1, alive=True,
                    paradigm="B", audio=True, aspect="16:9,9:16",
                    aliases=["veo3.1", "veo-3"], note="只吃首尾帧；长句自然语言最稳"),
    "sora-2": dict(kind="video", vendor="OpenAI", dur=12, refs=2, alive=False,
                   paradigm="B", audio=True, aspect="16:9,9:16",
                   aliases=["sora2"], note="已停服，须迁移"),
    "runway-gen4": dict(kind="video", vendor="Runway", dur=10, refs=3, alive=True,
                        paradigm="B", audio=False, aspect="16:9,9:16", aliases=["runway"]),
    "luma-ray3": dict(kind="video", vendor="Luma", dur=10, refs=2, alive=True,
                      paradigm="B", audio=False, aspect="16:9,9:16", aliases=["luma"]),
    "pika-2": dict(kind="video", vendor="Pika", dur=10, refs=2, alive=True,
                   paradigm="B", audio=False, aspect="16:9,9:16", aliases=["pika"]),
    "pixverse-v5": dict(kind="video", vendor="PixVerse", dur=5, refs=4, alive=True,
                        paradigm="B", audio=False, aspect="16:9,9:16", aliases=["pixverse"]),
    "ltx-2.5": dict(kind="video", vendor="Lightricks", dur=20, refs=4, alive=True,
                    paradigm="B", audio=False, aspect="16:9", aliases=["ltx"]),
    "hunyuan-video": dict(kind="video", vendor="腾讯 混元", dur=16, refs=3, alive=True,
                          paradigm="B", audio=False, aspect="16:9,9:16", aliases=["混元"]),
    "gemini-omni": dict(kind="video", vendor="Google", dur=10, refs=8, alive=True,
                        paradigm="E", audio=True, aspect="16:9,9:16"),
    # ---- 图像 · 范式 C：标签堆叠（逗号分隔关键词 + 权重） ----
    "midjourney-v8": dict(kind="image", vendor="Midjourney", dur=0, refs=3, alive=True,
                          paradigm="C", audio=False, aspect="多比例",
                          aliases=["midjourney", "mj", "mj-v8"]),
    "flux-1.1": dict(kind="image", vendor="Black Forest", dur=0, refs=2, alive=True,
                     paradigm="C", audio=False, aspect="多比例", aliases=["flux"]),
    "sd-3.5": dict(kind="image", vendor="社区", dur=0, refs=2, alive=True,
                   paradigm="C", audio=False, aspect="多比例", aliases=["sd", "sdxl"]),
    "recraft-v3": dict(kind="image", vendor="Recraft", dur=0, refs=2, alive=True,
                       paradigm="C", audio=False, aspect="多比例", aliases=["recraft"]),
    # ---- 图像 · 范式 D：指令式编辑（保持什么 + 只改什么） ----
    "gpt-image-2": dict(kind="image", vendor="OpenAI", dur=0, refs=6, alive=True,
                        paradigm="D", audio=False, aspect="1:1,3:4,2:3,16:9",
                        aliases=["gpt-image", "dalle"],
                        note="文字与排版执行最强；改图比重新生成稳"),
    "nano-banana-pro": dict(kind="image", vendor="Google", dur=0, refs=8, alive=True,
                            paradigm="D", audio=False, aspect="1:1,3:4,2:3,16:9",
                            aliases=["nano-banana", "nano-banana-2", "gemini-image"],
                            note="主体一致性最强，多格图首选"),
    "flux-kontext": dict(kind="image", vendor="Black Forest", dur=0, refs=3, alive=True,
                         paradigm="D", audio=False, aspect="多比例"),
    # ---- 图像 · 范式 B：自然语言 ----
    "seedream-4": dict(kind="image", vendor="字节 即梦", dur=0, refs=6, alive=True,
                       paradigm="B", audio=False, aspect="多比例",
                       aliases=["seedream", "即梦图像"],
                       note="中文语义与国风最强，中文海报几乎不出错字"),
    "qwen-image": dict(kind="image", vendor="阿里", dur=0, refs=4, alive=True,
                       paradigm="B", audio=False, aspect="多比例", aliases=["通义万相图像"]),
    "ideogram-3": dict(kind="image", vendor="Ideogram", dur=0, refs=2, alive=True,
                       paradigm="C", audio=False, aspect="多比例", aliases=["ideogram"]),
    "firefly": dict(kind="image", vendor="Adobe", dur=0, refs=2, alive=True,
                    paradigm="B", audio=False, aspect="多比例",
                    note="商用授权最干净"),
    "grok-image": dict(kind="image", vendor="xAI", dur=0, refs=3, alive=True,
                       paradigm="B", audio=False, aspect="多比例"),
    "kolors": dict(kind="image", vendor="快手", dur=0, refs=3, alive=True,
                   paradigm="B", audio=False, aspect="多比例", aliases=["可图"]),
}


def _build_model_index():
    idx = {}
    for k, v in MODEL_PROFILE.items():
        idx[k] = v
        for a in v.get("aliases", []):
            idx[a.lower()] = v
    return idx


MODEL_INDEX = _build_model_index()

# 兼容层：老逻辑读 (时长上限, 参考图上限, 是否在服役)
MODEL_CAPS = {k: (v["dur"], v["refs"], v["alive"]) for k, v in MODEL_INDEX.items()}


def model_profile(name):
    """按名称查完整档案（含范式）。匹配不到返回 None。"""
    if not name:
        return None
    key = str(name).strip().lower().replace(" ", "-").replace("_", "-")
    if key in MODEL_INDEX:
        return MODEL_INDEX[key]
    for k, v in MODEL_INDEX.items():
        if k in key or key in k:
            return v
    return None


def model_spec(name):
    """兼容层：返回 (时长上限, 参考图上限, 是否在服役)。"""
    v = model_profile(name)
    return (v["dur"], v["refs"], v["alive"]) if v else None

ACTION_DUR = {
    "位移": (3.0, ("走", "跑", "冲", "起身", "转身", "推门", "推开", "退", "扑", "奔")),
    "小幅": (2.2, ("抬手", "转头", "点头", "摇头", "伸手", "落座", "坐下", "抬眼", "低头", "松手")),
    "微动": (1.8, ()),
}

# 词根污染（X3）
NEGATION = ("不要", "没有", "禁止", "避免", "毫无", "不得", "不准")
METAPHOR = ("如钟", "似箭", "像刀", "成线", "成串", "成股", "如潮", "似水", "仿佛", "宛如")
PSYCH = ("意识到", "想着", "感到", "明白过来", "决定", "犹豫", "心里", "内心", "回想起")
ABSTRACT = ("压迫感", "氛围感", "电影感", "高级感", "张力十足", "唯美", "大气", "震撼",
            "moody", "cinematic", "atmospheric", "volumetric")
FORBIDDEN_IN_BAN = ("保持", "确保", "必须", "要求")   # 禁止项里混入正向指令
HEAD_CUT = ("headless", "cropped head", "砍头", "无头", "自颈部截断", "头部不入画")
MOSAIC = ("mosaic", "pixelated", "censored", "马赛克", "像素化", "打码")
VFX_BAN = ("粒子",) + ABSTRACT
SELF_REF = ("同上", "见母版", "同图", "同规格", "参照前文", "其余同理")

# ---------------------------------------------------------------- 人物图式
# 版式决定一切：同一个角色，要参考图和要海报是两套写法。见 references/26-figure-layouts.md
LAYOUTS = {
    "portrait":   dict(name="头像 / 半身", ratio="1:1", grids=1,
                       bg="纯色或渐变", light="影棚柔光", ref=True,
                       use="社媒、卡面、聊天头像"),
    "fullbody":   dict(name="单人全身立绘", ratio="2:3", grids=1,
                       bg="纯色 / 渐变 / 简化环境", light="影棚或戏剧光", ref=True,
                       use="宣发、角色页、出图"),
    "three-view": dict(name="三视图", ratio="16:9", grids=3,
                       bg="纯白无缝", light="平光", ref=True,
                       use="建模、设定参考（要体态不要脸时首选）"),
    "four-view":  dict(name="四视图", ratio="16:9", grids=4,
                       bg="纯白无缝", light="平光（第①格柔光）", ref=True,
                       use="设定参考，本 skill 原「四格板」"),
    "profile":    dict(name="角色档案图", ratio="2:3", grids=0,
                       bg="设计化底色", light="混合", ref=False,
                       use="设定集、设定海报"),
    "expression": dict(name="表情集", ratio="16:9", grids=4,
                       bg="纯白或极浅灰", light="正面平光", ref=True,
                       use="演出参考、表情包"),
    "outfit":     dict(name="服装拆解板", ratio="16:9", grids=3,
                       bg="纯白无缝", light="平光", ref=True,
                       use="服装资产（真源见 06）"),
    "pose":       dict(name="动作姿态集", ratio="16:9", grids=4,
                       bg="纯白或极浅灰", light="统一侧光", ref=True,
                       use="打戏、演出参考"),
    "kv":         dict(name="主视觉", ratio="9:16", grids=1,
                       bg="环境", light="戏剧光", ref=False,
                       use="封面、头图、预告首帧"),
    "chibi":      dict(name="Q 版", ratio="1:1", grids=1,
                       bg="纯色", light="平光", ref=True,
                       use="周边、表情包"),
    "lineup":     dict(name="阵容图", ratio="16:9", grids=0,
                       bg="设计化底色", light="统一主光", ref=False,
                       use="片头、群像介绍"),
}

LAYOUT_ALIAS = {
    "三视图": "three-view", "四视图": "four-view", "四格": "four-view",
    "四格板": "four-view", "立绘": "fullbody", "全身": "fullbody",
    "头像": "portrait", "半身": "portrait", "档案": "profile",
    "角色档案": "profile", "表情": "expression", "表情集": "expression",
    "服装": "outfit", "动作": "pose", "主图": "kv", "主视觉": "kv",
    "q版": "chibi", "Q版": "chibi", "阵容": "lineup",
}


# 镜头必需字段
SHOT_FIELDS = ("来源", "时长", "职责", "起点", "唯一动作", "终点")

# 视觉依据语法
RE_LOCK = re.compile(r"LOCK-([A-Za-z0-9\-]+)《([^》]+)》")
RE_SHOT_ID = re.compile(r"^##\s+(SHOT-[A-Za-z0-9]+-\d+)")
RE_SCENE_ID = re.compile(r"^##\s+(EP\d+-SC\d+)")
RE_ENTRY = re.compile(r"^##\s+(人物|造型|地点|道具)\s*·\s*(.+)$")
# 台词行：容忍三种主流写法。只认一种格式的后果很严重——
# 别人给的剧本会解析出 0 句台词，而 X1/X2/X3 在空集合上「全部通过」，机检变成假的。
RE_LINE = re.compile(
    r"^(?:\[(?:VO|OS|画外)\]\s*)?"
    r"(?P<who>[\u4e00-\u9fa5A-Za-z0-9·]{1,12})\s*[（(]\s*(?P<tone>[^）)]{0,30})\s*[）)]"
    r"\s*[：:]\s*(?P<text>.+)$")
RE_LINE_BARE = re.compile(
    r"^(?:\[(?:VO|OS|画外)\]\s*)?"
    r"(?P<who>[\u4e00-\u9fa5A-Za-z0-9·]{1,12})\s*[：:]\s*(?P<text>.+)$")
RE_LINE_BR = re.compile(
    r"^(?:\[(?:VO|OS|画外)\]\s*)?"
    r"【(?P<who>[^】]{1,12})】\s*[：:]?\s*(?P<text>.+)$")
LINE_BULLET = re.compile(r"^(?:[-*+]\s+|\d+[.)、]\s*)")
# 这些不是说话人，是听觉轨里的标注行
LINE_NONSPEAKER = ("音效", "画面", "注", "备注", "字幕", "音乐", "BGM", "配音说明",
                   "环境音", "旁白注", "说明")
# 有台词但不是「人物」的声源：不进人物账，也不参与已故角色检查
NON_PERSON_VOICE = ("系统", "旁白", "广播", "电视", "电话", "机械", "提示音",
                    "画外", "收音", "播报", "字幕", "群杂")
RE_IMG = re.compile(r"IMG-[A-Za-z0-9\-]+")


# ---------------------------------------------------------------- 工具

def match_line(raw):
    """解析一行台词 → (说话人, 语气, 台词) 或 None。容忍列表符/无语气位/半角/【名字】。"""
    t = (raw or "").strip()
    if not t:
        return None
    t = LINE_BULLET.sub("", t).strip()
    if not t:
        return None
    for rx in (RE_LINE, RE_LINE_BARE, RE_LINE_BR):
        m = rx.match(t)
        if not m:
            continue
        who = m.group("who").strip()
        if who in LINE_NONSPEAKER:
            return None
        tone = m.groupdict().get("tone") or ""
        return who, tone.strip(), m.group("text").strip()
    return None


def out(msg=""):
    sys.stdout.write(str(msg) + "\n")


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def cn_len(s):
    return len(re.sub(r"\s", "", s or ""))


def action_duration(text):
    for tag, (dur, keys) in ACTION_DUR.items():
        if keys and any(k in text for k in keys):
            return dur
    return ACTION_DUR["微动"][0]


def line_duration(text, cps=DEFAULT_CPS):
    """台词时长：字数/语速 + 句末留白 + 收口余量。"""
    chars = cn_len(text)
    if not chars:
        return SHOT_MIN
    return round(chars / cps + PAUSE + LINE_HEADROOM, 2)


def clamp(d):
    return round(max(SHOT_MIN, min(SHOT_MAX, d)), 2)


# ---------------------------------------------------------------- 解析

class Script:
    """剧本.md 解析结果。"""

    def __init__(self):
        self.episode = None      # EP001
        self.title = None
        self.scenes = []         # [{id, head, visual:[], audio:[]}]

    @property
    def lines(self):
        for sc in self.scenes:
            for ln in sc["audio"]:
                r = match_line(ln)
                if r:
                    yield sc["id"], r[0], r[1], r[2]


def parse_script(text):
    s = Script()
    cur = None
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^#\s+(EP\d+)\s*(.*)$", line)
        if m:
            s.episode, s.title = m.group(1), m.group(2).strip()
            continue
        m = RE_SCENE_ID.match(line)
        if m:
            head = line[2:].strip()
            # 张力标记写在标题里：## EP001-SC001 内 · 屋 · 夜（张力 7）
            tm = re.search(r"[（(]\s*张力\s*[:：]?\s*(\d{1,2})\s*[）)]", head)
            cur = {"id": m.group(1), "head": head, "visual": [], "audio": [],
                   "tension": int(tm.group(1)) if tm else None}
            s.scenes.append(cur)
            section = None
            continue
        # 非场次的一级标题（## 本集钩子 / ## 备注）之后不能再按轨解析，
        # 否则它下面的列表会被当成台词吞进去
        if line.startswith("## ") and not RE_SCENE_ID.match(line):
            section = None
            continue
        if line.startswith("### 画面轨"):
            section = "visual"
            continue
        if line.startswith("### 听觉轨"):
            section = "audio"
            continue
        if cur is not None and section and line.strip():
            # 听觉轨里没有列表符的行也要收——别把台词静默丢掉
            if line.startswith("- ") or line.startswith("* "):
                cur[section].append(line[2:].strip())
            elif section == "audio":
                cur[section].append(line.strip())
    return s


class Shot:
    def __init__(self, sid):
        self.id = sid
        self.fields = {}
        self.blocks = {}         # {小节名: [行]}
        self.section = None

    def get(self, k, default=""):
        return self.fields.get(k, default)


def parse_storyboard(text):
    shots = []
    cur = None
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = RE_SHOT_ID.match(line)
        if m:
            cur = Shot(m.group(1))
            shots.append(cur)
            section = None
            continue
        if line.startswith("### "):
            if cur is not None:
                section = line[4:].strip()
                cur.blocks.setdefault(section, [])
            continue
        if cur is None:
            continue
        if line.startswith("- ") and section is None:
            body = line[2:].strip()
            if "：" in body:
                k, v = body.split("：", 1)
                cur.fields[k.strip()] = v.strip()
        elif section:
            cur.blocks[section].append(line)
    return shots


class Bible:
    """视觉设定.md 解析结果。"""

    def __init__(self):
        self.entries = {}        # (类别, 名称) -> {字段: 值}
        self.locks = {}          # lock_id -> (锁面, 条目类别, 条目名)
        self.aliases = {}        # 条目名 -> 画面代称

    def has(self, kind, name):
        return (kind, name) in self.entries

    def names(self, kind=None):
        return [n for (k, n) in self.entries if kind is None or k == kind]


def parse_bible(text):
    b = Bible()
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = RE_ENTRY.match(line)
        if m:
            cur = (m.group(1), m.group(2).strip())
            b.entries[cur] = {}
            continue
        if line.startswith("## "):
            cur = None
            continue
        if cur is None:
            continue
        body = line[2:].strip() if line.startswith("- ") else ""
        if not body:
            continue
        if "：" in body:
            k, v = body.split("：", 1)
            k, v = k.strip(), v.strip()
            b.entries[cur].setdefault(k, v)
            if k == "画面代称":
                b.aliases[cur[1]] = v
        for lm in RE_LOCK.finditer(body):
            scope_raw = body
            sm = re.search(r"镜头：([^）]*)", scope_raw)
            scope = sm.group(1).strip() if sm else "入画"
            b.locks[lm.group(1)] = (lm.group(2).strip(), cur[0], cur[1], scope)
    return b


# ---------------------------------------------------------------- 检查

class Report:
    def __init__(self):
        self.items = []

    def add(self, group, code, ok, level, msg, where=""):
        if ok is None:           # INFO
            self.items.append((group, code, "INFO", msg, where))
        elif ok:
            self.items.append((group, code, "PASS", msg, where))
        else:
            self.items.append((group, code, level, msg, where))

    @property
    def failed(self):
        return [i for i in self.items if i[2] == "FAIL"]

    @property
    def warned(self):
        return [i for i in self.items if i[2] == "WARN"]

    def render(self, groups):
        icon = {"PASS": "✓", "WARN": "!", "FAIL": "✗", "INFO": "·"}
        for g in groups:
            rows = [i for i in self.items if i[0] == g]
            if not rows:
                continue
            out("")
            out("── %s 组 ──" % g)
            for _, code, status, msg, where in rows:
                if status == "PASS":
                    continue
                tail = "  ← %s" % where if where else ""
                out("  %s %-6s %s%s" % (icon.get(status, "?"), code, msg, tail))
            passed = sum(1 for i in rows if i[2] == "PASS")
            out("  （%d 项通过 / %d 项总计）" % (passed, len(rows)))


def load_project(root):
    root = Path(root)
    cfg = {}
    if not root.exists():
        raise SystemExit("路径不存在：%s\n先跑 init 建项目："
                         "python scripts/cd.py init %s --title 片名"
                         % (root, root))
    if not root.is_dir():
        raise SystemExit("不是目录：%s" % root)
    p = root / "short-drama.json"
    if p.exists():
        raw = read_text(p) or "{}"
        try:
            cfg = json.loads(raw)
        except json.JSONDecodeError as e:
            out("警告：short-drama.json 解析失败（%s），按空配置继续。" % e)
            cfg = {}
    return root, cfg


def find_episodes(root):
    base = root / "剧集"
    if not base.exists():
        return []
    return sorted([d for d in base.iterdir() if d.is_dir()])


def scan_asset_dirs(root):
    """找出项目里的资产文档（人物/场景/道具）。"""
    hits = []
    for d in root.iterdir() if root.exists() else []:
        if d.is_dir() and ("资产" in d.name):
            # 下划线开头是工作文件（建卡清单等），不是资产产物
            hits.extend(sorted(x for x in d.glob("*.md")
                               if not x.name.startswith("_")))
    return hits


def parse_ledger(text):
    """解析连续性台账的四张表。表头用关键词定位，列顺序按模板约定。"""
    led = {"foreshadow": [], "characters": [], "props": [], "rules": []}
    if not text:
        return led
    cur, head = None, None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("##"):
            low = line
            if "伏笔" in low:
                cur, head = "foreshadow", None
            elif "人物" in low:
                cur, head = "characters", None
            elif "道具" in low:
                cur, head = "props", None
            elif "规则" in low:
                cur, head = "rules", None
            else:
                cur, head = None, None
            continue
        if not cur or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if head is None:
            head = cells
            continue
        row = dict(zip(head, cells))
        # 跳过模板占位行与空行
        if any("〔" in c for c in cells) or not any(cells):
            continue
        led[cur].append(row)
    return led


def _ledger_path(root):
    return Path(root) / "连续性台账.md"


def _ep_no(name):
    m = re.search(r"(\d+)", name or "")
    return int(m.group(1)) if m else 0


def _int_of(s):
    m = re.search(r"\d+", str(s or ""))
    return int(m.group(0)) if m else 0


def build_alias(bible):
    """剧本说话人 → 视觉设定条目名。剧本写「长老」，条目叫「执法长老」，靠「画面代称」接。"""
    alias = {}
    for n in bible.names("人物"):
        alias[n] = n
        raw = (bible.entries.get(("人物", n), {}).get("画面代称", "") or "")
        for a in re.split(r"[、,，/|；;]", raw):
            a = a.strip()
            if a and a not in alias:
                alias[a] = n
    return alias


def check_ledger(root, rep, ep_dirs, bible=None):
    """L 组：叙事台账。台账管「那枚戒指现在在谁手里」，锁管「这一帧画里有没有它」。"""
    path = _ledger_path(root)
    max_ep = max([_ep_no(d.name) for d in ep_dirs] or [0])
    if not path.exists():
        if max_ep > 1:
            rep.add("L", "L1", False, "WARN", "多集项目有连续性台账",
                    "缺 连续性台账.md。跑 `cd.py ledger <项目> --init` 生成骨架，"
                    "或复制 assets/连续性台账模板.md")
        else:
            rep.add("L", "L1", None, "INFO", "单集项目，台账非必需")
        return

    led = parse_ledger(read_text(path))
    rep.add("L", "L1", True, "INFO", "连续性台账存在")

    bible = bible or parse_bible(read_text(root / "视觉设定.md"))
    alias = build_alias(bible)

    def norm(n):
        n = (n or "").strip()
        return alias.get(n, n)

    # L2 伏笔超期
    late = []
    for r in led["foreshadow"]:
        st = (r.get("状态") or "").strip()
        if st in ("收", "弃", ""):
            continue
        due = _int_of(r.get("拟收于"))
        if due and max_ep and max_ep > due + 3:
            late.append("%s（拟收 %d，已写到 %d）" % (r.get("ID") or "?", due, max_ep))
    rep.add("L", "L2", not late, "WARN", "伏笔没有超期未收（拟收 +3 集）",
            "；".join(late[:3]))

    # L3 已故角色后续集仍有台词
    dead = {}
    for r in led["characters"]:
        st = (r.get("当前状态") or "").strip()
        if st != "死亡":
            continue
        if "闪回" in (r.get("变动事件") or ""):
            continue
        dead[norm(r.get("角色"))] = _int_of(r.get("最后变动集"))
    talking = []
    if dead:
        for d in ep_dirs:
            no = _ep_no(d.name)
            script = parse_script(read_text(d / "剧本.md"))
            for sid, who, tone, text in script.lines:
                if any(k in who for k in NON_PERSON_VOICE):
                    continue
                w = norm(who)
                if w in dead and no > dead[w]:
                    talking.append("%s 第 %d 集仍有台词「%s」" % (who, no, text[:8]))
    rep.add("L", "L3", not talking, "FAIL", "已故角色不再有台词（回忆需在台账标「闪回」）",
            "；".join(talking[:3]))

    # L4 道具早于首次出现被提及
    early = []
    for r in led["props"]:
        name = (r.get("道具") or "").strip()
        first = _int_of(r.get("首次出现集"))
        if not name or not first or first <= 1:
            continue
        for d in ep_dirs:
            no = _ep_no(d.name)
            if no >= first:
                continue
            body = read_text(d / "剧本.md") + read_text(d / "分镜.md")
            if name in body:
                early.append("%s 第 %d 集被提及（首次 %d）" % (name, no, first))
    rep.add("L", "L4", not early, "WARN", "道具不早于首次出现集",
            "；".join(early[:3]))


def check_assets(root, rep):
    files = scan_asset_dirs(root)
    if not files:
        rep.add("A", "A0", None, "INFO", "未发现资产目录（人物资产/场景资产/道具资产）")
        return
    for f in files:
        txt = read_text(f)
        tag = f.name
        parent = f.parent.name
        is_char = ("人物" in parent or "角色" in parent)
        is_scene = ("场景" in parent or "地点" in parent)
        is_costume = ("服装" in parent or "造型" in parent or "服装" in f.name)
        is_weapon = ("武器" in parent or "武器" in f.name)
        # 单图主视觉（KV）和四格板是两种资产：前者要一张成图、可以有背景光效，
        # 后者要拆格、纯白背景。混在一起判，两边都会误报。
        is_kv = any(k in f.name for k in ("主图", "KV", "主视觉", "单图"))

        # 只扫代码块内的提示词正文——说明段与自检段不算
        blocks = re.findall(r"```(?:text)?\n(.*?)```", txt, re.S)
        body = "\n".join(blocks) if blocks else txt

        if is_kv:
            rep.add("A", "A13", ("单张成图" in body or "单图" in body), "FAIL",
                    "%s 声明了单张成图" % tag)
            multi_grid = [w for w in ("全图共 4 格", "全图共 9 格") if w in body]
            rep.add("A", "A14", not multi_grid, "FAIL",
                    "%s 主视觉不拆格" % tag, "、".join(multi_grid))

        if is_char and not is_kv:
            # 多格图必须声明格数；单图（立绘/头像/Q版）不要求。
            # 版式不再写死四格——三视图三格、表情集四格、档案图多区块，都合法。
            grid = re.search(r"全图共\s*(\d+)\s*格", body)
            multi = re.search(r"(三视图|四视图|多视图|设定稿|设定图|表情集|姿态集|拆解板|服装板)",
                              f.name + body)
            single = re.search(r"(单张成图|单图|单人全身立绘|Q 版单图)", body)
            need = bool(multi) and not single
            rep.add("A", "A1", (bool(grid) or not need), "FAIL",
                    "%s 多格图声明了格数（全图共 N 格）" % tag)
            if grid:
                n = int(grid.group(1))
                ok_cap = ("仅此" in body) or bool(
                    re.search(r"不出现第\s*%d\s*格" % (n + 1), body))
                rep.add("A", "A15", ok_cap, "WARN",
                        "%s 声明了格数上限（仅此 %d 格，不出现第 %d 格）" % (tag, n, n + 1))
            bad_head = [w for w in HEAD_CUT if w in body]
            rep.add("A", "A2", not bad_head, "FAIL", "%s 没有砍头写法" % tag,
                    "、".join(bad_head))
            need_full = any(k in body for k in ("全身", "立绘", "至鞋", "三视图", "四视图"))
            rep.add("A", "A4", (not need_full) or ("至鞋" in body or "含鞋" in body), "FAIL",
                    "%s 画全身时写了完整性（至鞋）" % tag)
            has_kit = sum(1 for k in ("标识物", "形制", "体态") if k in body) >= 2
            rep.add("A", "A5", has_kit, "WARN",
                    "%s 有职业标识物三件套" % tag)

        if is_scene:
            rep.add("A", "A6", "全图共 9 格" in body, "FAIL",
                    "%s 声明了「全图共 9 格」" % tag)

        if is_costume:
            # 披风/护甲/刺绣 是模型最爱自动补的三样，必须逐个声明「无」
            missing_parts = []
            for part, kind in (("披风", "结构"), ("护甲", "结构"), ("刺绣", "工艺")):
                if not re.search(part + r"[^\n]{0,12}无此" + kind, body):
                    missing_parts.append(part)
            rep.add("A", "A8", not missing_parts, "FAIL",
                    "%s 逐项声明了「无此结构/无此工艺」" % tag,
                    "；".join("未声明 %s" % x for x in missing_parts))
            has_back = bool(re.search(r"【[^】]*背面[^】]*】", body))
            rep.add("A", "A9", has_back, "FAIL",
                    "%s 有背面视图段" % tag)

        if is_weapon:
            has_len = ("厘米" in body) or ("至" in body and "齐" in body)
            rep.add("A", "A10", has_len, "FAIL", "%s 给了长度参照" % tag)
            has_hand = ("持用手" in body) or ("右手" in body) or ("左手" in body)
            rep.add("A", "A11", has_hand, "WARN", "%s 写了持用手" % tag)

        bad_mosaic = [w for w in MOSAIC if w in body]
        rep.add("A", "A3", not bad_mosaic, "FAIL", "%s 没有「马赛克」类字面词" % tag,
                "、".join(bad_mosaic))

        # 静态资产也要去水：写「粒子」只会得到一张发光噪点贴图，写「震撼」纯占字数
        wet = [w for w in VFX_BAN if w in body]
        rep.add("A", "A12", not wet, "WARN", "%s 静态设定稿无「粒子」与评价词" % tag,
                "、".join(wet[:4]))

        bad_ref = [w for w in SELF_REF if w in body]
        rep.add("A", "A7", not bad_ref, "WARN", "%s 自包含（无跨条引用）" % tag,
                "、".join(bad_ref))


# ---------------------------------------------------------------- Q 组常量

# Q1：竖屏里「无人物」的过渡镜是负资产（9:16 节奏堆得快，空镜=划走）
EMPTY_SHOT = ("空镜", "无人物入画", "无人物出场", "一个人都没有", "纯环境镜")
EMPTY_ALLOW = ("刻意空镜", "必要空镜", "刻意的空镜")

# Q2：群像行为缺失。聚合词出现却没给每人一件事 = 人形立牌
CROWD_WORD = ("众人", "大家", "围观", "在旁", "周围人群", "路人", "一群人",
              "学生们", "员工们", "宾客们", "群众")
CROWD_EXEMPT = ("四下无人", "无其他人物", "空无一人")

# Q3：已废除的硬约束残留。照抄会双杀（镜长雷同 + 该分的回合硬并）
OBSOLETE_RULES = (r"单镜\s*[3-6]\s*[~-]\s*[3-8]\s*秒",
                  r"一组\s*[34]\s*[~-]\s*[48]\s*镜")
OBSOLETE_CTX = ("约束", "限制", "规定", "预算", "上限", "不得超过",
                "必须", "须", "要求", "控制在")
OBSOLETE_PARDON = ("已废", "废止", "废弃", "不再", "旧版", "旧口径", "弃用",
                   "禁写", "不采用", "作废", "历史", "过时")


def _shot_text(sh):
    """拼一镜的全部正文，用于词根类判断。"""
    parts = [sh.get("起点", ""), sh.get("唯一动作", ""), sh.get("终点", ""),
             sh.get("景别", ""), sh.get("角度", ""), sh.get("运镜", ""),
             sh.get("声音", "")]
    for v in sh.blocks.values():
        parts.extend(v)
    return "".join(parts)


def check_q(root, cfg, rep, target_ep=None):
    """Q 组：条件触发的稿面检查。

    与 X 组的区别：X 组每镜必查，Q 组先看「条件门」开不开——
    条件不满足就整条不查，避免把不适用的规则硬套上去。
    """
    spec = cfg.get("spec", {}) or {}
    ar = str(spec.get("aspect_ratio", ""))
    eps = find_episodes(root)

    q1_bad, q2_bad, q3_bad = [], [], []
    q1_on = (ar == "9:16")          # 只有竖屏才查空镜；16:9 / 21:9 永不触发

    for epdir in eps:
        if target_ep and epdir.name != target_ep:
            continue
        raw = read_text(epdir / "分镜.md")
        shots = parse_storyboard(raw)
        for sh in shots:
            body = _shot_text(sh)

            # ---- Q1 竖屏空镜冗余 ----
            if q1_on:
                if any(k in body for k in EMPTY_SHOT) and not any(k in body for k in EMPTY_ALLOW):
                    q1_bad.append(sh.id)

            # ---- Q2 群像行为缺失 ----
            # 关门条件：打戏段 / 纯特写 / 密闭双人 / 声明无人 → 一条都不查
            gate_closed = (any(k in body for k in CROWD_EXEMPT)
                           or "打" in str(sh.get("职责", ""))[:6]
                           or sh.get("景别", "") in ("特写", "大特写", "微距"))
            if not gate_closed:
                chars = sh.get("characters") or []
                has_crowd_word = any(k in body for k in CROWD_WORD)
                has_task = "事务" in body
                # 同框三人以上，或用了聚合词：必须要么给事务，要么显式声明无人
                if (len(chars) >= 3 or has_crowd_word) and not has_task:
                    if not any(k in body for k in CROWD_EXEMPT):
                        q2_bad.append("%s 群像未写「事务」" % sh.id)

        # ---- Q3 已废除硬约束残留（整稿扫，带追述豁免）----
        for m in re.finditer(r"(" + "|".join(OBSOLETE_RULES) + ")", raw):
            lo = max(0, m.start() - 20)
            ctx = raw[lo:m.end() + 20]
            if any(k in ctx for k in OBSOLETE_PARDON):
                continue
            if any(k in ctx for k in OBSOLETE_CTX):
                q3_bad.append("%s「%s」" % (epdir.name, m.group(1)))

    if q1_on:
        rep.add("Q", "Q1", not q1_bad, "WARN",
                "竖屏(9:16) 无未标记的过渡空镜",
                "；".join(q1_bad[:4]) + ("（标「刻意空镜」可放行）" if q1_bad else ""))
    else:
        rep.add("Q", "Q1", True, "INFO",
                "画幅 %s 不查空镜（16:9/21:9 需要意境镜）" % (ar or "未定"))

    rep.add("Q", "Q2", not q2_bad, "WARN",
            "群像镜给了「事务」或声明无人", "；".join(q2_bad[:4]))
    rep.add("Q", "Q3", not q3_bad, "WARN",
            "没有照抄已废除的镜长/镜数硬约束", "；".join(q3_bad[:4]))


def check_project(root, only=None, target_ep=None):
    root, cfg = load_project(root)
    rep = Report()
    groups = only or list("SRXCAMQL")

    # ---- S 结构 ----
    if "S" in groups:
        rep.add("S", "S1", bool(cfg), "FAIL", "short-drama.json 存在")
        eps = find_episodes(root)
        rep.add("S", "S2", bool(eps), "FAIL", "剧集目录存在", str(root / "剧集"))

        for epdir in eps:
            if target_ep and epdir.name != target_ep:
                continue
            sp = epdir / "剧本.md"
            bp = epdir / "分镜.md"
            script = parse_script(read_text(sp))
            shots = parse_storyboard(read_text(bp))
            tag = epdir.name

            if script.scenes:
                rep.add("S", "S3", len({s["id"] for s in script.scenes}) == len(script.scenes),
                        "FAIL", "%s 场次 ID 唯一" % tag)
                empty = [s["id"] for s in script.scenes if not s["visual"]]
                rep.add("S", "S4", not empty, "FAIL",
                        "%s 每场有画面轨" % tag, "、".join(empty))

                # 台词解析覆盖率：听觉轨里有冒号的行，有多少真被认成台词。
                # 这一条防的是「格式不认 → 0 句台词 → X1/X2/X3 在空集合上全过」的假绿。
                declared, lost = 0, []
                for s in script.scenes:
                    for ln in s["audio"]:
                        if not re.search(r"[：:]", ln):
                            continue
                        head = re.split(r"[：:]", LINE_BULLET.sub("", ln).strip())[0].strip()
                        if head in LINE_NONSPEAKER:      # 音效/画面 这类标注行不算漏
                            continue
                        declared += 1
                        if match_line(ln) is None:
                            lost.append(ln[:18])
                if declared == 0:
                    rep.add("S", "S11", None, "INFO",
                            "%s 剧本没有台词行（或听觉轨为空）" % tag)
                else:
                    rep.add("S", "S11", not lost, "WARN",
                            "%s 台词行全部解析成功（%d 句）" % (tag, declared),
                            "有 %d 行没认成台词：%s —— 台词写成 `- 名字（语气）：台词`"
                            % (len(lost), "；".join(lost[:3])))
            else:
                rep.add("S", "S12", False, "FAIL",
                        "%s 剧本里有场次" % tag,
                        "0 场。场次标题写法：`## EP001-SC001 内 · 地点 · 时间`")
            # 兜底：分镜为空时下面是逐镜检查，一条都不会跑，会显示全过
            rep.add("S", "S0", bool(shots), "FAIL",
                    "%s 分镜里至少有一镜" % tag,
                    "0 镜。写分镜：复制 assets/分镜模板.md，"
                    "镜头行以「## SHOT-<集号>-001」开头")
            if shots:
                ids = [x.id for x in shots]
                rep.add("S", "S5", len(set(ids)) == len(ids), "FAIL", "%s 镜头 ID 唯一" % tag)

                missing = []
                for sh in shots:
                    lack = [f for f in SHOT_FIELDS if not sh.get(f)]
                    if lack:
                        missing.append("%s 缺 %s" % (sh.id, "/".join(lack)))
                rep.add("S", "S6", not missing, "FAIL", "%s 镜头必需字段齐全" % tag,
                        "；".join(missing[:3]))

                scene_ids = {s["id"] for s in script.scenes}
                bad_src, bad_dur = [], []
                spec0 = cfg.get("spec", {})
                _ms = model_spec(spec0.get("target_model"))
                _cap = float(min(SHOT_MAX, _ms[0])) if _ms else SHOT_MAX
                _floor = tune(cfg, "shot_min", SHOT_MIN)
                for sh in shots:
                    src = re.match(r"(EP\d+-SC\d+)", sh.get("来源"))
                    if scene_ids and (not src or src.group(1) not in scene_ids):
                        bad_src.append(sh.id)
                    try:
                        d = float(re.sub(r"[^\d.]", "", sh.get("时长")) or 0)
                    except ValueError:
                        d = 0
                    if not (_floor <= d <= _cap):
                        bad_dur.append("%s=%.1fs" % (sh.id, d))
                rep.add("S", "S7", not bad_src, "FAIL", "%s 镜头来源指向真实场次" % tag,
                        "、".join(bad_src[:4]))
                rep.add("S", "S8", not bad_dur, "FAIL",
                        "%s 单镜 %.1f–%.1f 秒（%s 档 × 模型上限）"
                        % (tag, _floor, _cap, spec_ar(cfg)),
                        "、".join(bad_dur[:4]))

                total = sum(float(re.sub(r"[^\d.]", "", x.get("时长")) or 0) for x in shots)
                spec = cfg.get("spec", {})
                per_ep = spec.get("episode_targets") or {}
                tgt = per_ep.get(tag) or spec.get("episode_duration_sec")
                if tgt:
                    diff = abs(total - tgt) / float(tgt)
                    rep.add("S", "S9", diff <= TOLERANCE, "WARN",
                            "%s 总时长 %.1fs vs 目标 %ss（偏差 %.0f%%）"
                            % (tag, total, tgt, diff * 100))

    # ---- R 引用 ----
    if "R" in groups:
        bible = parse_bible(read_text(root / "视觉设定.md"))
        rep.add("R", "R0", bool(bible.entries), "WARN", "视觉设定有条目",
                str(root / "视觉设定.md"))

        for epdir in find_episodes(root):
            if target_ep and epdir.name != target_ep:
                continue
            tag = epdir.name
            shots = parse_storyboard(read_text(epdir / "分镜.md"))
            if not shots:
                continue

            bad_ref, bad_lock, bad_slot, bad_img = [], [], [], []
            seen_lock = {}
            for sh in shots:
                for vm in re.finditer(r"(人物|造型|地点|道具)「([^」]+)」", sh.get("视觉依据")):
                    if bible.entries and not bible.has(vm.group(1), vm.group(2)):
                        bad_ref.append("%s→%s「%s」" % (sh.id, vm.group(1), vm.group(2)))

                # 锁面核对
                # 1) 锁声明了具体镜号 → 这些镜头必须逐字带锁面
                # 2) 锁声明「入画/全集」→ 涉及该条目的每镜都应带锁面
                text_all = sh.get("起点", "") + sh.get("唯一动作", "") + sh.get("终点", "")
                for blk in sh.blocks.values():
                    text_all += "".join(blk)
                vref = sh.get("视觉依据", "")
                for lid, (surface, kind, name, scope) in bible.locks.items():
                    if not surface:
                        continue
                    if scope in ("入画", "全集"):
                        if ("%s「%s」" % (kind, name)) in vref:
                            seen_lock.setdefault(lid, []).append((sh.id, surface in text_all))
                    elif sh.id in scope:
                        if surface not in text_all:
                            bad_lock.append("%s 缺锁面「%s」" % (sh.id, surface))

                refs = sh.get("输入参考图", "无")
                if "REF-" in refs or "PLAN-" in refs:
                    if "用途：" not in refs:
                        bad_slot.append("%s 槽位缺「用途」" % sh.id)
                img = sh.get("图片提示词项", "")
                if img and img != "无" and not RE_IMG.search(img):
                    bad_img.append("%s 图片提示词项格式错误" % sh.id)

            # 「入画/全集」的锁：涉及该条目的每一镜都该带锁面
            for lid, rows in seen_lock.items():
                missing = [i for i, ok in rows if not ok]
                if missing:
                    bad_lock.append("、".join(missing[:3]) + " 未带锁面「%s」"
                                    % bible.locks[lid][0])

            rep.add("R", "R1", not bad_ref, "FAIL", "%s 视觉依据指向真实条目" % tag,
                    "；".join(bad_ref[:3]))
            rep.add("R", "R2", not bad_lock, "WARN", "%s 锁面出现在镜头正文里" % tag,
                    "；".join(bad_lock[:3]))
            rep.add("R", "R3", not bad_slot, "FAIL", "%s 参考槽位格式完整" % tag,
                    "；".join(bad_slot[:3]))
            rep.add("R", "R4", not bad_img, "WARN", "%s 图片提示词项格式正确" % tag,
                    "；".join(bad_img[:3]))

        # 图号唯一性：重复会让素材接线单失效
        seen_no = {}
        dup = []
        for (kind, name), fields in bible.entries.items():
            if kind == "造型":
                continue
            m = re.search(r"(\d+)", fields.get("资产编号", ""))
            if not m:
                continue
            no = int(m.group(1))
            if no in seen_no:
                dup.append("图%d 被「%s」与「%s」重复占用" % (no, seen_no[no], name))
            seen_no[no] = name
        rep.add("R", "R6", not dup, "FAIL", "资产编号唯一", "；".join(dup[:3]))

    # ---- X 执行 ----
    if "X" in groups:
        for epdir in find_episodes(root):
            if target_ep and epdir.name != target_ep:
                continue
            tag = epdir.name
            script = parse_script(read_text(epdir / "剧本.md"))
            shots = parse_storyboard(read_text(epdir / "分镜.md"))

            line_max = tune(cfg, "line_max", LINE_MAX_CHARS)
            long_lines, no_tone = [], []
            for sid, who, tone, text in script.lines:
                if cn_len(text) > line_max:
                    long_lines.append("%s %s（%d字）" % (sid, who, cn_len(text)))
                if not tone.strip():
                    no_tone.append("%s %s" % (sid, who))
            rep.add("X", "X1", not long_lines, "FAIL",
                    "%s 单句台词 ≤%d 字（%s 档）"
                    % (tag, line_max, spec_ar(cfg)), "；".join(long_lines[:3]))
            rep.add("X", "X2", not no_tone, "WARN", "%s 台词有语气位" % tag,
                    "；".join(no_tone[:3]))

            if shots:
                tight, dirty, multi, no_block, no_atmo, no_anchor = [], [], [], [], [], []
                for sh in shots:
                    d = float(re.sub(r"[^\d.]", "", sh.get("时长")) or 0)
                    body = sh.get("起点", "") + sh.get("唯一动作", "") + sh.get("终点", "")

                    # 台词时长与镜长核对：台词在「声音」字段里
                    vm = re.search(r"）：(.+?)(?:\s*\[|$)", sh.get("声音", ""))
                    if vm:
                        need = line_duration(vm.group(1))
                        # 镜长按 0.5 秒粒度取值，留 0.2 秒容差避免舍入误报
                        if need > d + 0.2:
                            tight.append("%s 需%.1fs 仅%.1fs" % (sh.id, need, d))

                    hits = [w for w in NEGATION + METAPHOR + PSYCH + ABSTRACT if w in body]
                    if hits:
                        dirty.append("%s[%s]" % (sh.id, ",".join(hits[:2])))

                    act = sh.get("唯一动作", "")
                    if len(re.findall(r"[，,；;]", act)) >= 3:
                        multi.append(sh.id)

                    if not sh.get("来源"):
                        no_block.append(sh.id)

                    # 只认「关键帧提示词」那一节——别的小节有内容不算数
                    kp = ""
                    for name, blk in sh.blocks.items():
                        if "关键帧" in name or "提示词" in name:
                            kp = "".join(blk).strip()
                            break
                    if not kp:
                        no_anchor.append(sh.id)
                    else:
                        has_light = any(w in kp for w in ("光", "灯", "窗", "亮"))
                        has_air = any(w in kp for w in ("尘", "烟", "雾", "汽", "雨", "雪"))
                        has_fg = any(w in kp for w in ("前景", "虚焦", "景深", "遮挡"))
                        if sum([has_light, has_air, has_fg]) < 1:
                            no_atmo.append(sh.id)

                rep.add("X", "X3", not tight, "FAIL", "%s 台词镜有余量 ≥%.1fs" % (tag, LINE_HEADROOM),
                        "、".join(tight[:4]))
                rep.add("X", "X4", not dirty, "WARN", "%s 无词根污染" % tag,
                        "；".join(dirty[:3]))
                rep.add("X", "X5", not multi, "WARN", "%s 一镜一动作" % tag,
                        "、".join(multi[:4]))
                rep.add("X", "X6", not no_anchor, "WARN", "%s 每镜有关键帧提示词" % tag,
                        "、".join(no_anchor[:4]))
                rep.add("X", "X7", not no_atmo, "WARN",
                        "%s 关键帧有氛围层（特写只需光，全景要光/介质/前景之一）" % tag,
                        "、".join(no_atmo[:4]))

                # 特效去水：视频提示词里不许出现「粒子」与评价词
                vp = read_text(epdir / "视频提示词.md")
                if vp:
                    # 只看代码块内的可投喂正文，说明文字不算
                    body_blocks = re.findall(r"```(?:text)?\n(.*?)```", vp, re.S)
                    vp_body = "\n".join(body_blocks) if body_blocks else vp
                    wet = [w for w in VFX_BAN if w in vp_body]
                    rep.add("X", "X8", not wet, "WARN",
                            "%s 投喂稿没有「粒子」与评价词" % tag, "、".join(wet[:4]))

                # 图片提示词同样去水：静图不能靠速度差，只能靠「过程停在中间态」
                ip = read_text(epdir / "图片提示词.md")
                ip_blocks = re.findall(r"```(?:text)?\n(.*?)```", ip, re.S)
                if ip_blocks:
                    wet_i = [w for w in VFX_BAN if w in "\n".join(ip_blocks)]
                    rep.add("X", "X9", not wet_i, "WARN",
                            "%s 图片提示词没有「粒子」与评价词" % tag, "、".join(wet_i[:4]))

    # ---- L 台账 ----
    if "L" in groups:
        check_ledger(root, rep, find_episodes(root),
                     parse_bible(read_text(root / "视觉设定.md")))

    # ---- A 资产 ----
    if "A" in groups:
        check_assets(root, rep)

    # ---- C 合规 ----
    if "C" in groups:
        comp = cfg.get("compliance", {})
        rep.add("C", "C1", bool(comp.get("ai_label")), "FAIL", "AI 生成标识已确认")
        rep.add("C", "C2", bool(comp.get("filing_tier")), "FAIL", "备案档位已确认")
        redline = comp.get("redline_ok")
        rep.add("C", "C3", redline is True, "FAIL", "题材红线自检已勾选")
        spec = cfg.get("spec", {})
        rep.add("C", "C4", bool(spec.get("aspect_ratio")), "FAIL", "画幅已锁定")
        rep.add("C", "C5", bool(spec.get("target_model")), "FAIL", "目标视频模型已锁定")
        rep.add("C", "C6", bool(spec.get("form")), "FAIL", "制作形态已锁定")

    # ---- Q 条件触发 ----
    if "Q" in groups:
        check_q(root, cfg, rep, target_ep)

    # ---- M 模型适配 ----
    if "M" in groups:
        spec = cfg.get("spec", {})
        name = spec.get("target_model")
        ms = model_spec(name)

        # M1 模型已登记且在服役
        rep.add("M", "M1", ms is not None, "FAIL",
                "目标模型已登记（%s）" % (name or "未填"),
                "" if ms else "未在 MODEL_CAPS 中，参考 references/22-model-matrix.md")
        if ms and not ms[2]:
            rep.add("M", "M1b", False, "FAIL",
                    "目标模型仍在服役（%s）" % name,
                    "该模型已停服，须迁移；见 22-model-matrix.md 第五节")

        # M2 duration_cap_sec 与模型规格一致
        if ms:
            declared = spec.get("duration_cap_sec")
            if declared:
                rep.add("M", "M2", abs(float(declared) - ms[0]) <= 0.5, "WARN",
                        "duration_cap_sec=%s，目标模型上限 %ss" % (declared, ms[0]),
                        "两者不符，改一处会漏拦超长镜")
            else:
                rep.add("M", "M2", False, "WARN",
                        "未填 duration_cap_sec",
                        "按目标模型应为 %ss，填上才能拦住超长镜" % ms[0])
            cap_used = ms[0]

            # M3 参考图数量不超模型上限
            eps = find_episodes(root)
            over = []
            for epdir in eps:
                if target_ep and epdir.name != target_ep:
                    continue
                for sh in parse_storyboard(read_text(epdir / "分镜.md")):
                    refs = str(sh.get("输入参考图") or "")
                    n = len([x for x in re.split(r"[、，,；;]", refs)
                             if x.strip() and x.strip() not in ("无", "—")])
                    if n > ms[1]:
                        over.append("%s 用了 %d 个参考（上限 %d）"
                                    % (sh.id, n, ms[1]))
            rep.add("M", "M3", not over, "FAIL",
                    "参考图数量不超模型上限（%d）" % ms[1], "；".join(over[:4]))

            # M4 单镜时长不超单段上限
            too_long = []
            for epdir in eps:
                if target_ep and epdir.name != target_ep:
                    continue
                for sh in parse_storyboard(read_text(epdir / "分镜.md")):
                    d = float(re.sub(r"[^\d.]", "", sh.get("时长")) or 0)
                    if d > cap_used:
                        too_long.append("%s=%.1fs>%ss" % (sh.id, d, cap_used))
            rep.add("M", "M4", not too_long, "FAIL",
                    "单镜不超模型单段上限（%ss）" % cap_used, "；".join(too_long[:4]))

    return rep


# ---------------------------------------------------------------- selftest

ST_CFG = {
    "title": "自测项目", "spec": {
        "form": "国漫二次元", "aspect_ratio": "9:16",
        "target_model": "seedance-2.5", "duration_cap_sec": 30,
        "episode_duration_sec": 4,
    },
    "compliance": {"ai_label": True, "filing_tier": "其他", "redline_ok": True},
}

ST_BIBLE = """# 视觉设定 · 自测

## 人物 · 甲
- 资产编号：图1
- 识别锚点：30岁东亚女性，鹅蛋脸，左眉尾一道浅疤，身形偏瘦。
- 本集造型：见「造型 · 甲-常服」

## 造型 · 甲-常服
- 身份：甲
- 适用：全剧
- 锁定：灰衬衫，黑长裤，布鞋。

## 地点 · 屋
- 资产编号：图2
- 空间锚点：木门朝南，窗在东墙，地面水泥。
- 连续性锁：LOCK-DOOR《裂缝》（镜头：SHOT-EP001-001）
"""

ST_SCRIPT = """# EP001 自测

## EP001-SC001 内 · 屋 · 夜

### 画面轨
- 甲坐在木桌边，桌上有一盏台灯。
- 门板上有一道裂缝。

### 听觉轨
- 甲（很轻）：走吧。
"""

ST_BOARD = """# EP001 分镜

## SHOT-EP001-001 · 起身
- 来源：EP001-SC001
- 时长：3.5s
- 职责：给她一个离开的理由。
- 景别：中景
- 角度：斜侧（四分之三）
- 机位高度：平视
- 运镜：固定
- 起点：甲坐在木桌边，手搭在桌沿。
- 唯一动作：她撑桌站起，转身朝门。
- 终点：她背对镜头，站在门板前。
- 声音：甲（很轻）：走吧。
- 视觉依据：《视觉设定.md》·人物「甲」（控制：身份、面部）；地点「屋」（控制：门板裂缝）
- 输入参考图：PLAN-SHOT-START（顺序：1）《冻结关键帧》（用途：起始帧；控制：构图）

### 冻结关键帧提示词
> 国漫二次元。竖屏 9:16 中景，斜侧四分之三，平视。
> 画面是水泥地面的屋内，东墙一扇窗，暖黄台灯从右后方斜切过来，光柱里有细尘浮动。
> 甲坐木桌边，手搭桌沿，门板上一道裂缝清晰可辨。
> 前景一小片虚焦的桌角。
> 排除：不出现文字。
"""

ST_CHAR = """# 甲 · 四格板

## 提示词
```text
角色设定图，30岁 女性 【身份】（甲），全图共 4 格。
【头身比】成年身材约 6.5 头身。
【职业标识物】硬标识：布店伙计的蓝布围裙；形制：粗布短打，宽袖；体态：常年站立使肩背微驼。
【锚点·逐字复用】30岁东亚女性，鹅蛋脸，左眉尾一道浅疤，身形偏瘦。
【服装】灰衬衫，黑长裤，布鞋。
【版式】第 1 格：面部四分之三侧特写。第 2~4 格：无脸全身三视图（正面 / 侧面 / 背面），
头顶至鞋完整入画（含鞋袜，不裁头、不裁脚）。
【背景】纯白无缝背景。
【图面纪律】画面为纯图像，无任何文字。仅此 4 格，不出现第 5 格。
```

【无此结构声明】
- 披风：无此结构
- 护甲：无此结构
- 刺绣：无此工艺

【正面视图】
完整正面。

【侧面视图】
标准侧面。

【背面视图】
完整背面。
"""

ST_COSTUME = """# 甲-常服 · 服装板

```text
横向 Costume Sheet，纯白背景，均匀柔和影棚光。
正面、标准侧面、背面三个等高全身视图，脚底对齐同一基线。

【服装八字段】
① 整体类型：棉麻衬衫 + 直筒长裤，无外套
② 颜色体系：主色浅灰，辅色黑，鞋面黑
③ 面料材质：棉麻混纺，哑光，略有身骨
④ 纹样图案：素面无纹
⑤ 结构细节：正面对襟，五粒布扣，袖口卷起
⑥ 服装状态：两处补丁，裤脚磨白
⑦ 鞋袜：黑布面布鞋，白底，无袜
⑧ 专属配饰：无

【无此结构声明】
- 披风：无此结构
- 护甲：无此结构
- 刺绣：无此工艺

【正面视图】
完整展示头顶至鞋底，服装中心线垂直。

【侧面视图】
标准侧视，呈现衣料厚度与前后落差。

【背面视图】
完整展示后领、背部接缝、裤脚与鞋跟。
```
"""

ST_WEAPON = """# 刀 · 武器板

```text
纯白背景，武器设定板，全图共 7 格。
【形制】全长约 90 厘米；立起时刃尖到成年女性下巴，柄底齐腰。
单刃，刃筋朝背侧；有血槽。护手为铁制圆盘；柄部长 18 厘米，可单手握持。
重心在护手前两指处。持用手：右手。
【材质】刃部：哑光钢灰，锻造纹理可见。柄部：深褐木，浅色包浆。
【状态】入鞘；刃口一处米粒大缺口。
禁止：人物、场景、文字水印。
```
"""

ST_SCENE = """# 屋 · 九宫格

```text
场景九宫格，全图共 9 格，同一空间的九个视角。
1 正面全景　2 左斜 45°　3 右斜 45°
4 低机位　5 高机位　6 门口视角
7 窗外视角　8 细节：门板裂缝　9 细节：桌面
无人物，无动物，无文字。
```
"""


def st_build(root):
    """建一个最小合规项目，供各 case 在其副本上注入错误。"""
    root = Path(root)
    (root / "剧集" / "EP001").mkdir(parents=True, exist_ok=True)
    (root / "人物资产").mkdir(exist_ok=True)
    (root / "场景资产").mkdir(exist_ok=True)
    (root / "服装资产").mkdir(exist_ok=True)
    (root / "武器资产").mkdir(exist_ok=True)
    (root / "short-drama.json").write_text(
        json.dumps(ST_CFG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "视觉设定.md").write_text(ST_BIBLE, encoding="utf-8")
    (root / "剧集" / "EP001" / "剧本.md").write_text(ST_SCRIPT, encoding="utf-8")
    (root / "剧集" / "EP001" / "分镜.md").write_text(ST_BOARD, encoding="utf-8")
    (root / "剧集" / "EP001" / "图片提示词.md").write_text(
        "# 图片提示词\n\n```text\n国漫二次元，中景，人物持刀立于门前，\n"
        "右后上方侧逆光，地面尘土被风带起，前景虚焦一道门框。\n```\n", encoding="utf-8")
    (root / "人物资产" / "甲.md").write_text(ST_CHAR, encoding="utf-8")
    (root / "人物资产" / "甲-主图.md").write_text(
        "# 甲 · 单图主视觉\n\n```text\n3D 国风，单张成图，竖构图半身，人物偏左三分线，\n"
        "侧逆光自右后上方 45°，光比 1:6，前景一道虚焦门框。\n```\n", encoding="utf-8")
    (root / "场景资产" / "屋.md").write_text(ST_SCENE, encoding="utf-8")
    (root / "服装资产" / "甲-常服.md").write_text(ST_COSTUME, encoding="utf-8")
    (root / "武器资产" / "刀.md").write_text(ST_WEAPON, encoding="utf-8")
    return root


def _edit(path, old, new):
    t = read_text(path)
    assert old in t, "样本里找不到：%s" % old[:30]
    path.write_text(t.replace(old, new, 1), encoding="utf-8")


def _cfg(path, fn):
    d = json.loads(read_text(path))
    fn(d)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def st_cases():
    """(码, 组, 说明, 注入函数)。注入后该码应报 FAIL 或 WARN。"""

    def c_s0(r):   # 分镜里一镜都没有
        import re as _re
        p = r / "剧集" / "EP001" / "分镜.md"
        t = read_text(p)
        head = t[:t.index("## SHOT-")]
        p.write_text(head, encoding="utf-8")

    def c_s3(r):   # 场次 ID 重复
        p = r / "剧集" / "EP001" / "剧本.md"
        p.write_text(read_text(p) + "\n## EP001-SC001 内 · 屋 · 夜\n\n### 画面轨\n- 重复场次。\n",
                     encoding="utf-8")

    def c_s6(r):   # 缺职责
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 职责：给她一个离开的理由。\n", "")

    def c_s8(r):   # 镜长超模型上限
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 时长：3.5s", "- 时长：40s")

    def c_x1(r):   # 台词超长
        _edit(r / "剧集" / "EP001" / "剧本.md", "甲（很轻）：走吧。",
              "甲（很轻）：这是我们沈家最后剩下来的全部东西了你得明白。")

    def c_x3(r):   # 台词塞不进镜长
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 时长：3.5s", "- 时长：2s")
        _edit(r / "剧集" / "EP001" / "分镜.md", "甲（很轻）：走吧。",
              "甲（很轻）：这是我们沈家最后剩下来的全部东西了你得明白。")

    def c_x4(r):   # 词根污染
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 唯一动作：她撑桌站起，转身朝门。",
              "- 唯一动作：她撑桌站起，眼里没有一丝犹豫，仿佛在告别过去。")

    def c_r1(r):   # 引用不存在的人物
        _edit(r / "剧集" / "EP001" / "分镜.md", "·人物「甲」（控制：身份、面部）",
              "·人物「乙」（控制：身份、面部）")

    def c_r2(r):   # 锁面被改
        _edit(r / "视觉设定.md", "LOCK-DOOR《裂缝》", "LOCK-DOOR《裂痕》")

    def c_a1(r):   # 删四格声明
        _edit(r / "人物资产" / "甲.md", "全图共 4 格", "四视图")

    def c_a2(r):   # 砍头写法
        _edit(r / "人物资产" / "甲.md", "头顶至鞋完整入画（含鞋袜，不裁头、不裁脚）",
              "headless figure，头部不入画")

    def c_a8(r):   # 未声明无此结构
        _edit(r / "服装资产" / "甲-常服.md", "- 披风：无此结构", "- 披风：加一件短披风")

    def c_a6(r):   # 删九格声明
        _edit(r / "场景资产" / "屋.md", "全图共 9 格", "九个视角")

    def c_c1(r):   # AI 标识缺失
        _cfg(r / "short-drama.json", lambda d: d["compliance"].update({"ai_label": False}))

    def c_m1b(r):  # 停服模型
        _cfg(r / "short-drama.json", lambda d: d["spec"].update({"target_model": "sora-2"}))

    def c_m2(r):   # cap 与模型不符
        _cfg(r / "short-drama.json", lambda d: d["spec"].update({"duration_cap_sec": 8}))

    def c_q1(r):   # 竖屏空镜
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 唯一动作：她撑桌站起，转身朝门。",
              "- 唯一动作：空镜，无人物入画，只拍门板。")

    def c_q2(r):   # 群像无事务
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 唯一动作：她撑桌站起，转身朝门。",
              "- 唯一动作：众人站在墙边，一齐看过来。")

    def c_q3(r):   # 旧口径残留
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 职责：给她一个离开的理由。",
              "- 职责：给她一个离开的理由。本段必须遵守「单镜 3~5 秒」的规定。")

    def c_s5(r):   # 镜头 ID 重复
        p = r / "剧集" / "EP001" / "分镜.md"
        t = read_text(p)
        p.write_text(t + "\n## SHOT-EP001-001 · 重复镜\n- 来源：EP001-SC001\n- 时长：3s\n"
                     "- 职责：重复。\n- 起点：a\n- 唯一动作：b\n- 终点：c\n", encoding="utf-8")

    def c_s7(r):   # 来源指向不存在场次
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 来源：EP001-SC001", "- 来源：EP001-SC009")

    def c_x2(r):   # 台词无语气位
        _edit(r / "剧集" / "EP001" / "剧本.md", "甲（很轻）：走吧。", "甲（）：走吧。")

    def c_x5(r):   # 一镜多动作
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 唯一动作：她撑桌站起，转身朝门。",
              "- 唯一动作：她撑桌站起，转身朝门，抬手推门，回头看，随即低头、快步离开。")

    def c_x6(r):   # 删关键帧提示词
        _edit(r / "剧集" / "EP001" / "分镜.md",
              "### 冻结关键帧提示词\n> 国漫二次元。", "### 备注\n")

    def c_x7(r):   # 关键帧无氛围层
        p = r / "剧集" / "EP001" / "分镜.md"
        t = read_text(p)
        i = t.index("### 冻结关键帧提示词")
        p.write_text(t[:i] + "### 冻结关键帧提示词\n> 一个人站着。\n", encoding="utf-8")

    def c_x9(r):   # 图片提示词写了「粒子」与评价词
        p = r / "剧集" / "EP001" / "图片提示词.md"
        p.write_text(read_text(p) + "\n```text\n金色粒子特效，顶级震撼的电影级画面。\n```\n",
                     encoding="utf-8")

    def c_a12(r):  # 静态设定稿写了「粒子」
        p = r / "人物资产" / "甲.md"
        p.write_text(read_text(p) + "\n```text\n周身环绕蓝色发光粒子。\n```\n",
                     encoding="utf-8")

    LED_HEAD = ("## ① 伏笔账\n\n| ID | 伏笔内容 | 埋于 | 拟收于 | 状态 | 收法 / 备注 |\n"
                "|---|---|---:|---:|---|---|\n%s\n\n"
                "## ② 人物账\n\n| 角色 | 首次出场 | 当前状态 | 与主角关系现值 | 最后变动集 | 变动事件 |\n"
                "|---|---:|---|---|---:|---|\n%s\n\n"
                "## ③ 道具状态账\n\n| 道具 | 首次出现集 | 持有者 | 当前状态 | 变动集 |\n"
                "|---|---:|---|---|---:|\n%s\n\n"
                "## ④ 世界观规则账\n\n| 规则 | 类别 | 确立集 | 引用集 | 是否被违反 |\n"
                "|---|---|---:|---|---|\n")

    def _mk_eps(r, n):
        import shutil
        for i in range(2, n + 1):
            d = r / "剧集" / ("EP%03d" % i)
            if not d.exists():
                shutil.copytree(r / "剧集" / "EP001", d)
                for f in d.glob("*.*"):
                    f.write_text(read_text(f).replace("EP001", "EP%03d" % i), encoding="utf-8")

    def c_l1(r):   # 多集项目没有台账
        _mk_eps(r, 2)

    def c_l2(r):   # 伏笔超期未收
        _mk_eps(r, 6)
        (r / "连续性台账.md").write_text(
            LED_HEAD % ("| FB-01 | 旧怀表 | 1 | 1 | 埋 | |", "", ""), encoding="utf-8")

    def c_l3(r):   # 已故角色后续集仍有台词
        _mk_eps(r, 2)
        (r / "连续性台账.md").write_text(
            LED_HEAD % ("", "| 甲 | 1 | 死亡 |  | 1 | 第 1 集坠楼 |", ""), encoding="utf-8")

    def c_l4(r):   # 道具早于首次出现集被提及
        (r / "连续性台账.md").write_text(
            LED_HEAD % ("", "", "| 门 | 2 | 甲 | 关着 | 1 |"), encoding="utf-8")

    def c_s11(r):  # 台词行格式不认，会被静默丢掉
        p = r / "剧集" / "EP001" / "剧本.md"
        p.write_text(read_text(p) + "\n[音效] 门板：吱呀一声。\n", encoding="utf-8")

    def c_s12(r):  # 剧本连场次都没有
        p = r / "剧集" / "EP001" / "剧本.md"
        p.write_text(read_text(p).replace("## EP001-SC001 内 · 屋 · 夜", "第一场 屋里 夜里"),
                     encoding="utf-8")

    def c_a15(r):  # 多格图没声明格数上限
        _edit(r / "人物资产" / "甲.md", "仅此 4 格，不出现第 5 格。", "")

    def c_a13(r):  # 主视觉误写成四格板
        _edit(r / "人物资产" / "甲-主图.md", "单张成图", "全图共 4 格")

    def c_r6(r):   # 图号重复
        _edit(r / "视觉设定.md", "- 资产编号：图2", "- 资产编号：图1")

    def c_a3(r):   # 马赛克
        _edit(r / "人物资产" / "甲.md", "【背景】纯白无缝背景。",
              "【背景】纯白无缝背景。脸部可打马赛克处理。")

    def c_a9(r):   # 删背面视图
        _edit(r / "服装资产" / "甲-常服.md", "【背面视图】", "【背视图】")

    def c_a10(r):  # 武器无长度参照
        _edit(r / "武器资产" / "刀.md", "全长约 90 厘米；立起时刃尖到成年女性下巴，柄底齐腰。",
              "一把很长的刀。")
        _edit(r / "武器资产" / "刀.md", "柄部长 18 厘米", "柄部很长")

    def c_m1(r):   # 未登记模型
        _cfg(r / "short-drama.json", lambda d: d["spec"].update({"target_model": "unknown-model-x"}))

    def c_m4(r):   # 单镜超单段上限（改用 veo 8s 限制）
        _cfg(r / "short-drama.json",
             lambda d: d["spec"].update({"target_model": "veo-3.1", "duration_cap_sec": 8}))
        _edit(r / "剧集" / "EP001" / "分镜.md", "- 时长：3.5s", "- 时长：9s")

    return [
        ("S0", "S", "分镜一镜都没有", c_s0),
        ("S3", "S", "场次 ID 重复", c_s3),
        ("S5", "S", "镜头 ID 重复", c_s5),
        ("S7", "S", "来源指向不存在场次", c_s7),
        ("S6", "S", "镜头缺职责字段", c_s6),
        ("S8", "S", "单镜 40 秒超模型上限", c_s8),
        ("S11", "S", "台词行格式不认", c_s11),
        ("L1", "L", "多集项目无台账", c_l1),
        ("L2", "L", "伏笔超期未收", c_l2),
        ("L3", "L", "已故角色仍有台词", c_l3),
        ("L4", "L", "道具早于首次出现被提", c_l4),
        ("S12", "S", "剧本没有场次", c_s12),
        ("X1", "X", "台词超画幅上限", c_x1),
        ("X3", "X", "台词塞不进 2 秒镜", c_x3),
        ("X2", "X", "台词缺语气位", c_x2),
        ("X4", "X", "词根污染（否定/比喻）", c_x4),
        ("X5", "X", "一镜塞多个动作", c_x5),
        ("X6", "X", "缺关键帧提示词", c_x6),
        ("X7", "X", "关键帧无氛围层", c_x7),
        ("X9", "X", "图片提示词写「粒子」", c_x9),
        ("A12", "A", "静态设定稿写「粒子」", c_a12),
        ("A13", "A", "主视觉误写成四格板", c_a13),
        ("A15", "A", "缺格数上限声明", c_a15),
        ("R1", "R", "引用未登记人物", c_r1),
        ("R2", "R", "锁面被改写", c_r2),
        ("R6", "R", "资产编号重复", c_r6),
        ("A1", "A", "删四格声明", c_a1),
        ("A2", "A", "出现砍头写法", c_a2),
        ("A8", "A", "未声明无此结构", c_a8),
        ("A3", "A", "出现马赛克字面词", c_a3),
        ("A6", "A", "删九格声明", c_a6),
        ("A9", "A", "服装缺背面视图", c_a9),
        ("A10", "A", "武器无长度参照", c_a10),
        ("C1", "C", "AI 标识未确认", c_c1),
        ("M1", "M", "用了未登记模型", c_m1),
        ("M1b", "M", "用了已停服模型", c_m1b),
        ("M2", "M", "cap 与模型上限不符", c_m2),
        ("M4", "M", "单镜超模型单段上限", c_m4),
        ("Q1", "Q", "竖屏出现空镜", c_q1),
        ("Q2", "Q", "群像无人有事务", c_q2),
        ("Q3", "Q", "照抄已废硬约束", c_q3),
    ]


def cmd_selftest(args):
    """跑内置回归：每项检查是否真的能拦住它该拦的问题。"""
    import tempfile
    import shutil

    out("机检自测 · %d 项" % len(st_cases()))
    out("")

    # 基线：先确认最小项目本身是干净的
    base = Path(tempfile.mkdtemp(prefix="cd_st_"))
    try:
        st_build(base / "clean")
        rep = check_project(base / "clean")
        base_ok = (len(rep.failed) == 0 and len(rep.warned) == 0)
        if base_ok:
            out("✓ 基线  最小项目零告警（%d 项通过）" % len(rep.items))
        else:
            out("✗ 基线  最小项目本身就有告警，后续自测不可信：")
            for g, c, stt, m, w in rep.items:
                if stt in ("FAIL", "WARN"):
                    out("    %s%s %s %s" % (g, c, stt, m))
            if not args.keep:
                shutil.rmtree(base, ignore_errors=True)
            return 2
        out("")

        fails = []
        for code, group, desc, inject in st_cases():
            d = base / ("case_" + code)
            shutil.copytree(base / "clean", d)
            try:
                inject(d)
            except AssertionError as e:
                out("? %-4s 样本构造失败：%s" % (code, e))
                fails.append(code)
                continue
            rep = check_project(d)
            hit = [i for i in rep.items if i[1] == code
                   and i[2] in ("FAIL", "WARN")]
            if hit:
                out("✓ %-4s %s" % (code, desc))
            else:
                same = [i for i in rep.items if i[1] == code]
                stt = same[0][2] if same else "未产出"
                out("✗ %-4s %s —— 该项状态 %s，没拦住" % (code, desc, stt))
                fails.append(code)

        out("")
        ok = len(st_cases()) - len(fails)
        out("结果：%d/%d 项检查有效" % (ok, len(st_cases())))
        if fails:
            out("失效项：%s" % "、".join(fails))
            out("这几项等于没写机检，先修再交付。")
        if args.keep:
            out("样本保留在：%s" % base)
        else:
            shutil.rmtree(base, ignore_errors=True)
        return 1 if fails else 0
    except Exception:
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)
        raise


def cmd_check(args):
    rep = check_project(args.project, args.only.split(",") if args.only else None, args.episode)
    sig = _content_sig(args.project, rep.items)
    if args.json:
        out(json.dumps({
            "failed": len(rep.failed),
            "warned": len(rep.warned),
            "fingerprint": sig,
            "items": [{"group": g, "code": c, "status": s, "message": m, "where": w}
                      for g, c, s, m, w in rep.items],
        }, ensure_ascii=False, indent=2))
    else:
        out("漫剧机检 · %s" % args.project)
        rep.render([g for g in "SRXCAMQL" if not args.only or g in args.only])
        out("")
        n_all = len(rep.items)
        n_info = sum(1 for i in rep.items if i[2] == "INFO")
        out("结果：共 %d 项 · 通过 %d · FAIL %d · WARN %d%s"
            % (n_all, n_all - len(rep.failed) - len(rep.warned) - n_info,
               len(rep.failed), len(rep.warned),
               (" · INFO %d" % n_info) if n_info else ""))
        if rep.failed:
            out("FAIL 必须清零再交付。")
        out("凭证 %s · %s · %d 项 · %s"
            % (sig, str(Path(args.project)).replace("\\", "/").rstrip("/").split("/")[-1],
               n_all, time.strftime("%Y-%m-%d %H:%M")))
        out("（同一份文件复现一次，凭证必须相同；对不上说明不是真跑的）")
    return 1 if rep.failed else 0


# ---------------------------------------------------------------- estimate

def cmd_estimate(args):
    text = read_text(args.script)
    if not text:
        out("读不到文件：%s" % args.script)
        return 2
    script = parse_script(text)
    if not script.scenes:
        out("没有解析到场次。检查剧本.md 的标题语法：## EP001-SC001 内 · 地点 · 时间")
        return 2

    # 语速按画幅取默认值：竖屏爽剧念得快，横屏精品剧慢一点
    cps = args.cps
    cps_src = "手动指定"
    if cps is None:
        cfg = {}
        # 从剧本所在目录向上找 short-drama.json，找到就用它的画幅
        for up in Path(args.script).resolve().parents:
            cand = up / "short-drama.json"
            if cand.exists():
                try:
                    cfg = json.loads(read_text(cand) or "{}")
                except json.JSONDecodeError:
                    cfg = {}
                break
        ar = str((cfg.get("spec", {}) or {}).get("aspect_ratio", ""))
        cps = tune(cfg, "cps", DEFAULT_CPS)
        cps_src = ("%s 档默认" % ar) if ar in FORMAT_TUNING else "通用默认（%s）" % (ar or "画幅未定")

    total = 0.0
    out("逐场折算（语速 %.1f 字/秒 · %s · 留白 %.2fs · 收口 %.1fs）"
        % (cps, cps_src, PAUSE, LINE_HEADROOM))
    out("")
    for sc in script.scenes:
        sc_dur = 0.0
        n_line = 0
        for item in sc["audio"]:
            r = match_line(item)
            if r:
                sc_dur += line_duration(r[2], cps)
                n_line += 1
        for item in sc["visual"]:
            if not item:
                continue
            hit = False
            for sid, who, tone, txt in script.lines:
                if sid == sc["id"] and txt and txt in item:
                    hit = True
                    break
            if not hit:
                sc_dur += action_duration(item)
        total += sc_dur
        out("  %-14s %5.1fs  （%d 句台词 / %d 条画面）"
            % (sc["id"], sc_dur, n_line, len(sc["visual"])))

    out("")
    out("合计：%.1f 秒（%.2f 分钟）" % (total, total / 60))
    out("台词总字数：%d" % sum(cn_len(t) for _, _, _, t in script.lines))
    out("台词句数：%d" % sum(1 for _ in script.lines))

    tgt = args.target
    if tgt:
        diff = (total - tgt) / float(tgt)
        flag = "在容忍范围" if abs(diff) <= TOLERANCE else "超出容忍范围（±%.0f%%）" % (TOLERANCE * 100)
        out("对比目标 %ss：偏差 %+.1f%% → %s" % (tgt, diff * 100, flag))
    return 0


# ---------------------------------------------------------------- init

PROJECT_TEMPLATE = {
    "title": "",
    "spec": {
        "form": "",
        "aspect_ratio": "9:16",
        "target_model": "",
        "episode_duration_sec": 120,
        "episode_count": 12,
        "platform": "",
        "asset_mode": "M1",
    },
    "compliance": {"ai_label": False, "filing_tier": "", "redline_ok": False},
    "rhythm": {
        "first_hook_seconds": 3,
        "beat_interval_seconds_max": 12,
        "end_on_peak": True,
    },
}


def cmd_init(args):
    root = Path(args.dir)
    (root / "剧集").mkdir(parents=True, exist_ok=True)
    (root / "审查").mkdir(exist_ok=True)
    (root / "输入").mkdir(exist_ok=True)

    cfgp = root / "short-drama.json"
    if not cfgp.exists():
        cfg = json.loads(json.dumps(PROJECT_TEMPLATE))
        cfg["title"] = args.title
        cfg["spec"]["form"] = args.form or ""
        cfg["spec"]["aspect_ratio"] = args.aspect
        cfg["spec"]["target_model"] = args.model or ""
        cfg["spec"]["episode_duration_sec"] = args.duration
        cfg["spec"]["episode_count"] = args.episodes
        cfg["spec"]["platform"] = args.platform or ""
        cfgp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out("已建 short-drama.json")

    bi = root / "视觉设定.md"
    if not bi.exists():
        bi.write_text(BIBLE_SEED, encoding="utf-8")
        out("已建 视觉设定.md（全季共用）")

    made = 0
    for i in range(1, args.episodes + 1):
        ep = root / "剧集" / ("EP%03d" % i)
        ep.mkdir(parents=True, exist_ok=True)
        for name, tpl in (("剧本.md", SCRIPT_SEED), ("分镜.md", BOARD_SEED),
                          ("图片提示词.md", IMG_SEED)):
            f = ep / name
            if not f.exists():
                f.write_text(tpl.replace("{EP}", "EP%03d" % i), encoding="utf-8")
                made += 1
    out("已建 %d 集的创作文档（%d 个文件）" % (args.episodes, made))
    out("")
    out("下一步：")
    out("  1. 填 short-drama.json 的 spec/compliance（P0 四道锁）")
    out("  2. 写 视觉设定.md（人物/地点/道具，每条带资产编号）")
    out("  3. 写 剧集/EP001/剧本.md")
    out("  4. 出资产：复制 assets/人物四格板模板.md、场景九宫格模板.md")
    out("  5. 写 剧集/EP001/分镜.md → check → pack → board")
    out("")
    out("注意：刚建完跑 check 会有 FAIL，这是正常的——空项目当然不完整。")
    out("按上面五步填完，FAIL 才会清零。")
    return 0


SCRIPT_SEED = """# {EP} 集名

## {EP}-SC001 内 · 地点 · 夜

### 画面轨
- （写摄影机拍得到的东西。禁心理描写、禁括号暗示、禁比喻。）

### 听觉轨
- 角色名（语气位）：台词（单句 ≤15 字）
- [SFX] 音效
- [BGM] 音乐
"""

BOARD_SEED = """# {EP} 分镜

> 本文件是空骨架，**不算镜头**。镜头格式见 `assets/分镜模板.md`，复制一条改。
> 解析器只认行首的 `## SHOT-{EP}-001` 形式，编号连续。

## 场景站位 · {EP}-SC001 · 地点
- 固定锚点：
- 人物：
- 轴线：
- 变化：无
"""

IMG_SEED = """# {EP} 图片提示词

> 每镜一条可投产的冻结关键帧提示词。`IMG-` 只是条目 ID，不代表图已生成。

## IMG-{EP}-001 · 镜头名
- 用途：〔锁定本镜起始构图与人物状态〕
- 对应分镜：SHOT-{EP}-001
- 参考：无外部参考

### 可复制提示词
> 〔画风基底 → 景别画幅角度 → 空间站位 → 氛围六件套 → 冻结瞬间 → 视觉重点 → 可读性约束 → 排除项〕
"""

BIBLE_SEED = """# 视觉设定

> 全季共用一份。不要每集复制。

## 人物 · 角色名
- 识别锚点：（30–60 字，全是可画的物理事实）
- 画面代称：Name、角色名
- 声音：（音色质地，不写组合词）
- 本集造型：见「造型 · 角色名-造型名」
- 状态变化：无
- 连续性锁：LOCK-XXX《短名词锁面》（镜头：入画）

## 造型 · 角色名-造型名
- 身份：角色名
- 适用：EP001-SC001 至 EP001-SC004
- 锁定：（服装形制、材质、主色）

## 地点 · 地点名
- 空间锚点：（方位 + 固定陈设）
- 光线变体：
  - 夜景（主）：
  - 日景：
- 连续性锁：LOCK-XXX《短名词锁面》（镜头：入画）

## 道具 · 道具名
- 外观锚点：
- 尺寸基准：
- 状态：
- 连续性锁：LOCK-XXX《短名词锁面》（镜头：入画）

## 时代锚点 · （古装/年代戏才写）
- 必须在场：
- 禁止出现：
- 光线来源：
"""


# ---------------------------------------------------------------- pack

SEVEN_SECTIONS = ("画幅风格", "场景资产", "核心人物", "站位声明", "时间轴分镜", "音效", "强制禁止项")


def cmd_pack(args):
    root = Path(args.project)
    ep = root / "剧集" / args.episode
    shots = parse_storyboard(read_text(ep / "分镜.md"))
    if not shots:
        out("分镜为空或解析失败：%s" % (ep / "分镜.md"))
        return 2
    _, cfg = load_project(root)
    spec = cfg.get("spec", {})
    bible = parse_bible(read_text(root / "视觉设定.md"))
    script = parse_script(read_text(ep / "剧本.md"))

    # 地点去重：一部戏通常只有几个景，不该按场次列
    locations = []
    for sc in script.scenes:
        parts = [p.strip() for p in sc["head"].split("·")]
        loc = parts[1] if len(parts) >= 2 else sc["head"]
        if loc and loc not in locations:
            locations.append(loc)

    lines = []
    lines.append("> 素材形态：%s" % spec.get("asset_mode", "M1"))
    lines.append("")
    lines.append("# %s 投喂稿 · %s" % (args.episode, spec.get("target_model", "未指定模型")))
    lines.append("")
    lines.append("> 模型 %s · 画幅 %s" % (spec.get("target_model", "?"), spec.get("aspect_ratio", "?")))
    lines.append("> 本文件由分镜骨架生成，**七段内容需按 `references/15-video-prompts.md` 逐段加工**："
                 "画风基底、光比色板、氛围六件套、站位五要素都要换成这部戏的真实事实，"
                 "占位符（……）必须全部替换。")
    lines.append("")
    lines.append("```text")
    lines.append("【画幅风格】%s %s。画风基底：……（一集一句，全集冻结）。"
                 "光比与色板：……（写具体数值与颜色名）。"
                 % (spec.get("aspect_ratio", ""), spec.get("form", "")))
    lines.append("")
    lines.append("【场景资产】%s" % "；".join(
        "@SCN-%s（空间锚点见视觉设定「地点 · %s」）" % (loc, loc) for loc in locations))
    lines.append("")
    people = []
    for (kind, name), fields in bible.entries.items():
        if kind == "人物":
            alias = fields.get("画面代称", name)
            people.append("@CHR-%s（按图锁定外形；年龄锚；造型锚）" % name)
    lines.append("【核心人物】%s" % ("；".join(people) if people else "（先补视觉设定人物条目）"))
    lines.append("")
    lines.append("【站位声明】%s" % "；".join(
        "@%s（画面… · 依托物 · 朝向 · 姿态 · 手头事务：…）" % n
        for n in [x for (k, x) in bible.entries if k == "人物"][:2]) +
        "；轴线锁定：…，全段禁越轴；位移：…")
    lines.append("")
    lines.append("【时间轴分镜】")
    t = 0.0
    for i, sh in enumerate(shots, 1):
        dur = float(re.sub(r"[^\d.]", "", sh.get("时长")) or 0)
        head = " · ".join(x for x in (sh.get("景别"), sh.get("角度"),
                                      sh.get("机位高度"),
                                      (sh.get("运镜") or "固定").split("；")[0]) if x)
        beats = [x.rstrip("。") for x in (sh.get("起点"), sh.get("唯一动作"), sh.get("终点")) if x]
        body = "。".join(beats) + "。"
        if t == 0:
            lines.append("  %s。%s" % (head, body))
        else:
            lines.append("  [Shot %d] At %s, the shot cuts to. %s。%s"
                         % (i, fmt_ts(t), head, body))
        t += dur
    lines.append("")
    lines.append("【音效】环境底：……（铺满全片）；动作音：按镜卡点；"
                 "强调音：……（峰值处）；静默：……（至少一处）")
    lines.append("")
    lines.append("【强制禁止项】画面：角色变形、多余手指、服装跳变、现代元素、"
                 "非画内字幕、水印、Logo。音频：……（需要纯环境音时写「无背景音乐」）。")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 素材接线单（M1 必附）")
    lines.append("")
    lines.append("| 图号 | 类型 | 用途 | 你该挂哪张 | 不控制什么 |")
    lines.append("|:--|:--|:--|:--|:--|")
    n = 0
    for sh in shots:
        refs = sh.get("输入参考图", "无")
        if "PLAN-" in refs or "REF-" in refs:
            n += 1
            lines.append("| 图%d | 起始帧 | 起始构图与站位 | %s 的冻结关键帧《图片提示词.md》 | "
                         "尚未发生的动作、终点状态 |" % (n, sh.id))
    lines.append("")
    lines.append("> 本包不持有图。上表是「你该在平台挂哪张」，不需要把图交回项目。")

    outp = ep / "视频提示词.md"
    outp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out("已生成 %s（%d 镜 / 估算 %ds / %d 个场景 / %d 个图槽）"
        % (outp, len(shots), int(t), len(locations), n))
    out("下一步：按 references/15-video-prompts.md 逐段替换占位符，过一次词根清洗。")
    return 0


def fmt_ts(sec):
    m = int(sec // 60)
    s = sec - m * 60
    return "%02d:%05.2f" % (m, s)


# ---------------------------------------------------------------- cast

RE_DIALOG = re.compile(r"^([^\[（：]{1,12})（([^）]*)）：(.+)$")
# 这些「说话人」没有视觉形象，不该进角色表
NARRATOR_NAMES = ("旁白", "画外音", "解说", "字幕", "OS", "V.O.", "vo", "narration")
# 模板占位名：init 生成的骨架里就有，不能当真实角色
PLACEHOLDER_NAMES = ("角色名", "人名", "姓名", "主角", "配角", "某某", "XX", "角色A", "角色B")


def collect_cast(root, target_ep=None):
    """从剧本提取全部角色：说话人 + 画面里出现的已登记人物名。"""
    bible = parse_bible(read_text(root / "视觉设定.md"))
    known = bible.names("人物")
    info = {}
    narr = []
    ph = []
    total_scenes = 0

    # 别名表：剧本里写「长老」，条目叫「执法长老」——靠「画面代称」接上。
    # 不建这张表，用户必须让剧本说话人和条目名逐字一致，太苛刻。
    alias = {}
    for n in known:
        alias[n] = n
        fields = bible.entries.get(("人物", n), {})
        raw = fields.get("画面代称", "") or ""
        for a in re.split(r"[、,，/|；;]", raw):
            a = a.strip()
            if a and a not in alias:
                alias[a] = n

    def resolve(name):
        return alias.get(name, name)

    def hit(name):
        name = resolve(name)
        d = info.setdefault(name, {"lines": 0, "scenes": set(), "eps": set(),
                                   "visual": 0})
        return d

    for epdir in find_episodes(root):
        if target_ep and epdir.name != target_ep:
            continue
        sc = parse_script(read_text(epdir / "剧本.md"))
        total_scenes += len(sc.scenes)
        for scene in sc.scenes:
            for line in scene["audio"]:
                m = RE_DIALOG.match(line)
                if not m:
                    continue
                who = m.group(1).strip()
                if any(k in who for k in NARRATOR_NAMES):
                    narr.append(who)
                    continue
                if who in PLACEHOLDER_NAMES:
                    ph.append(who)
                    continue
                d = hit(who)
                d["lines"] += 1
                d["scenes"].add(scene["id"])
                d["eps"].add(epdir.name)
            for line in scene["visual"]:
                # 画面轨同时认条目名与别名（长老 / 执法长老 / Elder）
                for n in alias:
                    if n and n in line:
                        d = hit(n)
                        d["visual"] += 1
                        d["scenes"].add(scene["id"])
                        d["eps"].add(epdir.name)
    return info, bible, total_scenes, sorted(set(narr)), sorted(set(ph))


def cast_grade(d, total_scenes=0):
    """按出场强度分级。A 才必须建板，B 可共享锚点，C 不建。

    除绝对数，还看「场次占比」：单集项目里，主角也可能只有三五场。
    但占比必须配台词下限——4 场的短集里，出现 3 场就是 75%，
    不设门槛的话，只有两句词的功能角色也会被判成主角。
    """
    eps = len(d["eps"])
    scenes = len(d["scenes"])
    lines = d["lines"]
    ratio = (scenes / total_scenes) if total_scenes else 0
    if lines >= 6 or scenes >= 8 or eps >= 3 or (ratio >= 0.6 and lines >= 3):
        return "A", "主角·必须建四格板"
    if lines >= 2 or scenes >= 2 or (ratio >= 0.3 and lines >= 1):
        return "B", "重要配角·建板或共享主角锚点"
    return "C", "龙套·不建板，文字描述即可"


def _parse_anchor(anchor):
    """从锚点里抠出年龄与性别，省得人再填一遍。"""
    age, sex = "", ""
    m = re.search(r"(\d{1,2})\s*岁", anchor)
    if m:
        age = m.group(1) + "岁"
    if "女性" in anchor or "女子" in anchor:
        sex = "女性"
    elif "男性" in anchor or "男子" in anchor:
        sex = "男性"
    return age, sex


def _outfit_of(fields, bible):
    """顺着「本集造型：见「造型 · X」」找到造型条目，取其锁定描述。"""
    ref = fields.get("本集造型", "")
    m = re.search(r"「造型 · ([^」]+)」", ref)
    if m:
        o = bible.entries.get(("造型", m.group(1).strip()), {})
        if o.get("锁定"):
            return o["锁定"], m.group(1).strip()
    # 退化：直接用条目里的「服装」字段
    if fields.get("服装"):
        return fields["服装"], ""
    return "", ""


def cast_prompt(name, fields, cfg, bible=None):
    """生成四格板提示词骨架。有视觉设定条目就填进去，没有留【】。"""
    anchor = fields.get("识别锚点", "")
    age0, sex0 = _parse_anchor(anchor)
    age = fields.get("年龄", "") or age0 or "【年龄区间，如 24~28】"
    sex = fields.get("性别", "") or sex0 or "【性别】"
    ident = fields.get("身份", "") or "【身份】"
    body = fields.get("体型", "") or "【身高·体态】"
    form = (cfg.get("spec", {}) or {}).get("form", "") or "【画风基底】"
    outfit_txt, outfit_name = (_outfit_of(fields, bible) if bible else ("", ""))

    L = []
    L.append("```text")
    L.append("角色设定图，%s %s %s（%s），全图共 4 格。" % (age, sex, ident, name))
    L.append("")
    L.append("【头身比】成年身材约 6.5 头身，肩宽腿长符合成年人。"
             "严禁儿童幼态、娃娃脸、Q 版、大头娃娃、头身比失调。")
    L.append("")
    L.append("【职业标识物】%s" % (fields.get("标识物", "【硬标识 + 服装形制 + 体态，三件套】")))
    L.append("反漂移：不添加任何未列出的配饰、制服元素、徽章。")
    L.append("")
    if anchor:
        L.append("【锚点·逐字复用】%s" % anchor)
    else:
        L.append("【识别锚点】%s" % "【30~60 字：脸型骨相 + 眉 + 眼 + 鼻 + 唇 + 发型 + 标志性特征】")
    L.append("")
    if body.strip() and not body.startswith("【"):
        L.append("【体型】%s" % body)
        L.append("")
    if outfit_txt:
        L.append("【服装】造型「%s」：%s" % (outfit_name or name, outfit_txt))
    else:
        L.append("【服装】【八字段：类型/颜色/面料/纹样/结构/状态/鞋袜/配饰】")
    L.append("")
    L.append("【版式】")
    L.append("第 1 格：面部四分之三侧特写，五官清晰，不戴帽不遮挡，头部完整入画。")
    L.append("第 2~4 格：无脸全身三视图（正面 / 标准侧面 / 背面），等高排列，脚底对齐同一基线。")
    L.append("三格全身一律去五官、保留头部轮廓，**头顶至鞋完整入画（含鞋袜，不裁头、不裁脚）**。")
    L.append("四格同一人、同一时刻、同一造型、同一光照。")
    L.append("")
    L.append("【背景】纯白无缝背景，柔和均匀影棚主光，接触阴影克制。")
    L.append("")
    L.append("【图面纪律】画面为纯图像，除图底短标签外无任何文字、无水印、无 Logo。"
             "禁止拼图之外的额外视图，禁止同一视图重复出现。")
    L.append("")
    L.append("【风格】%s" % form)
    L.append("```")
    return "\n".join(L)


def _outfit_fields(root, name):
    """服装资产文档里的八字段优先——视觉设定里的「锁定」只有一行，会截断。"""
    d = Path(root) / "服装资产"
    if not d.exists():
        return ""
    for f in sorted(d.glob("*.md")):
        if f.name.startswith("_") or name not in f.name:
            continue
        t = read_text(f)
        b = re.search(r"【服装八字段】(.+?)(?:【无此结构声明】|【正面视图】|```)", t, re.S)
        if b:
            txt = b.group(1).strip()
            # 特效字段不进参考图；markdown 粗体不能进投喂稿
            txt = re.split(r"\n⑨", txt)[0]
            return txt.replace("**", "").strip()
    return ""


def _norm_layout(s):
    s = (s or "").strip()
    return s.lower() if s.lower() in LAYOUTS else LAYOUT_ALIAS.get(s, s)


def _fit_outfit(c, full, lay):
    """参考图类图式只要形制，物料类图式吃八字段全文。"""
    if not full:
        return
    c["outfit"] = (_outfit_pick(full, "①②③⑤⑦⑧")
                   if lay in ("three-view", "four-view", "expression", "pose", "chibi")
                   else full)


def _outfit_pick(txt, keep="①②③⑤⑦⑧"):
    """按字段号取子集——三视图要的是形制，不是八字段全文。"""
    if not txt:
        return txt
    parts = re.split(r"\n(?=[①②③④⑤⑥⑦⑧⑨])", txt)
    d = {}
    for p in parts:
        m = re.match(r"([①②③④⑤⑥⑦⑧⑨])", p.strip())
        if m:
            d[m.group(1)] = p.strip()
    return "\n".join(d[k] for k in keep if k in d)


def _is_anime(form):
    return any(k in (form or "") for k in ("二次元", "动漫", "漫画", "国漫", "番剧", "动画"))


def _fig_ctx(name, fields, cfg, bible):
    anchor = fields.get("识别锚点", "") or ""
    age0, sex0 = _parse_anchor(anchor)
    outfit_txt, outfit_name = (_outfit_of(fields, bible) if bible else ("", ""))
    return dict(
        name=name,
        age=fields.get("年龄", "") or age0 or "",
        sex=fields.get("性别", "") or sex0 or "",
        ident=fields.get("身份", "") or "",
        anchor=anchor.strip(),
        body=fields.get("体型", "") or "",
        alias=fields.get("画面代称", "") or "",
        kit=(fields.get("标识物", "") or "").strip(),
        outfit=outfit_txt.strip(),
        outfit_name=outfit_name or "",
        form=(cfg.get("spec", {}) or {}).get("form", "") or "",
    )


def _fig_anchor_line(c):
    """把识别锚点拆成一行可复述的角色锚；拆不出来就整段复用。"""
    a = c["anchor"].rstrip("。")
    bits = [x for x in (c["age"], c["sex"], c["ident"]) if x and x not in a]
    head = "，".join(bits)
    if a:
        return (head + "；" + a) if head else a
    head = head or "【年龄 + 性别 + 身份】"
    return head + "；【脸型骨相 + 眉 + 眼 + 鼻 + 唇 + 发型 + 标志性特征】"


def _fig_outfit_line(c):
    if c["outfit"]:
        nm = ("造型「%s」：" % c["outfit_name"]) if c["outfit_name"] else ""
        body = c["outfit"].rstrip("。")
        return "【服装】" + nm + ("\n" + body if "\n" in body.strip() else body)
    return "【服装】【八字段：类型 / 颜色 / 面料 / 纹样 / 结构 / 状态 / 鞋袜 / 配饰】"


def _fig_anime_block(c):
    """二次元题材追加词法段。写实向不输出。"""
    if not _is_anime(c["form"]):
        return []
    return [
        "【二次元词法】风格锚只取一个：赛璐璐上色——阴影为两段平涂、边界硬边，"
        "高光为形状而非渐变；线稿为干净的等粗细线，轮廓线完整闭合。",
        "眼睛五层：内眼角〔尖/钝〕、外眼角〔上扬 5°/平〕；虹膜占眼高约 70%，上缘被上眼睑遮 1/5，"
        "上深下浅；瞳孔占虹膜约 1/3，边缘清晰；高光在虹膜左上 1/4 处，大小约瞳孔的 1/2；"
        "下眼睑一条细线，下方无阴影。",
        "发束分组：共〔7〕组——额前刘海 2 组（端点在下眼睑高度）、两侧鬓发 2 组（端点在下颌角）、"
        "后脑 3 组（端点及〔腰〕）；另加 5~8 根游离细发，方向与主发束一致。",
        "鼻子与嘴简化：鼻子为一个点/一条短线/一块斜向阴影（三选一），不写鼻梁高度；"
        "嘴为一条闭合线或一个小三角，靠下唇阴影给出厚度。",
        "排除项（英文，放最后）：no photorealistic skin texture, no visible pores, "
        "no 3d render gloss, no extra fingers, no malformed hands, no asymmetric eyes, "
        "no watermark, no signature, no text.",
    ]


def _fig_body(c, layout, ratio):
    L = []
    A = _fig_anchor_line(c)
    O = _fig_outfit_line(c)
    form = ("【风格】%s" % c["form"]) if c["form"] else "【风格】〔画风基底：写实 / 3D / 二次元 三选一〕"

    if layout == "portrait":
        L += ["【版式】单张头像，%s，头部占画面高度约 65%%，取景自头顶至锁骨下方。" % ratio,
              "【角色锚】%s" % A,
              "【表情】〔一种主情绪，写肌肉不写词：如嘴角单侧上提 3 毫米，下眼睑微收〕",
              "【姿态】头部微转约 15°，肩线一高一低，重心偏一侧。",
              "【光】主光来自右前上方 45°，光比 1:4；下颌下方一道柔和过渡阴影；眼白上一点针尖大的高光。",
              "【背景】纯色〔色名〕或渐变〔由什么色到什么色〕。",
              "【图面纪律】除人物外无其他主体；无文字、无水印、无边框。"]
    elif layout == "fullbody":
        L += ["【版式】单张全身立绘，%s 竖构图，头顶至鞋底完整入画（不裁头、不裁脚、不露底），"
              "人物占画面高度约 85%%，脚底距画面下沿约 3%%。" % ratio,
              "【角色锚】%s" % A,
              "【体型】%s" % (c["body"] or "〔身高 cm〕，〔头身比〕；肩宽约〔x〕个头宽"),
              "【姿态】〔站姿：重心在哪只脚、手在做什么〕；重心偏一侧，不站军姿。",
              *O.splitlines(),
              "【光】主光〔方位〕，光比 1:5；地面有接触阴影，朝向与主光一致。",
              "【背景】纯色〔色名〕/ 渐变 / 简化环境（一句写完，不出现第二个主体）。",
              "【图面纪律】单人单图；无文字、无水印；不出现第二个人物、不出现道具特写。"]
    elif layout in ("three-view", "four-view"):
        g = 4 if layout == "four-view" else 3
        if g == 4:
            L += ["【版式】四视图设定稿，全图共 4 格，横向并排：① 面部特写 ② 正面全身 ③ 90° 侧面全身 ④ 背面全身。",
                  "① 是全图唯一清晰的脸，头部占该格高度 ≥70%；",
                  "②③④ 为无脸全身，头部完整入画（featureless face, no facial features, "
                  "smooth untextured facial plane），头顶至鞋完整，脚底对齐同一基线。"]
        else:
            L += ["【版式】三视图设定稿，全图共 3 格，横向等高并排：① 正面 ② 90° 侧面 ③ 背面。",
                  "三格均为无脸全身（featureless face, no facial features, "
                  "smooth untextured facial plane），头部完整入画，头顶至鞋全部可见，脚底对齐同一基线。"]
        L += ["三格同一人、同一时刻、同一造型、同一光照。",
              "【角色锚】%s" % A,
              *O.splitlines(),
              "【光】平光，无主光方向，不产生方向性投影；仅脚下有极淡接触阴影。",
              "【背景】纯白无缝背景。",
              "【图面纪律】仅此 %d 格，不设大主图、不重复视角、不出现第 %d 格；无文字、无标注、无箭头。" % (g, g + 1)]
    elif layout == "profile":
        L += ["【版式】角色档案海报（character profile sheet），%s 竖版，分区布局，共 5 个区块：" % ratio,
              "① 左侧 60%% 宽：全身立绘（头顶至鞋完整入画），占版面高度 70%%，带轻微环境与投影；",
              "② 右上：面部特写方图，占版面宽度 30%%、高度 22%%；",
              "③ 右中：三行文字信息区（角色名 / 身份 / 一行标语），左对齐；",
              "④ 右下：四格小图带（正面 / 侧面 / 背面 / 背面细节），每格等高；",
              "⑤ 底部横条：色板五格（主色 / 辅色 / 点缀 / 深色 / 高光色），色块等高。",
              "【版式纪律】只有这 5 个区块；区块之间留白 ≥ 版宽 3%%；所有区块共用同一角色、同一造型、同一光照方向。",
              "【角色锚】%s" % A,
              *O.splitlines(),
              "【背景】设计化底色〔如深灰纸质底 / 单色平涂〕，允许极淡纹理。",
              "【图面纪律】文字区只允许「角色名 + 身份 + 一行标语」三段，其余零文字；无页码、编号、Logo、花边。"]
    elif layout == "expression":
        L += ["【版式】表情集，全图共 4 格，%s，4 格等大网格排列，每格为头肩像（头顶至锁骨下方），"
              "每格头部大小一致、朝向一致、光位一致。" % ratio,
              "【格内容】①〔表情 A〕 ②〔表情 B〕 ③〔表情 C〕 ④〔表情 D〕",
              "【表情写法】写肌肉与五官位移，不写情绪词。例：「眉内侧上抬 2 毫米，"
              "上眼睑抬至露出完整瞳仁，嘴角向两侧拉开、露出上齿 4 颗」。",
              "【角色锚】%s" % A,
              "【一致性】四格为同一人，发型、发色、眼型、瞳色、领口不得变化。",
              "【光】正面平光，光比 1:3，无方向性投影。",
              "【背景】纯白或极浅灰，单色，每格底色相同。",
              "【图面纪律】无文字、无表情名称标注、无边框装饰；仅此 4 格，不出现第 5 格。"]
    elif layout == "outfit":
        L += ["【版式】服装设定板，%s 横版，正面 / 标准侧面 / 背面三个等高全身视图（头顶至鞋完整入画），脚底对齐同一基线；"
              "另设部件拆解区（领口、袖口、腰带、鞋）、材质样片区（4~6 块）、颜色样片区（4~6 格）。" % ratio,
              "【角色锚】%s（不出现面部特征）" % A,
              *O.splitlines(),
              "【光】均匀平光，无方向性投影。",
              "【背景】纯白无缝背景。",
              "【图面纪律】不出现剧情背景、不出现道具、无文字标注、无水印。完整八字段与「无此结构」声明见服装资产文档。"]
    elif layout == "pose":
        L += ["【版式】姿态集，全图共 4 格，%s，4 格等大，每格一个全身动态姿势（头顶至鞋完整入画），"
              "人物占该格高度 80%%。" % ratio,
              "【格内容】①〔招式/动作 A〕 ②〔B〕 ③〔C〕 ④〔D〕",
              "【动作写法】每格写「起始姿态 → 力从哪来 → 落点在哪 → 衣摆与头发怎么动」，"
              "不写「很激烈」「高速」。",
              "【角色锚】%s" % A,
              *O.splitlines(),
              "【光】统一侧光，四格光位一致。",
              "【背景】纯白或极浅灰。",
              "【图面纪律】除速度线外无装饰；无文字、无招式名标注；仅此 4 格，不出现第 5 格。"]
    elif layout == "kv":
        L += ["【版式】单张主视觉，%s，取景自头顶至〔小腿中部 / 腰线〕，人物占画面高度约 80%%，"
              "主体偏〔左/右〕三分线，另一侧留给环境与特效。" % ratio,
              "【场景】〔一句时空 + 一句空间构成 + 一句前景遮挡〕",
              "【光】主光〔方位 + 色温 + 光比〕；补光〔方位 + 强度比〕；影子朝向与主光一致。",
              "【动作】一个停在中间的动作（未完成，让图还在动）。",
              "【角色锚】%s" % A,
              *O.splitlines(),
              "【特效】〔按 references/11-vfx-and-particles.md 第八节写：材质、层、方向、中间态、亮度上限〕",
              "【图面纪律】无文字、无水印；不出现第二个角色。本图不作参考图使用。"]
    elif layout == "chibi":
        L += ["【版式】Q 版单图，%s，全身（头顶至鞋完整入画），头身比 2.5~3 头身，"
              "头部占画面高度约 50%%。" % ratio,
              "【角色锚】提取三个最强识别点：〔发型轮廓〕/〔标志性配饰〕/〔主色〕；其余细节一律简化。",
              "【表情】〔一种〕",
              "【背景】纯色〔色名〕或透明感单色。",
              "【图面纪律】不写实化、不加细节纹理、无文字。"]
    elif layout == "lineup":
        L += ["【版式】角色阵容图，%s，〔3~6〕人横向并排站立，全部全身、头顶至鞋完整入画，"
              "脚底对齐同一基线；人物间距一致，不重叠、不互相遮挡。" % ratio,
              "【高度关系】按设定身高排序（最高 / 最矮相差约〔8〕厘米），不得拉平。",
              "【角色锚】",
              "  ① %s" % A,
              "  ② 〔第二位：年龄 + 性别 + 身份；脸型与五官；发型与发色；服装主色；一处与①互斥的记忆点〕",
              "【防同脸】每人给一个互斥的记忆点（一个戴斗笠、一个光头、一个极瘦），靠轮廓区分，不靠脸。",
              "【光】统一主光方位，所有人共享同一光位与色温。",
              "【背景】设计化底色 / 极简环境。",
              "【图面纪律】无文字、无角色名标注、无装饰。"]

    L.append("")
    L.append(form)
    for line in _fig_anime_block(c):
        L.append(line)
    return L


def figure_prompt(c, layout, ratio=None):
    meta = LAYOUTS[layout]
    r = ratio or meta["ratio"]
    head = "# %s · %s（%s）" % (c["name"], meta["name"], layout)
    note = "> 用途：%s。背景：%s。光：%s。%s" % (
        meta["use"], meta["bg"], meta["light"],
        "可作参考图。" if meta["ref"] else "不作参考图——带环境与特效会污染后续镜头。")
    L = [head, "", note, "", "```text"]
    body = _fig_body(c, layout, r)
    # 职业标识物统一插在角色锚之后——少这一行，出来就是路人
    kit = c.get("kit") or "硬标识〔一眼认出行当的物件〕；形制〔取服装①〕；体态〔长期职业塑造的身体习惯〕"
    for i, line in enumerate(body):
        if line.startswith("【角色锚】"):
            body.insert(i + 1, "【职业标识物】" + kit)
            break
    L += body
    L.append("```")
    L += ["", "【自检】"]
    L.append("- 版式：%s，%s，%d 格" % (meta["name"], r, meta["grids"]) if meta["grids"] else
             "- 版式：%s，%s，多区块" % (meta["name"], r))
    L.append("- 槽位填满，填空写「无」")
    L.append("- 图面纪律：无文字、无水印")
    if meta["grids"] > 1:
        L.append("- 格数上限：仅此 %d 格，不出现第 %d 格" % (meta["grids"], meta["grids"] + 1))
    return "\n".join(L)


def _srt_time(sec):
    ms = int(round(max(0.0, sec) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def _split_sub(text, max_chars=14):
    """字幕断句：先按标点，再按字数硬切；不在「的了是就」后面断。"""
    raw = [p.strip() for p in re.split(r"(?<=[。！？!?…；;，,])", text or "") if p.strip()]
    out_ = []
    for seg in raw:
        seg = seg.rstrip("，,、")
        while len(seg) > max_chars:
            cut = max_chars
            # 往前找语义边界，最多回退 4 字
            for back in range(0, 4):
                if seg[cut - back - 1] not in "的地得了着过是和与就才也都又很":
                    cut = cut - back
                    break
            out_.append(seg[:cut])
            seg = seg[cut:]
        if seg:
            out_.append(seg)
    return out_


def cmd_srt(args):
    """从分镜生成 SRT 骨架：按镜长与语速铺时间轴，字幕逐字取自剧本台词。"""
    root = Path(args.project)
    ep = root / "剧集" / args.episode
    shots = parse_storyboard(read_text(ep / "分镜.md"))
    if not shots:
        out("分镜里没有镜头。先写 剧集/%s/分镜.md" % args.episode)
        return 2

    _, cfg = load_project(root)
    cps = args.cps or tune(cfg, "cps", DEFAULT_CPS)

    lines, idx, t = [], 0, 0.0
    for sh in shots:
        d = float(re.sub(r"[^\d.]", "", sh.get("时长")) or 0) or 2.0
        m = re.search(r"）：(.+?)(?:\s*\[|$)", sh.get("声音", ""))
        subs = _split_sub(m.group(1).strip()) if m else []
        if subs:
            lead = min(0.25, d * 0.12)          # 开口前的预备
            span = max(0.5, d - lead - 0.15)
            total = sum(len(x) for x in subs) or 1
            cur = t + lead
            for s in subs:
                dur = max(0.6, span * len(s) / total)
                end = min(cur + dur, t + d - 0.05)
                if end <= cur:
                    end = cur + 0.4
                idx += 1
                lines.append((idx, cur, end, s))
                cur = end
        t += d

    if not lines:
        out("分镜里没有可用的台词（「- 声音：」字段为空）。")
        out("两条路：")
        out("  1. 在分镜每镜补 `- 声音：角色（语气）：台词` —— 推荐，字幕与镜头天然对齐")
        out("  2. 从剧本取台词手动铺轴 —— 见 剧集/%s/剧本.md" % args.episode)
        return 0

    body = "\n".join("%d\n%s --> %s\n%s\n" % (i, _srt_time(a), _srt_time(b), txt)
                     for i, a, b, txt in lines)
    outp = Path(args.out) if args.out else (ep / "字幕.srt")
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(body, encoding="utf-8")
    out("已写入 %s" % outp)
    out("  %d 条字幕 · 覆盖 %.1f 秒 · 语速 %.1f 字/秒 · 分镜总长 %.1f 秒"
        % (len(lines), t, cps, t))
    over = [i for i, a, b, txt in lines if len(txt) > 20]
    if over:
        out("  ⚠ 有 %d 条字幕超 20 字（第 %s 条），会被阅读速度拖住"
            % (len(over), "、".join(str(x) for x in over[:5])))
    out("  提示：这是按镜长铺的骨架，配音出来后按实际波形微调入出点。")
    return 0


def cmd_figure(args):
    if args.list:
        out("可用图式（%d 种）：" % len(LAYOUTS))
        out("")
        out("%-12s %-14s %-6s %-4s %-20s %s" % ("代号", "名称", "画幅", "格", "用途", "可作参考图"))
        for k, v in LAYOUTS.items():
            out("%-12s %-14s %-6s %-4s %-20s %s"
                % (k, v["name"], v["ratio"], v["grids"] or "-", v["use"], "是" if v["ref"] else "否"))
        out("")
        out("中文别名也认：三视图 / 四视图 / 立绘 / 头像 / 档案 / 表情 / 服装 / 动作 / 主图 / Q版 / 阵容")
        return 0

    root = Path(args.project)
    root, cfg = load_project(root)
    bible = parse_bible(read_text(root / "视觉设定.md"))
    if not bible.entries:
        out("找不到 视觉设定.md 里的人物条目")
        return 1

    layout = _norm_layout(args.layout or "fullbody")
    if layout not in LAYOUTS:
        out("未知图式：%s" % args.layout)
        out("用 --list 看全部代号")
        return 1

    chars = [(k[1], v) for k, v in bible.entries.items() if k[0] == "人物"]
    if args.char:
        chars = [(n, f) for n, f in chars if args.char in n]

    if not chars:
        out("没找到人物条目。先跑 cast 或手写 视觉设定 的「人物 · 名字」段。")
        return 1

    blocks = []
    for name, fields in chars:
        c = _fig_ctx(name, fields, cfg, bible)
        _fit_outfit(c, _outfit_fields(root, name), layout)
        blocks.append(figure_prompt(c, layout, args.ratio))

    text = "\n\n---\n\n".join(blocks)
    if args.out:
        p = Path(args.out)
        if p.is_dir():
            p = p / ("%s-%s.md" % (chars[0][0] if len(chars) == 1 else "人物", layout))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
        out("已写入 %s（%d 份）" % (p, len(blocks)))
    else:
        out(text)
    return 0


def cmd_cast(args):
    """从剧本提取角色，输出建卡清单与该图式的提示词骨架。"""
    root, cfg = load_project(args.project)
    lay = _norm_layout(getattr(args, "layout", "") or "four-view")
    if lay not in LAYOUTS:
        lay = "four-view"
    info, bible, total_scenes, narr, ph = collect_cast(root, args.episode)
    if not info:
        out("剧本里没提取到角色，未生成清单。")
        if ph:
            out("（检测到模板占位名：%s —— 说明剧本还是 init 生成的空壳）" % "、".join(ph))
        out("")
        out("可能的原因：")
        out("  1. 还没写剧本 → 先写 剧集/EP001/剧本.md")
        out("  2. 台词没按「名字（语气）：台词」格式写 → 参考 assets/剧本模板.md")
        out("  3. 剧本里只有画面轨没有听觉轨 → cast 靠对白认人，画面里的人都需先进视觉设定")
        return 2

    rows = []
    for name, d in info.items():
        g, why = cast_grade(d, total_scenes)
        fields = bible.entries.get(("人物", name), {})
        registered = bool(fields)
        anchor = fields.get("识别锚点", "")
        # 旁白这类「无视觉形象」的角色不该建板
        visual = False if ("无视觉形象" in anchor) else (True if anchor else None)
        rows.append((g, name, len(d["eps"]), len(d["scenes"]), d["lines"],
                     registered, visual, why, None))
    rows.sort(key=lambda r: (r[0], -(r[4] * 10 + r[3])))

    out("角色提取 · %s" % cfg.get("title", "未命名"))
    out("")
    out("  %-2s %-10s %-4s %-4s %-4s %-8s %s"
        % ("级", "角色", "集", "场", "台词", "已登记", "建议"))
    for g, name, ne, ns, nl, reg, vis, why, cid in rows:
        out("  %-2s %-10s %-4d %-4d %-4d %-8s %s"
            % (g, name, ne, ns, nl, "是" if reg else "否", why))

    if narr:
        out("")
        out("已排除无视觉形象的说话人：%s（旁白类，只进台词轨，不建板）"
            % "、".join(narr))

    need = [r for r in rows if r[0] in ("A", "B")]
    pure_narr = [r for r in rows if r[6] is False]
    out("")
    out("合计 %d 人，其中 %d 人需要建板（A/B 级）。" % (len(rows), len(need)))
    if pure_narr:
        out("")
        out("注意：%s 在视觉设定里标为「无视觉形象」（如旁白），不要建板。"
            % "、".join(r[1] for r in pure_narr))
        need = [r for r in need if r[6] is not False]

    # 写建卡清单
    ep_tag = args.episode or "ALL"
    outdir = root / "人物资产"
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / ("_建卡清单-%s.md" % ep_tag)

    L = []
    L.append("# 建卡清单 · %s · %s" % (cfg.get("title", "未命名"), ep_tag))
    L.append("")
    L.append("> 由剧本自动提取。A/B 级逐个给四格板提示词骨架，填掉 `【】` 即可出图。")
    L.append("> 规范见 `references/05-character-assets.md`。")
    L.append("")
    L.append("## 一、角色表")
    L.append("")
    L.append("| 级 | 角色 | 出场集 | 出场场 | 台词 | 已登记 | 建议 |")
    L.append("|---|---|---:|---:|---:|---|---|")
    for g, name, ne, ns, nl, reg, vis, why, cid in rows:
        L.append("| %s | %s | %d | %d | %d | %s | %s |"
                 % (g, name, ne, ns, nl, "✅" if reg else "—", why))
    L.append("")
    L.append("分级口径：**A = 台词≥6 或 出场≥8 场 或 跨 3 集**；"
             "**B = 台词≥2 或 出场≥3 场**；其余为 C。")
    L.append("")
    L.append("四格板要花钱、占资产槽，所以 C 级不建板。B 级如果和主角同框多，"
             "可以共享主角锚点、不单独出板。")
    L.append("")
    L.append("## 二、每个人的提示词（%s）" % LAYOUTS[lay]["name"])
    L.append("")
    for g, name, ne, ns, nl, reg, vis, why, cid in need:
        fields = bible.entries.get(("人物", name), {})
        L.append("### %s（%s 级）" % (name, g))
        L.append("")
        L.append("- 出场：%d 集 / %d 场 / %d 句台词" % (ne, ns, nl))
        L.append("- 视觉设定：%s" % ("已登记，锚点会填进提示词" if reg else "**未登记**——先补条目再出图"))
        L.append("")
        if lay == "four-view":
            L.append(cast_prompt(name, fields, cfg, bible))
        else:
            c = _fig_ctx(name, fields, cfg, bible)
            _fit_outfit(c, _outfit_fields(root, name), lay)
            L.append(figure_prompt(c, lay))
        L.append("")
        if not reg:
            L.append("> ⚠ 该角色还没进视觉设定。先把锚点、服装八字段补进 `视觉设定.md`，"
                     "否则上面的 `【】` 填不出来，多集之间会变脸。")
            L.append("")
    L.append("## 三、下一步")
    L.append("")
    L.append("1. 补视觉设定：未登记的角色先进 `视觉设定.md`，写锚点与服装八字段")
    L.append("2. 填提示词：把每段里的 `【】` 换成具体值")
    L.append("3. 出图：挂 `22-model-matrix.md` 的路由——人物板用 Nano Banana Pro（一致性最强）")
    L.append("4. 回填：出的图进 `人物资产/`，`assets` 命令会把它们列进素材接线单")
    L.append("")

    L.append("## 四、提取来源与局限")
    L.append("")
    L.append("提取只认两个来源：")
    L.append("")
    L.append("1. 听觉轨里 `名字（语气）：台词` 格式的**说话人**")
    L.append("2. 画面轨里出现的、**视觉设定已登记**的人物名")
    L.append("")
    L.append("**提不到的情况**：剧本里出现了一个新角色，既没台词、也还没进视觉设定。")
    L.append("这类角色不是提取失败，是流程没走到位——先补 `## 人物 · X` 条目，再重跑本命令。")
    L.append("")
    L.append("不做人名猜测的理由：中文没有分词与词典，靠「X的」「X把手」这类模式猜出来的"
             "多是「白旧衬衫」「靠在桌后」这类噪声，误判比漏判更麻烦。")
    L.append("")

    dst.write_text("\n".join(L) + "\n", encoding="utf-8")
    out("")
    out("提取来源：听觉轨说话人 + 视觉设定已登记人物名。")
    out("若剧中有新角色既无台词也未登记，先补视觉设定条目再重跑。")
    out("已生成建卡清单：%s" % dst)
    return 0


# ---------------------------------------------------------------- reverse

IMG_MAGIC = ((b"\x89PNG", "png"), (b"\xff\xd8", "jpeg"),
             (b"GIF8", "gif"), (b"RIFF", "webp"))


def probe_image(path):
    """读图片尺寸，只用标准库。返回 (fmt, w, h) 或 None。"""
    try:
        data = open(path, "rb").read(512 * 1024)
    except OSError:
        return None
    fmt = None
    for magic, name in IMG_MAGIC:
        if data.startswith(magic):
            fmt = name
            break
    if not fmt:
        return None
    try:
        if fmt == "png":
            return (fmt, int.from_bytes(data[16:20], "big"),
                    int.from_bytes(data[20:24], "big"))
        if fmt == "jpeg":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    h = int.from_bytes(data[i + 5:i + 7], "big")
                    w = int.from_bytes(data[i + 7:i + 9], "big")
                    return (fmt, w, h)
                seg = int.from_bytes(data[i + 2:i + 4], "big")
                i += 2 + seg
            return (fmt, 0, 0)
        if fmt == "gif":
            return (fmt, int.from_bytes(data[6:8], "little"),
                    int.from_bytes(data[8:10], "little"))
    except (IndexError, ValueError):
        return (fmt, 0, 0)
    return (fmt, 0, 0)


def probe_video(path):
    """轻量解析 MP4/MOV：时长、分辨率、有无音轨。零依赖。"""
    try:
        f = open(path, "rb")
        size = os.path.getsize(path)
    except OSError:
        return None

    info = {"duration": 0.0, "w": 0, "h": 0, "audio": False, "ftyp": ""}

    def walk(off, end, depth=0):
        while off + 8 <= end and depth < 6:
            f.seek(off)
            head = f.read(8)
            if len(head) < 8:
                return
            bsize = int.from_bytes(head[0:4], "big")
            btype = head[4:8]
            if bsize == 1:
                ext = f.read(8)
                if len(ext) < 8:
                    return
                bsize = int.from_bytes(ext, "big")
                hdr = 16
            else:
                hdr = 8
            if bsize < hdr:
                return
            body = off + hdr
            if btype == b"ftyp":
                info["ftyp"] = f.read(8)[:4].decode("latin-1", "ignore")
            elif btype in (b"moov", b"trak", b"mdia", b"minf", b"stbl"):
                walk(body, min(off + bsize, end), depth + 1)
            elif btype == b"mvhd":
                f.seek(body)
                ver = f.read(1)[0]
                f.read(3)
                if ver == 1:
                    f.read(16)
                    ts = int.from_bytes(f.read(4), "big")
                    du = int.from_bytes(f.read(8), "big")
                else:
                    f.read(8)
                    ts = int.from_bytes(f.read(4), "big")
                    du = int.from_bytes(f.read(4), "big")
                if ts:
                    info["duration"] = du / ts
            elif btype == b"tkhd":
                # tkhd 布局：ver+flags(4) creation+mod(8|16) trackID+res(8)
                # duration(4|8) 保留+layer/alt/vol(16) matrix(36) width+height(8)
                f.seek(body)
                ver = f.read(1)[0]
                f.read(3)
                f.read(16 if ver == 1 else 8)      # creation + modification
                f.read(8)                          # track_ID + reserved
                f.read(8 if ver == 1 else 4)       # duration
                f.read(16)                         # reserved + layer/alt/volume
                f.read(36)                         # matrix
                w = int.from_bytes(f.read(4), "big") >> 16
                h = int.from_bytes(f.read(4), "big") >> 16
                if w and h:
                    info["w"], info["h"] = w, h
            elif btype == b"hdlr":
                f.seek(body + 8)
                if f.read(4) == b"soun":
                    info["audio"] = True
            off += bsize

    walk(0, size)
    f.close()
    return info


def cmd_reverse(args):
    """为图/视频生成反推工作表（骨架）。"""
    src = Path(args.source)
    if not src.exists():
        out("找不到文件：%s" % src)
        return 2

    ext = src.suffix.lower()
    is_video = ext in (".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv")
    L = []

    def add(*xs):
        for x in xs:
            L.append(x)

    add("# 反推工作表 · %s" % src.name, "",
        "> 按 `references/23-reverse-prompting.md` 的七步填。",
        "> **不要只描述画面**——每个要素都要归因并标置信度。", "")

    add("## 0. 探测结果", "")
    if is_video:
        vi = probe_video(src)
        if vi:
            add("| 项 | 值 |", "|---|---|",
                "| 时长 | %.1f 秒 |" % vi["duration"],
                "| 分辨率 | %dx%d |" % (vi["w"], vi["h"]),
                "| 音轨 | %s |" % ("有（需判断原生/后期）" if vi["audio"] else "无"),
                "| 容器 | %s |" % (vi["ftyp"] or ext), "")
            d = vi["duration"]
            if d:
                add("### 建议抽帧点（按动作节点，非固定间隔）", "", "```",
                    "首帧      0.0s",
                    "动作转折  约 %.1fs / %.1fs / %.1fs（按实际动作调整）"
                    % (d * 0.25, d * 0.5, d * 0.75),
                    "尾帧      %.1fs" % max(d - 0.05, 0), "```", "")
                if d >= 25:
                    add("**推断**：单段 ≥25 秒且连续，大概率 Seedance 2.5 / Wan 3.0。")
                elif d >= 12:
                    add("**推断**：12–15 秒档，Seedance 2.0 / Kling 3.0 / H3 都可能，"
                        "看有无原生音频与运镜复杂度再定。")
                elif d >= 8:
                    add("**推断**：8–12 秒档。可能是 Veo 3.1（上限 8s）、"
                        "或别的模型后剪过的片段。看有无硬切点。")
                else:
                    add("**推断**：短片，通常是多镜拼的，或某模型的下限档。")
        else:
            add("（无法解析容器，请手工填时长与分辨率）")
        add("")
    else:
        pi = probe_image(src)
        if pi:
            add("| 项 | 值 |", "|---|---|", "| 格式 | %s |" % pi[0])
            if pi[1]:
                add("| 尺寸 | %dx%d（比例 %.2f）|"
                    % (pi[1], pi[2], pi[1] / pi[2] if pi[2] else 0))
            add("| 文件大小 | %.0f KB |" % (src.stat().st_size / 1024), "")
            if pi[1] and pi[2]:
                r = pi[1] / pi[2]
                ar = "9:16" if abs(r - 9 / 16) < 0.02 else (
                     "16:9" if abs(r - 16 / 9) < 0.02 else (
                     "1:1" if abs(r - 1) < 0.02 else (
                     "4:3" if abs(r - 4 / 3) < 0.02 else (
                     "3:4" if abs(r - 3 / 4) < 0.02 else "非常规"))))
                add("**画幅**：约 %s" % ar, "")
        else:
            add("（无法识别图片头，请手工填）", "")

    add("## 1. 介质判断", "",
        "- 类型：概念设定图 / 电影剧照 / 插画 / 摄影合成 / 三维渲染",
        "- 依据：", "")

    add("## 2. 四层拆解", "", "### 叙事层")
    add("- 谁：", "- 在哪：", "- 做什么：",
        "- 情绪（写身体表现，不写形容词）：", "- 关系：", "")
    add("### 镜头层")
    add("- 景别：", "- 角度与机位高低：", "- 焦段感：", "- 景深：")
    if is_video:
        add("- **运镜（只填一种）**：", "- 运镜速度：")
    add("")
    add("### 光影层")
    add("- 光源方位（读鼻影/颈影/眼窝/高光，四处交叉验证）：")
    add("- 色温：", "- 光比（差几档）：", "- 硬软：", "- 轮廓光：")
    if is_video:
        add("- 光是否随时间变化：")
    add("")
    add("### 模型层")
    add("- 画幅：", "- 风格词根（三到五个词，不是句子）：",
        "- 参考槽位需求：", "- 排除项（正向穷举，不写「不要 X」）：", "")

    if is_video:
        add("### 时间层", "```",
            "0.0–__s  预备（      ）",
            "__–__s   动作（      ）",
            "__–__s   停滞（      ）",
            "__–__s   收（        ）", "```", "")
        add("### 声音层",
            "- 原生还是后期：",
            "- 音轨构成（环境/动作/人声/音乐 各占多少）：",
            "- 静默点：", "")

    add("## 3. 归因表", "",
        "| 要素 | 归因 | 置信度 | 依据 |", "|---|---|---|---|",
        "|  | 提示词 / 参考图 / 模型默认 | 高/中/低 |  |", "",
        "> 判据：异常性（同类图常见吗）、可描述性（能否精确短语定位）、一致性（是否稳定出现）。", "")

    add("## 4. 可复制提示词", "", "```text",
        "（按四层顺序组装。留 20% 给模型补，不要覆盖全部细节。）", "```", "")

    add("## 5. 待验证项", "", "（低置信度的猜测放这里，**不进正文**）", "", "- ", "")

    add("## 6. 复现记录", "", "| 轮次 | 改动 | 差异 | 结论 |",
        "|---|---|---|---|", "| 1 | 首跑 |  |  |", "")

    add("## 7. 反推不出来的三样", "",
        "- **参考图**：原文靠参考图锁的形象，文字替代不了 → 写「此处需参考图锁定」",
        "- **随机种子**：目标是「能出同类」，不是「一模一样」",
        "- **后期处理**：好到不像模型能做的（完美中文、精确排版、干净抠图）→ 大概率后期加的，别写进提示词",
        "")

    dst = Path(args.out) if args.out else (src.parent / ("反推-%s.md" % src.stem))
    dst.write_text("\n".join(L) + "\n", encoding="utf-8")
    out("已生成反推工作表：%s" % dst)
    out("下一步：按 23-reverse-prompting.md 的七步填。低置信项一定单列。")
    return 0


# ---------------------------------------------------------------- assets

def cmd_assets(args):
    """生成资产清单：图号 / 类型 / 名称 / 规格 / 状态。"""
    root, cfg = load_project(args.project)
    mode = cfg.get("spec", {}).get("asset_mode", "M1")
    files = scan_asset_dirs(root)
    bible = parse_bible(read_text(root / "视觉设定.md"))

    rows = []
    n = 0
    # 图号优先取条目里显式声明的「资产编号」，没有才按顺序补
    for (kind, name), fields in bible.entries.items():
        declared = fields.get("资产编号", "")
        if kind == "造型" and not declared:
            continue          # 没编号的造型不占图槽，靠换装模板派生
        n += 1
        m = re.search(r"(\d+)", declared)
        if m:
            n = int(m.group(1))
        spec = "—"
        f = None
        # 只在对应的类型目录里找。**不退回全目录**——
        # 「造型 · 林小雨-夜班」和「人物 · 林小雨」的板常同名，
        # 全目录匹配会让人物四格板冒充服装板，把「待写」错报成「已有」。
        want = {"人物": "人物", "造型": "服装", "地点": "场景",
                "道具": "道具", "武器": "武器"}.get(kind, "")
        if want:
            for cand in files:
                if want in cand.parent.name and name in cand.stem:
                    f = cand
                    break
        elif files:
            # 未知类型才退回全目录
            for cand in files:
                if name in cand.stem:
                    f = cand
                    break
        if f:
            txt = read_text(f)
            if "Costume Sheet" in txt or "服装设定图" in txt:
                spec = "服装板"
            elif "全图共 9 格" in txt:
                spec = "九宫格"
            elif "全图共 4 格" in txt:
                spec = "四格板"
        rows.append((n, kind, name, spec,
                     "✅ 已有提示词" if f else "⏳ 待写提示词"))

    out("资产清单 · %s · 素材形态 %s" % (cfg.get("title", "未命名"), mode))
    out("")
    if not rows:
        out("  视觉设定里还没有条目。先写 视觉设定.md。")
        return 1
    rows.sort(key=lambda r: r[0])
    out("  %-4s %-6s %-16s %-10s %s" % ("图号", "类型", "名称", "规格", "状态"))
    for n, kind, name, spec, st in rows:
        out("  图%-3d %-6s %-16s %-10s %s" % (n, kind, name, spec, st))
    out("")
    ready = sum(1 for r in rows if r[4].startswith("✅"))
    out("合计 %d 项，已备提示词 %d 项。" % (len(rows), ready))
    if mode == "M1":
        out("")
        out("M1 形态：上表即《素材接线单》。拿提示词去平台出图后，按图号挂载即可，")
        out("不需要把图交回项目。")
    elif mode == "M0":
        out("")
        out("M0 形态：提示词里不写图号，一致性靠文字锁。上表仅供你自查。")
    return 0


# ---------------------------------------------------------------- board

BOARD_CSS = """
:root{--paper:#f7f4ee;--ink:#1c2430;--muted:#6b7280;--line:#e2ddd3;
--ok:#2f7d5d;--warn:#b4762a;--bad:#b23a3a;--accent:#2b6cb0}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
line-height:1.65;font-size:15px}
.wrap{max-width:1080px;margin:0 auto;padding:48px 28px 80px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:.5px}
.sub{color:var(--muted);font-size:13px;margin-bottom:32px}
h2{font-size:16px;margin:36px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.card .k{color:var(--muted);font-size:12px;margin-bottom:4px}
.card .v{font-size:19px;font-weight:600}
.gates{background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.sum{font-size:12.5px;font-weight:400;color:var(--muted);margin-left:8px}
.gate{display:flex;gap:12px;padding:10px 16px;border-bottom:1px solid var(--line);
font-size:13.5px;align-items:flex-start}
.gate:last-child{border-bottom:none}
.tag{font-family:ui-monospace,Menlo,monospace;font-size:11px;padding:1px 6px;border-radius:3px;
flex:none;margin-top:2px}
.pass{color:var(--ok);background:#eaf4ef}
.fail{color:var(--bad);background:#faeaea}
.warn{color:var(--warn);background:#fbf2e4}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13px;
border:1px solid var(--line);border-radius:8px;overflow:hidden}
th{background:#f2eee6;text-align:left;padding:9px 12px;font-weight:600;font-size:12.5px;
color:#4b5563;white-space:nowrap}
td{padding:9px 12px;border-top:1px solid var(--line);vertical-align:top}
td.id{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--accent);white-space:nowrap}
.dur{font-variant-numeric:tabular-nums;color:var(--muted);white-space:nowrap;width:64px}
.bar{height:26px;background:#fff;border:1px solid var(--line);border-radius:6px;
display:flex;overflow:hidden;margin-top:8px}
.bar i{display:block;height:100%}
.note{color:var(--muted);font-size:12.5px;margin-top:10px}
"""


def _tension_svg(points, width=680, height=150):
    """points: [(场号, 张力0-10, 时长秒)]。按累计时长铺 x 轴，能看出「连续多久在低位」。"""
    pts = [p for p in points if p[1] is not None]
    if not pts:
        return ""
    total = sum(max(0.1, p[2]) for p in pts) or 1
    pl, pr, pt, pb = 30, 14, 16, 30
    w, h = width - pl - pr, height - pt - pb

    def X(t):
        return pl + t / total * w

    def Y(v):
        return pt + (10 - max(0, min(10, v))) / 10.0 * h

    s = ['<svg viewBox="0 0 %d %d" width="100%%" style="max-width:%dpx;height:auto" '
         'role="img" aria-label="情绪曲线">' % (width, height, width)]
    for v in (0, 5, 10):
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e2ddd3" stroke-width="1"/>'
                 % (pl, Y(v), width - pr, Y(v)))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#6b7280" text-anchor="end">%d</text>'
                 % (pl - 6, Y(v) + 3, v))
    # 低位警戒带（0~3）
    s.append('<rect x="%d" y="%.1f" width="%d" height="%.1f" fill="#b23a3a" opacity="0.05"/>'
             % (pl, Y(3), w, Y(0) - Y(3)))

    acc, coords = 0.0, []
    for i, (label, v, d) in enumerate(pts):
        x = X(acc + max(0.1, d) / 2)
        coords.append((x, Y(v), label, v))
        acc += max(0.1, d)
    path = " ".join("%s%.1f,%.1f" % ("M" if i == 0 else "L", x, y)
                    for i, (x, y, _, _) in enumerate(coords))
    s.append('<path d="%s" fill="none" stroke="#b23a3a" stroke-width="2" '
             'stroke-linejoin="round"/>' % path)
    s.append('<path d="%s L%.1f,%.1f L%.1f,%.1f Z" fill="#b23a3a" opacity="0.08"/>'
             % (path, coords[-1][0], Y(0), coords[0][0], Y(0)))
    peak = max(c[3] for c in coords)
    for x, y, label, v in coords:
        r = 4 if v == peak else 3
        s.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="%s" stroke="#fff" stroke-width="1.5"/>'
                 % (x, y, r, "#b23a3a" if v == peak else "#6b7280"))
        s.append('<text x="%.1f" y="%.1f" font-size="10" fill="#6b7280" text-anchor="middle">%s</text>'
                 % (x, height - 8, label.replace("EP001-", "")))
    s.append("</svg>")
    return "".join(s)


def _content_sig(root, items):
    """内容指纹：项目文件内容 + 检查项状态。

    用途不是防伪，是**可证伪**——同一份文件复现一次，指纹应完全相同。
    模型编造的输出大概率对不上这个值，用户复现一次就能识破。
    """
    h = hashlib.sha256()
    rp = Path(root).resolve()
    h.update(str(rp).encode("utf-8", "ignore"))
    files = []
    for pat in ("*.md", "*.json"):
        files.extend(sorted(rp.glob(pat)))
        files.extend(sorted(rp.glob("剧集/*/" + pat)))
        files.extend(sorted(rp.glob("*/*" + ".md")))
    for f in files[:60]:
        try:
            h.update(f.name.encode("utf-8", "ignore"))
            h.update(f.read_bytes())
        except OSError:
            continue
    for g, code, status, msg, where in items:
        h.update(("%s|%s|%s;" % (code, status, msg)).encode("utf-8", "ignore"))
    return h.hexdigest()[:8]


def _jaccard(a, b):
    sa, sb = set(a or ""), set(b or "")
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


PARADIGM = {
    "A": ("结构化分段", "分段 + 时间轴 + 分字段。写清楚每段几秒、镜头怎么动。",
          "Seedance / H3 / 可灵 / 万相 / Vidu"),
    "B": ("自然语言散文", "一段连续描述，像给摄影师讲戏。不写字段名，不写参数。",
          "Veo / Runway / Luma / Pika / 混元 / Seedream"),
    "C": ("标签堆叠", "逗号分隔的关键词 + 权重，越靠前越重。",
          "Midjourney / Flux / SD / Ideogram / Recraft"),
    "D": ("指令式编辑", "保持什么 + 只改什么。改图比重新生成稳。",
          "GPT Image 2 / Nano Banana Pro / Flux Kontext"),
    "E": ("对话式迭代", "先给一版，再逐轮追加修改。",
          "Gemini Omni / 新一代对话式生成"),
}


def cmd_model(args):
    """模型档案：列表 / 详情 / 当前项目适配建议。"""
    if args.list or not args.show:
        if args.show:
            pass
        else:
            for kind in ("video", "image"):
                rows = [(k, v) for k, v in MODEL_PROFILE.items() if v["kind"] == kind]
                out("── %s（%d） ──" % ("视频" if kind == "video" else "图像", len(rows)))
                out("%-16s %-8s %-4s %-6s %-5s %s"
                    % ("模型", "范式", "上限", "参考图", "音频", "厂商"))
                for k, v in rows:
                    out("%-16s %-8s %-4s %-6d %-5s %s%s"
                        % (k, v["paradigm"], ("%ds" % v["dur"]) if v["dur"] else "—",
                           v["refs"], "有" if v["audio"] else "—", v["vendor"],
                           "" if v["alive"] else "  ⚠ 已停服"))
                out("")
            out("范式说明：")
            for k, (nm, desc, who) in PARADIGM.items():
                out("  %s %-8s %s" % (k, nm, desc))
                out("     常见：%s" % who)
            out("")
            out("详情：python scripts/cd.py model <模型名>")
            return 0

    v = model_profile(args.show)
    if not v:
        out("没登记这个模型：%s" % args.show)
        out("用 `cd.py model --list` 看全部；要加新模型改 scripts/cd.py 的 MODEL_PROFILE")
        return 1

    nm, desc, who = PARADIGM[v["paradigm"]]
    out("%s · %s" % (args.show, v["vendor"]))
    out("  类型：%s   范式：%s（%s）" % ("视频" if v["kind"] == "video" else "图像",
                                    v["paradigm"], nm))
    if v["dur"]:
        out("  单段上限：%ds   参考图上限：%d   原生音频：%s"
            % (v["dur"], v["refs"], "有" if v["audio"] else "无"))
    else:
        out("  参考图上限：%d   原生音频：%s" % (v["refs"], "有" if v["audio"] else "无"))
    out("  画幅：%s" % v["aspect"])
    out("  状态：%s" % ("在服役" if v["alive"] else "已停服，须迁移"))
    if v.get("note"):
        out("  备注：%s" % v["note"])
    if v.get("aliases"):
        out("  别名：%s" % "、".join(v["aliases"]))
    out("")
    out("  写法要点：%s" % desc)
    out("  同类模型：%s" % who)
    out("")
    if v["kind"] == "video":
        out("  骨架：见 references/29-model-adapters.md 第三节（范式 %s）" % v["paradigm"])
    else:
        out("  骨架：见 references/29-model-adapters.md 第四节（范式 %s）" % v["paradigm"])
    return 0


def cmd_lines(args):
    """台词七维诊断：①② 自动判，③⑥ 给可疑标记，④⑤⑦ 输出空表让人填。"""
    root, cfg = load_project(args.project)
    ep = root / "剧集" / args.episode
    script = parse_script(read_text(ep / "剧本.md"))
    rows = list(script.lines)
    if not rows:
        out("这集没解析到台词。检查听觉轨格式（S11）：`- 名字（语气）：台词`")
        return 2

    line_max = tune(cfg, "line_max", LINE_MAX_CHARS)
    lens = [cn_len(r[3]) for r in rows]
    out("台词诊断 · %s" % args.episode)
    out("  %d 句 / %d 字 / 平均 %.1f 字 · 最长 %d 字 · 最短 %d 字"
        % (len(rows), sum(lens), sum(lens) / len(lens), max(lens), min(lens)))
    out("")

    long_, notone, echo = [], [], []
    prev = None
    for i, (sid, who, tone, text) in enumerate(rows, 1):
        if cn_len(text) > line_max:
            long_.append((i, sid, who, cn_len(text), text))
        if not tone.strip():
            notone.append((i, sid, who, text))
        if prev and _jaccard(prev[3], text) >= 0.6:
            echo.append((i, sid, who, text, prev[3]))
        prev = (sid, who, tone, text)

    def title(s):
        out(s)

    if long_:
        title("✗ 超长 %d 句（上限 %d 字）" % (len(long_), line_max))
        for i, sid, who, n, txt in long_[:6]:
            out("   #%d %s %s %d 字「%s」" % (i, sid, who, n, txt))
        for i, sid, who, n, txt in long_[:6]:
            out("   → 砍到 %d 字以内，或拆成两句中间插一个动作" % line_max)
        out("")
    if notone:
        title("! 缺语气位 %d 句" % len(notone))
        for i, sid, who, txt in notone[:6]:
            out("   #%d %s %s「%s」" % (i, sid, who, txt))
        out("")
    if echo:
        title("! 疑似回声 %d 句（与上一句字面重叠 ≥60%）" % len(echo))
        for i, sid, who, txt, last in echo[:6]:
            out("   #%d %s「%s」 ← 上一句「%s」" % (i, who, txt, last[:14]))
        out("   → 回声句不给新信息。改成一个动作，或换成相反的话")
        out("")

    # ⑥ 人物辨识：句长指纹
    by = {}
    for sid, who, tone, text in rows:
        by.setdefault(who, []).append(cn_len(text))
    if len(by) >= 2:
        stat = sorted(((k, sum(v) / len(v), len(v)) for k, v in by.items()),
                      key=lambda x: -x[2])
        title("⑥ 人物句长指纹")
        for who, avg, n in stat[:6]:
            out("   %-6s %.1f 字/句（%d 句）" % (who, avg, n))
        top = stat[:2]
        if top[0][2] >= 2 and top[1][2] >= 2 and abs(top[0][1] - top[1][1]) < 2:
            out("   ⚠ %s 与 %s 平均句长只差 %.1f 字 —— 靠句长分不开，需要别的指纹"
                "（口头禅/称呼/回避方式）" % (top[0][0], top[1][0],
                                         abs(top[0][1] - top[1][1])))
        out("")

    out("七维打分（①②已自动判，③④⑤⑥⑦请人工填 1~5 分）")
    out("")
    out("| # | 场次 | 角色 | 台词 | ①长度 | ②语气 | ③信息 | ④推进 | ⑤潜台 | ⑥辨识 | ⑦可演 |")
    out("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, (sid, who, tone, text) in enumerate(rows, 1):
        a = "✗" if cn_len(text) > line_max else "✓"
        b = "✓" if tone.strip() else "✗"
        out("| %d | %s | %s | %s | %s | %s |  |  |  |  |  |"
            % (i, sid.replace("EP001-", ""), who, text.replace("|", "/"), a, b))
    out("")
    out("判读：①②有 ✗ 先改，别急着打分。③≤2 是水词，④≤2 是描述不是推进，")
    out("     ⑤≤2 说明说的就是想的，⑥≤2 换个人说也一样，⑦≤2 配不上动作。")
    out("方法见 references/03-script.md 第三节 3.0–3.7。")
    return 0


def cmd_ledger(args):
    """连续性台账：生成骨架 / 校验 / 看摘要。"""
    root, cfg = load_project(args.project)
    path = _ledger_path(root)
    eps = find_episodes(root)

    if args.check:
        rep = check_project(root, only="L")
        for g, c, status, msg, where in rep.items:
            out("%-5s %-4s %s%s" % (c, status, msg, ("（%s）" % where) if where else ""))
        return 1 if rep.failed else 0

    if args.init:
        if path.exists() and not args.force:
            out("台账已存在：%s" % path)
            out("要重建加 --force（会覆盖，旧内容不保留）")
            return 0
        first, cnt = {}, {}
        for d in eps:
            no = _ep_no(d.name)
            sc = parse_script(read_text(d / "剧本.md"))
            for sid, who, tone, text in sc.lines:
                first.setdefault(who, no)
                cnt[who] = cnt.get(who, 0) + 1
        bible = parse_bible(read_text(root / "视觉设定.md"))
        chars = [k[1] for k in bible.entries if k[0] == "人物"]
        props = [k[1] for k in bible.entries if k[0] == "道具"]
        for who in first:
            if who not in chars and not any(k in who for k in NON_PERSON_VOICE):
                chars.append(who)

        L = ["# 连续性台账 · %s" % cfg.get("title", "未命名项目"), "",
             "> 每集写前读账、写后更新。方法与取舍见 references/19-consistency-playbook.md 第三·补节。", "",
             "---", "", "## ① 伏笔账", "",
             "| ID | 伏笔内容 | 埋于 | 拟收于 | 状态 | 收法 / 备注 |",
             "|---|---|---:|---:|---|---|",
             "<!-- 每集规划时登记新伏笔。状态：埋 / 养 / 收 / 弃 -->", "",
             "## ② 人物账", "",
             "| 角色 | 首次出场 | 当前状态 | 与主角关系现值 | 最后变动集 | 变动事件 |",
             "|---|---:|---|---|---:|---|"]
        for c in chars:
            L.append("| %s | %d | 活着 |  |  |  |" % (c, first.get(c, 1)))
        L += ["", "<!-- 死亡的角色，从该集之后不得再有台词；回忆闪回要在变动事件里写「闪回」 -->", "",
              "## ③ 道具状态账", "",
              "| 道具 | 首次出现集 | 持有者 | 当前状态 | 变动集 |",
              "|---|---:|---|---|---:|"]
        for p_ in props:
            L.append("| %s | 1 |  |  |  |" % p_)
        L += ["", "<!-- 关键道具每次易手/损毁/出示都记一行；首次出现集之后的集才能被引用 -->", "",
              "## ④ 世界观规则账", "",
              "| 规则 | 类别 | 确立集 | 引用集 | 是否被违反 |",
              "|---|---|---:|---|---|",
              "<!-- 重生/系统/规则怪谈类必立：能力边界、代价、禁忌各一行 -->", "",
              "台词统计（便于核人物账）：", ""]
        for who, n in sorted(cnt.items(), key=lambda x: -x[1]):
            L.append("- %s：首次第 %d 集，共 %d 句" % (who, first[who], n))
        path.write_text("\n".join(L) + "\n", encoding="utf-8")
        out("已生成 %s" % path)
        out("  人物 %d 位（按首次出场集填好）/ 道具 %d 件" % (len(chars), len(props)))
        out("  下一步：补关系现值、道具持有者、伏笔与规则；伏笔账空着等于没建账")
        return 0

    # 默认：摘要
    if not path.exists():
        out("还没有台账：%s" % path)
        out("生成骨架：python scripts/cd.py ledger <项目> --init")
        return 0
    led = parse_ledger(read_text(path))
    open_fb = [r for r in led["foreshadow"]
               if (r.get("状态") or "").strip() not in ("收", "弃")]
    dead = [r for r in led["characters"] if (r.get("当前状态") or "").strip() == "死亡"]
    out("台账 · %s" % path.name)
    out("  伏笔 %d 条（未收 %d）· 人物 %d 位（死亡 %d）· 道具 %d 件 · 规则 %d 条"
        % (len(led["foreshadow"]), len(open_fb), len(led["characters"]),
           len(dead), len(led["props"]), len(led["rules"])))
    for r in open_fb[:5]:
        out("    %s %s（埋 %s → 拟收 %s）"
            % (r.get("ID", "?"), (r.get("伏笔内容") or "")[:16],
               r.get("埋于", "?"), r.get("拟收于", "?")))
    if not led["foreshadow"]:
        out("  ⚠ 伏笔账是空的——多集项目不记伏笔，等于没有台账")
    out("")
    out("校验：python scripts/cd.py ledger <项目> --check")
    return 0


def cmd_bench(args):
    """同口径对比：把本项目的四项指标，跟对标数据并排放。"""
    root, cfg = load_project(args.project)
    ep = root / "剧集" / args.episode
    shots = parse_storyboard(read_text(ep / "分镜.md"))
    script = parse_script(read_text(ep / "剧本.md"))
    if not shots:
        out("分镜里没有镜头，先写 剧集/%s/分镜.md" % args.episode)
        return 2

    dur = sum(float(re.sub(r"[^\d.]", "", s.get("时长")) or 0) for s in shots)
    n_shot = len(shots)
    lines = list(script.lines)
    n_line = len(lines)
    chars = sum(cn_len(x[3]) for x in lines)

    mine = dict(
        sec=dur,
        shots=n_shot,
        shot_len=(dur / n_shot) if n_shot else 0,
        lines=n_line,
        chars=chars,
        density=(chars / dur) if dur else 0,
        lines_per_shot=(n_line / n_shot) if n_shot else 0,
    )

    ref = {}
    if args.sec:
        ref["sec"] = args.sec
    if args.shots:
        ref["shots"] = args.shots
    if args.chars:
        ref["chars"] = args.chars
        ref["density"] = args.chars / args.sec if args.sec else 0
    if args.lines:
        ref["lines"] = args.lines
    if args.sec and args.shots:
        ref["shot_len"] = args.sec / args.shots
    if args.sec and args.lines:
        ref["lines_per_shot"] = args.lines / args.shots if args.shots else 0

    if not ref:
        out("没给对标数据。示例：")
        out("  python scripts/cd.py bench ./my-drama --sec 96 --shots 24 --chars 268")
        out("")
        out("本项目当前：")
        out("  %s · %.1fs · %d 镜 · 平均 %.2fs/镜 · %d 句 / %d 字 · 对白密度 %.2f 字/秒"
            % (args.episode, mine["sec"], mine["shots"], mine["shot_len"],
               mine["lines"], mine["chars"], mine["density"]))
        return 0

    rows = [
        ("集时长", "sec", "%.1fs", 0.20),
        ("镜数", "shots", "%d", 0.20),
        ("平均镜长", "shot_len", "%.2fs", 0.20),
        ("台词句数", "lines", "%d", 0.25),
        ("台词字数", "chars", "%d", 0.25),
        ("对白密度", "density", "%.2f 字/秒", 0.20),
        ("每镜句数", "lines_per_shot", "%.2f", 0.25),
    ]

    out("同口径对比 · %s" % args.episode)
    out("")
    out("%-10s %12s %12s %10s  %s" % ("指标", "本项目", "对标", "偏差", "判读"))
    out("-" * 66)
    flags = []
    for label, key, fmt, tol in rows:
        if key not in ref:
            continue
        a, b = mine[key], ref[key]
        if not b:
            continue
        diff = (a - b) / b
        verdict = "同档"
        if abs(diff) > tol:
            verdict = "偏高" if diff > 0 else "偏低"
            flags.append((label, verdict, diff))
        out("%-10s %12s %12s %9.0f%%  %s"
            % (label, fmt % a, fmt % b, diff * 100, verdict))
    out("")

    if not flags:
        out("全部落在 ±20%~25% 容差内，与对标同档。")
    else:
        out("需要能说出理由的三项以内：")
        tips = {
            "平均镜长": ("镜头偏长，节奏容易拖", "切得太碎，观众跟不上"),
            "对白密度": ("台词太满，配音会赶词、字幕会截断", "台词太空，要靠视觉信息补"),
            "每镜句数": ("一镜多句，口型与断句都会崩", "无台词镜偏多，检查是不是在拖"),
            "集时长": ("超平台上限，或内容量偏多", "信息量可能不够，观众觉得水"),
            "镜数": ("镜头密度高于对标，注意单镜信息量", "镜头数不足，可能一镜塞太多事"),
            "台词字数": ("台词量偏大", "台词量偏小"),
            "台词句数": ("句子偏多，平均句长会变短", "句子偏少，单句偏长"),
        }
        for label, verdict, diff in flags[:5]:
            hi, lo = tips.get(label, ("偏高", "偏低"))
            out("  · %s %s %.0f%% —— %s" % (label, verdict, abs(diff) * 100,
                                            hi if verdict == "偏高" else lo))
    out("")
    out("容差内不改；超容差先写理由，别急着改数。见 references/28-benchmark-recon.md")
    return 0


def cmd_board(args):
    root, cfg = load_project(args.project)
    spec = cfg.get("spec", {})
    eps = find_episodes(root)

    rows, gate_rows, totals = [], [], []
    for epdir in eps:
        if args.episode and epdir.name != args.episode:
            continue
        shots = parse_storyboard(read_text(epdir / "分镜.md"))
        script = parse_script(read_text(epdir / "剧本.md"))
        dur = sum(float(re.sub(r"[^\d.]", "", s.get("时长")) or 0) for s in shots)
        totals.append((epdir.name, len(script.scenes), len(shots), dur))
        for sh in shots:
            rows.append((epdir.name, sh))

    rep = check_project(root) if args.with_check else None

    h = []
    h.append("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">")
    h.append("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
    h.append("<title>%s · 制作看板</title><style>%s</style></head><body><div class=\"wrap\">"
             % (cfg.get("title", "漫剧"), BOARD_CSS))
    h.append("<h1>%s</h1>" % cfg.get("title", "未命名项目"))
    tgt = spec.get("episode_targets") or {}
    tgt_txt = ("目标 " + " / ".join("%s %ss" % (k, v) for k, v in tgt.items())) if tgt \
        else ("目标单集 %ss" % spec.get("episode_duration_sec", "?"))
    h.append("<div class=\"sub\">%s · 画幅 %s · %s · %s</div>"
             % (spec.get("form", "未设形态"), spec.get("aspect_ratio", "?"),
                spec.get("target_model", "未设模型"), tgt_txt))

    total_shots = sum(t[2] for t in totals)
    total_dur = sum(t[3] for t in totals)
    h.append("<div class=\"cards\">")
    for k, v in (("集数", len(totals)), ("总镜数", total_shots),
                 ("总时长", "%.0fs" % total_dur),
                 ("平均镜长", "%.1fs" % (total_dur / total_shots if total_shots else 0)),
                 ("素材形态", spec.get("asset_mode", "M1"))):
        h.append("<div class=\"card\"><div class=\"k\">%s</div><div class=\"v\">%s</div></div>" % (k, v))
    h.append("</div>")

    if rep:
        # 分组统计：先给一眼能看的总账，再列具体问题
        from collections import Counter
        stat = {}
        for g, c, status, msg, where in rep.items:
            d = stat.setdefault(g, {"n": 0, "bad": 0})
            d["n"] += 1
            if status in ("FAIL", "WARN"):
                d["bad"] += 1
        names = {"S": "结构", "R": "引用", "X": "执行", "A": "资产",
                 "C": "合规", "M": "模型", "Q": "条件"}
        h.append("<h2>机检结果 <span class=\"sum\">%d 项 · FAIL %d · WARN %d</span></h2>"
                 % (len(rep.items), len(rep.failed), len(rep.warned)))
        h.append("<div class=\"gates\">")
        for g in "SRXCAMQ":
            if g not in stat:
                continue
            d = stat[g]
            cls = "pass" if d["bad"] == 0 else "warn"
            h.append("<div class=\"gate\"><span class=\"tag %s\">%s</span>"
                     "<span>%s %d/%d</span></div>"
                     % (cls, g, names.get(g, g), d["n"] - d["bad"], d["n"]))
        h.append("</div>")

        bad = [i for i in rep.items if i[2] in ("FAIL", "WARN")]
        if bad:
            h.append("<div class=\"gates\">")
            for g, c, status, msg, where in bad:
                cls = {"FAIL": "fail", "WARN": "warn"}.get(status, "warn")
                h.append("<div class=\"gate\"><span class=\"tag %s\">%s%s</span>"
                         "<span>%s%s</span></div>"
                         % (cls, status, c, msg, ("（%s）" % where) if where else ""))
            h.append("</div>")

    h.append("<h2>分集节奏</h2><div class=\"gates\">")
    for name, nsc, nsh, d in totals:
        h.append("<div class=\"gate\"><span class=\"tag pass\">%s</span>"
                 "<span>%d 场 · %d 镜 · 合计 %.1fs · 平均 %.1fs/镜</span></div>"
                 % (name, nsc, nsh, d, d / nsh if nsh else 0))
    h.append("</div>")

    # 情绪曲线：只在剧本标了张力时出现
    tens = []
    for epdir in eps:
        if args.episode and epdir.name != args.episode:
            continue
        sc = parse_script(read_text(epdir / "剧本.md"))
        for s_ in sc.scenes:
            if s_.get("tension") is not None:
                # x 轴用「画面轨条数 × 3 秒」当权重，够表示每场在全片里的占比
                tens.append((s_["id"], s_["tension"], max(1, len(s_["visual"])) * 3))
    if tens:
        h.append("<h2>情绪曲线 <span class=\"sum\">%d 场有张力标记</span></h2>" % len(tens))
        h.append("<div class=\"card\">%s</div>" % _tension_svg(tens))
        h.append("<div class=\"note\">标法：场次标题后加「（张力 7）」，0~10。"
                 "曲线中段连续两场低于 3 就是塌陷区。</div>")

    # 资产清单
    asset_files = scan_asset_dirs(root)
    if asset_files:
        h.append("<h2>资产清单</h2><div class=\"gates\">")
        for f in asset_files:
            txt = read_text(f)
            kind = f.parent.name
            spec = ""
            if "Costume Sheet" in txt or "服装设定图" in txt:
                spec = "服装板"
            elif "全图共 9 格" in txt:
                spec = "九宫格"
            elif "全图共 4 格" in txt:
                spec = "四格板"
            chars = len(re.findall(r"[\u4e00-\u9fa5]", txt))
            h.append("<div class=\"gate\"><span class=\"tag pass\">%s</span>"
                     "<span>%s%s · 提示词约 %d 字</span></div>"
                     % (kind, f.stem, ("· " + spec) if spec else "", chars))
        h.append("</div>")

    h.append("<h2>分镜表</h2><table><tr><th>镜号</th><th>时长</th><th>景别/角度</th>"
             "<th>职责</th><th>动作链</th></tr>")
    for epname, sh in rows:
        h.append("<tr><td class=\"id\">%s</td><td class=\"dur\">%s</td><td>%s / %s</td>"
                 "<td>%s</td><td>%s</td></tr>"
                 % (sh.id, sh.get("时长", ""), sh.get("景别", ""), sh.get("角度", ""),
                    sh.get("职责", ""), sh.get("唯一动作", "")))
    h.append("</table>")
    h.append("<div class=\"note\">本页由 scripts/cd.py board 生成，数据源为各集 分镜.md。"
             "改内容请改 Markdown，不要改本页。</div>")
    h.append("</div></body></html>")

    outp = root / "制作看板.html"
    outp.write_text("\n".join(h), encoding="utf-8")
    out("已生成 %s（%d 集 / %d 镜）" % (outp, len(totals), total_shots))
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    if sys.version_info < MINIMUM_PYTHON:
        sys.stderr.write("需要 Python %d.%d+\n" % MINIMUM_PYTHON)
        return 2

    ap = argparse.ArgumentParser(prog="cd.py", description="漫剧制作工具链")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="建项目骨架")
    p.add_argument("dir")
    p.add_argument("--title", default="未命名漫剧")
    p.add_argument("--episodes", type=int, default=12)
    p.add_argument("--duration", type=int, default=120)
    p.add_argument("--aspect", default="9:16")
    p.add_argument("--form", default="")
    p.add_argument("--model", default="")
    p.add_argument("--platform", default="")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("selftest", help="机检自测：验证每项检查真能拦住问题")
    p.add_argument("--keep", action="store_true", help="保留临时样本便于排查")
    p.set_defaults(func=cmd_selftest)

    p = sub.add_parser("check", help="分层检查")
    p.add_argument("project")
    p.add_argument("--only", default="", help="S,R,X,C,A,M,Q 的任意组合")
    p.add_argument("--episode", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("estimate", help="时长折算")
    p.add_argument("script")
    p.add_argument("--cps", type=float, default=None,
                   help="字/秒；不填则按画幅取（9:16→5.8，16:9→5.0）")
    p.add_argument("--target", type=int, default=0)
    p.set_defaults(func=cmd_estimate)

    p = sub.add_parser("pack", help="生成投喂稿骨架")
    p.add_argument("project")
    p.add_argument("--episode", default="EP001")
    p.add_argument("--model", default="")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("cast", help="从剧本提取角色并出提示词骨架")
    p.add_argument("project")
    p.add_argument("--episode", default="", help="只处理某一集")
    p.add_argument("--layout", "-l", default="four-view",
                   help="图式代号（默认 four-view；见 figure --list）")
    p.set_defaults(func=cmd_cast)

    p = sub.add_parser("srt", help="从分镜生成字幕骨架（SRT）")
    p.add_argument("project")
    p.add_argument("--episode", default="EP001")
    p.add_argument("--out", default="", help="输出路径（默认 剧集/EP001/字幕.srt）")
    p.add_argument("--cps", type=float, default=None, help="字/秒，默认按画幅取")
    p.set_defaults(func=cmd_srt)

    p = sub.add_parser("figure", help="按图式出人物提示词（三视图/立绘/档案/表情/主图…）")
    p.add_argument("project")
    p.add_argument("--char", default="", help="角色名，留空则全部")
    p.add_argument("--layout", "-l", default="fullbody",
                   help="图式代号，见 --list；也认中文别名")
    p.add_argument("--ratio", default="", help="覆盖画幅，如 3:4")
    p.add_argument("--out", default="", help="输出文件或目录；留空打印到屏幕")
    p.add_argument("--list", action="store_true", help="列出全部图式")
    p.set_defaults(func=cmd_figure)

    p = sub.add_parser("reverse", help="为图/视频生成反推工作表")
    p.add_argument("source", help="图片或视频路径")
    p.add_argument("--out", default="", help="输出路径（默认与源同目录）")
    p.set_defaults(func=cmd_reverse)

    p = sub.add_parser("assets", help="生成资产清单")
    p.add_argument("project")
    p.set_defaults(func=cmd_assets)

    p = sub.add_parser("model", help="模型档案：列表 / 详情 / 范式")
    p.add_argument("show", nargs="?", default="", help="模型名，留空则列出全部")
    p.add_argument("--list", action="store_true")
    p.set_defaults(func=cmd_model)

    p = sub.add_parser("lines", help="台词七维诊断（逐句清单 + 打分表）")
    p.add_argument("project")
    p.add_argument("--episode", default="EP001")
    p.set_defaults(func=cmd_lines)

    p = sub.add_parser("ledger", help="连续性台账：生成/校验/摘要")
    p.add_argument("project")
    p.add_argument("--init", action="store_true", help="生成台账骨架")
    p.add_argument("--force", action="store_true", help="覆盖已有台账")
    p.add_argument("--check", action="store_true", help="只跑 L 组检查")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("bench", help="与对标同口径对比")
    p.add_argument("project")
    p.add_argument("--episode", default="EP001")
    p.add_argument("--sec", type=float, default=0, help="对标单集时长（秒）")
    p.add_argument("--shots", type=int, default=0, help="对标镜数")
    p.add_argument("--lines", type=int, default=0, help="对标台词句数")
    p.add_argument("--chars", type=int, default=0, help="对标台词总字数")
    p.set_defaults(func=cmd_bench)

    p = sub.add_parser("board", help="渲染看板")
    p.add_argument("project")
    p.add_argument("--episode", default="")
    p.add_argument("--with-check", action="store_true")
    p.set_defaults(func=cmd_board)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
