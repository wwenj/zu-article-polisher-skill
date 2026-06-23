#!/usr/bin/env python3
"""Locate style and AI-flavor hints for Zu-style Chinese technical articles.

This script never rewrites text. It only reports deterministic structure errors
and candidate passages that the model should review before editing.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys
from pathlib import Path


@dataclass(frozen=True)
class PatternHint:
    pattern: str
    category: str
    message: str


PATTERN_HINTS: list[PatternHint] = [
    PatternHint(r"不是.*而是", "否定式排比", "检查是否为 AI 模板：不是...而是..."),
    PatternHint(r"不仅仅?.*(而是|更是)", "否定式排比", "检查是否为 AI 模板：不仅仅是...更是/而是..."),
    PatternHint(r"而不是", "否定式排比", "检查是否可以改成正向判断，避免模板对比"),
    PatternHint(r"不是", "否定式排比", "检查这个“不是”是否必要，避免重复模板化否定"),
    PatternHint(r"这篇文章不是想", "模板开场", "不要用“这篇文章不是想...”解释写作意图"),
    PatternHint(r"这篇文章.*想回答", "模板开场", "不要用“这篇文章想回答...”做 meta 开场"),
    PatternHint(r"本文将", "模板开场", "删除论文式开场，直接写判断"),
    PatternHint(r"到了.*到底.*是什么", "假问题", "把“到了...到底是什么”改成判断句"),
    PatternHint(r"真正.*拉开差距.*到底是什么", "假问题", "把“真正拉开差距的到底是什么”改成判断句"),
    PatternHint(r"这意味着什么", "假问题", "检查是否为段落间模板问题"),
    PatternHint(r"如果只看.*你会觉得", "模板转折", "检查是否为“如果只看...你会觉得...”式铺垫"),
    PatternHint(r"但如果.*(往下看|深入|顺着)", "模板转折", "检查是否为“但如果深入看...”式转折"),
    PatternHint(r"换句话说", "模板转折", "通常可以删除，让下一句直接成立"),
    PatternHint(r"过去比的是.*现在比的是", "阶段口号", "把“过去/现在比的是”改成当前判断标准"),
    PatternHint(r"现在比的是.{0,24}([0-9]+|[一二三四五六七八九十几])件事", "三件套", "检查是否为强行“三件事”结构"),
    PatternHint(r"主要有以下", "三件套", "检查是否为模板列表开头"),
    PatternHint(r"主要有[一二三四五六七八九十0-9]+[点项个]", "三件套", "检查是否为强行凑项"),
    PatternHint(r"可以从.*(维度|角度).*看", "三件套", "避免“几个维度/角度”式泛化框架"),
    PatternHint(r"大家最容易盯着", "人工标记高 AI 味", "不要用“大家最容易盯着...”做观点铺垫"),
    PatternHint(r"(模型名、参数、榜单和发布会|模型名.*参数.*榜单.*发布会)", "人工标记高 AI 味", "检查是否为模型名单/参数/榜单/发布会式模板开场"),
    PatternHint(r"(稳不稳|能不能|会不会|算不算|跑不跑|清不清楚)", "人工感叠词", "稳不稳/能不能/会不会这类叠词要谨慎，连续出现时 AI 味很重"),
    PatternHint(r"我的判断很(直接|扎心|现实)", "刻意拟人口吻", "不要用“我的判断很直接/扎心/现实”模仿人类语气"),
    PatternHint(r"相比较.*我更关心", "固定关注句式", "不要用“相比较...我更关心...”做高频模板转场"),
    PatternHint(r"我更关心这几个问题", "固定关注句式", "不要用“我更关心这几个问题”做固定转场"),
    PatternHint(r"可接入.*可上线.*可控成本", "密集排比", "可接入、可上线、可控成本这类排比过密，检查是否白皮书腔"),
    PatternHint(r"瞄准的是.*(可接入|可上线|可控成本)", "密集排比", "检查“瞄准的是...”是否为产品白皮书句式"),
    PatternHint(r"一方面.*另一方面", "过度平衡", "检查是否可以合并成一个更明确的判断"),
    PatternHint(r"已经从.*(进入|走向|转向)", "虚假跨度", "把“已经从...进入/走向/转向...”改成具体后果"),
    PatternHint(r"从.*转向.*", "虚假跨度", "检查“从...转向...”是否为抽象阶段变化"),
    PatternHint(r"从.*走向.*", "虚假跨度", "检查“从...走向...”是否为抽象阶段变化"),
    PatternHint(r"(标志着|见证了|体现了|证明了|奠定了|彰显了|凸显了).{0,40}(意义|价值|重要|关键|基础|作用)", "空泛意义升华", "检查是否把普通事实写成宏大意义"),
    PatternHint(r"(不断演变的格局|关键时刻|不可磨灭的印记|重要抓手|战略高地)", "空泛意义升华", "删除或改成具体事实/后果"),
    PatternHint(r"(确保|彰显|反映|象征|展示|凸显|体现).{0,50}(价值|意义|作用|联系|能力|重要性)", "句尾强行升华", "检查是否为句尾硬贴意义标签"),
    PatternHint(r"(专家认为|行业报告显示|观察者指出|有观点认为|业内普遍认为|多个来源表明)", "模糊归因", "需要具体来源或改成作者判断"),
    PatternHint(r"(无缝|直观|强大|充满活力|令人叹为观止|开创性|必备)", "宣传腔", "检查是否为宣传/广告腔"),
    PatternHint(r"(值得注意的是|综上所述|毋庸置疑|在当今快速发展的时代|深入探讨)", "AI 高频词", "删除或改成更直接的中文"),
    PatternHint(r"(赋能|闭环|降本增效|复杂格局|关键作用)", "AI 高频词", "检查是否为泛化业务黑话"),
    PatternHint(r"(尽管存在这些挑战|尽管.*面临.*挑战|未来展望|未来可期|迈出重要一步|继续追求卓越)", "套路化结尾", "改成具体结论、风险或下一步"),
    PatternHint(r"(当然|好问题|你说得完全正确|希望这对.*有帮助|如果你需要.*我可以)", "聊天残留", "删除聊天回复痕迹"),
    PatternHint(r"(截至.*知识截止|根据我最后的训练|基于可用信息|虽然具体细节有限)", "模型免责声明", "不要把模型免责声明留进文章"),
    PatternHint(r"LLM WIKI", "术语大小写", "统一写作：LLM Wiki"),
    PatternHint(r"(?<![A-Za-z])mcp(?![A-Za-z])", "术语大小写", "统一写作：MCP"),
]


def collect_outline(lines: list[str]) -> list[tuple[int, str, int]]:
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == "## 阅读大纲":
            start = idx + 1
            break
    if start is None:
        return []

    outline: list[tuple[int, str, int]] = []
    for i in range(start, len(lines)):
        line = lines[i].rstrip("\n")
        if line.startswith("## ") and i != start:
            break
        match = re.match(r"^(\d+)\.\s+(.+?)\s*$", line)
        if match:
            outline.append((int(match.group(1)), match.group(2), i + 1))
    return outline


def collect_body_sections(lines: list[str]) -> list[tuple[int, str, int]]:
    sections: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines, start=1):
        match = re.match(r"^##\s+(\d+)\.\s+(.+?)\s*$", line.rstrip("\n"))
        if match:
            sections.append((int(match.group(1)), match.group(2), i))
    return sections


def collect_paragraphs(lines: list[str]) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    buf: list[str] = []
    start_line = 0
    in_code = False

    for i, line in enumerate(lines, start=1):
        raw = line.rstrip("\n")
        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not raw.strip():
            if buf:
                paragraphs.append((start_line, " ".join(buf)))
                buf = []
                start_line = 0
            continue
        if raw.startswith("#"):
            if buf:
                paragraphs.append((start_line, " ".join(buf)))
                buf = []
                start_line = 0
            continue
        if start_line == 0:
            start_line = i
        buf.append(raw.strip())

    if buf:
        paragraphs.append((start_line, " ".join(buf)))
    return paragraphs


def text_len(text: str) -> int:
    cleaned = re.sub(r"[*_`#>\-\s，。！？、；：,.!?;:（）()\[\]【】“”\"']", "", text)
    return len(cleaned)


def strip_markdown(text: str) -> str:
    return re.sub(r"[*_`#>\[\]()]|!\S+", "", text)


def short_snippet(text: str, limit: int = 88) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def add_issue(
    issues: list[tuple[str, int | None, str, str | None]],
    level: str,
    line: int | None,
    message: str,
    snippet: str | None = None,
) -> None:
    issues.append((level, line, message, snippet))


def check_outline(
    lines: list[str],
    issues: list[tuple[str, int | None, str, str | None]],
) -> None:
    outline = collect_outline(lines)
    sections = collect_body_sections(lines)

    if outline and sections:
        if [(n, t) for n, t, _ in outline] != [(n, t) for n, t, _ in sections]:
            add_issue(issues, "ERROR", None, "Reading outline does not exactly match numbered body headings")
            for (on, ot, ol), (sn, st, sl) in zip(outline, sections):
                if (on, ot) != (sn, st):
                    add_issue(issues, "ERROR", ol, f"Outline item differs from body line {sl}: {on}. {ot} <> {sn}. {st}")
            if len(outline) != len(sections):
                add_issue(issues, "ERROR", None, f"Outline count {len(outline)} differs from body section count {len(sections)}")

    if sections:
        numbers = [n for n, _, _ in sections]
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            add_issue(issues, "ERROR", None, f"Section numbers are not continuous: {numbers}")


def check_lines(
    lines: list[str],
    issues: list[tuple[str, int | None, str, str | None]],
) -> None:
    blank_run = 0
    blank_start = 0
    in_code = False

    for i, line in enumerate(lines, start=1):
        raw = line.rstrip("\n")

        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        if raw.rstrip(" \t") != raw:
            add_issue(issues, "WARN", i, "Trailing whitespace")

        if raw == "":
            if blank_run == 0:
                blank_start = i
            blank_run += 1
        else:
            if blank_run > 2:
                add_issue(issues, "WARN", blank_start, f"Too many consecutive blank lines ({blank_run})")
            blank_run = 0

        for hint in PATTERN_HINTS:
            if re.search(hint.pattern, raw):
                add_issue(issues, "HINT", i, f"{hint.category}: {hint.message}", short_snippet(raw))

        if raw.count("**") % 2 == 1:
            add_issue(issues, "WARN", i, "Possibly unbalanced bold markers", short_snippet(raw))
        if raw.count("**") >= 6:
            add_issue(issues, "HINT", i, "粗体滥用: 一行内粗体过多，检查是否为机械强调", short_snippet(raw))
        if re.match(r"^\s*[-*]\s+\*\*[^*：:]{1,24}[：:]\*\*", raw):
            add_issue(issues, "HINT", i, "粗体小标题列表: 检查是否为 AI 式列表模板", short_snippet(raw))

    if blank_run > 2:
        add_issue(issues, "WARN", blank_start, f"Too many consecutive blank lines ({blank_run})")


def check_sentence_rhythm(
    lines: list[str],
    issues: list[tuple[str, int | None, str, str | None]],
) -> None:
    for start_line, paragraph in collect_paragraphs(lines):
        plain = strip_markdown(paragraph)
        sentences = [s.strip() for s in re.split(r"[。！？!?]+", plain) if text_len(s) >= 8]
        if len(sentences) < 3:
            continue
        lengths = [text_len(s) for s in sentences]
        for idx in range(len(lengths) - 2):
            triad = lengths[idx : idx + 3]
            if max(triad) - min(triad) <= 4 and sum(triad) / 3 >= 12:
                add_issue(
                    issues,
                    "HINT",
                    start_line,
                    "节奏过齐: 连续三个句子长度接近，检查是否像机器生成段落",
                    short_snippet(paragraph),
                )
                break


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_article_style.py <markdown-file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    issues: list[tuple[str, int | None, str, str | None]] = []

    check_outline(lines, issues)
    check_lines(lines, issues)
    check_sentence_rhythm(lines, issues)

    if not issues:
        print("OK: no deterministic style hints found")
        return 0

    print("Style hints for model review. Do not rewrite mechanically from this output.")
    for level, line, message, snippet in issues:
        where = f":{line}" if line is not None else ""
        print(f"{level}{where}: {message}")
        if snippet:
            print(f"  -> {snippet}")

    return 1 if any(level == "ERROR" for level, _, _, _ in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
