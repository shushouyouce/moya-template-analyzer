#!/usr/bin/env python3
"""Validate a member-facing Moya template introduction."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FIELDS = (
    "适用赛道",
    "目标人群",
    "内容平台",
    "内容形式",
    "使用阶段",
    "主要用途",
)

INTERNAL_PUBLIC_LEAKS = (
    "【使用难度】",
    "【合规等级】",
    "| 使用难度 |",
    "| 合规等级 |",
    "stage_primary",
    "risk_level",
    "threshold:",
    "confidence:",
)

ACQUISITION_PROCESS_LEAKS = (
    "这份素材",
    "用户提供",
    "采集载体",
    "完整录屏",
    "原作品本身",
    "额外证据",
)

BRAND = "—— 渡鸦科技社 · 墨鸦AI获客圈"
CTA = "觉得有用，顺手点个赞，转发到朋友圈留着。真要做这个赛道的时候，省得再到处找。"

CONTEXT_LEAKS = (
    "上一个模板",
    "前一个模板",
    "前面那个模板",
    "接着上面",
    "比上一个",
    "和前面那个",
    "再测试一个",
)

AI_CLICHES = (
    "该模板通过精准洞察",
    "具有较强传播价值和转化潜力",
    "形成完整闭环",
    "赋能",
    "适合所有行业",
)

FORBIDDEN_AFTER_BRAND = (
    "评论",
    "留言",
    "关注",
    "私信",
    "扣1",
    "进群",
)


def read_input(path: str | None, inline_text: str | None) -> str:
    if inline_text is not None:
        return inline_text
    if path:
        return Path(path).read_text(encoding="utf-8-sig")
    return sys.stdin.read()


def normalized_length(text: str) -> int:
    return len(text.replace("\r", "").strip())


def validate(text: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    size = normalized_length(text)
    if size > 1000:
        errors.append(f"全文{size}个字符，超过1000字符上限")

    if not re.search(r"^###\s+【[^｜】]+｜[^｜】]+｜[^｜】]+】.+", text, flags=re.MULTILINE):
        errors.append("标题不符合### 【对外赛道｜平台｜获客作用】模板名称")

    title_match = re.search(r"^###\s+(.+)$", text, flags=re.MULTILINE)
    if title_match and re.search(r"S[0-6]", title_match.group(1)):
        errors.append("对外标题不得出现S0-S6阶段编码")
    if re.search(r"(?<![A-Za-z0-9])S[0-6](?![A-Za-z0-9])", text):
        errors.append("会员发布版不得出现S0-S6阶段编码")

    for field in REQUIRED_FIELDS:
        if f"【{field}】" not in text:
            errors.append(f"缺少信息卡字段：{field}")

    for term in INTERNAL_PUBLIC_LEAKS:
        if term in text:
            errors.append(f"会员发布版泄露后台字段：{term}")

    for term in ACQUISITION_PROCESS_LEAKS:
        if term in text:
            errors.append(f"会员发布版泄露素材采集或分析过程：{term}")

    if BRAND not in text:
        errors.append("缺少固定品牌落款")
    if CTA not in text:
        errors.append("缺少或改动了固定点赞／朋友圈引导")

    if BRAND in text:
        tail = text.split(BRAND, 1)[1]
        for term in FORBIDDEN_AFTER_BRAND:
            if term in tail:
                errors.append(f"品牌落款后不得引导：{term}")

    for term in CONTEXT_LEAKS:
        if term in text:
            errors.append(f"模板没有独立成篇，出现上下文词：{term}")

    if "真正能复制" not in text and "可复制的结构" not in text:
        warnings.append("没有明确写出可复制结构")
    if "换到其他赛道" not in text and "迁移到" not in text:
        warnings.append("没有给出跨赛道迁移例子")
    if "风险提醒" not in text:
        errors.append("缺少风险提醒")

    for phrase in AI_CLICHES:
        if phrase in text:
            warnings.append(f"疑似AI套话：{phrase}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="UTF-8 Markdown file")
    parser.add_argument("--text", help="validate inline text instead of a file")
    args = parser.parse_args()

    text = read_input(args.path, args.text)
    errors, warnings = validate(text)

    print(f"characters: {normalized_length(text)} / 1000")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("result: FAIL")
        return 1
    print("result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
