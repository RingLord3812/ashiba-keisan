"""Generate universal Web-Chat AI bundle (dist/ashiba-keisan-web-prompt.md) and llms.txt.

Usage:
    python scripts/build_web_bundle.py
    python scripts/build_web_bundle.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "ashiba-keisan"
RAW_BASE = "https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main"

REF_ORDER = [
    "wind_load.md",
    "wakugumi_ashiba.md",
    "tankan_issoku.md",
    "ashiba_uke_bracket.md",
    "tekkotsu_tsuri.md",
    "nitori_koudai.md",
]


def build_web_prompt() -> str:
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    # Remove YAML frontmatter for direct system-prompt usage
    parts = skill_text.split("---", 2)
    skill_body = parts[2].strip() if len(parts) == 3 else skill_text.strip()

    materials = json.loads((SKILL_DIR / "data" / "materials.json").read_text(encoding="utf-8"))
    wind = json.loads((SKILL_DIR / "data" / "wind_tables.json").read_text(encoding="utf-8"))

    out: list[str] = [
        "# 足場強度計算スキル (ashiba-keisan) — Web Chat AI 用スタンドアロン指示書",
        "",
        "> ChatGPT (Custom GPT / Projects)、Claude.ai (Projects)、Gemini Gems、NotebookLM 等の Web AI にそのまま貼り付け、またはナレッジファイルとしてアップロードして使用できます。",
        "> Python 実行環境（Code Interpreter 等）がある場合は、下記数式とカタログデータを用いて高精度に自動計算し、なければ各ステップを検算付きで `kgf/cm² (N/mm²)` 併記（$g=9.81$・有効数字3桁切上げ）で出力してください。",
        "",
        "---",
        "",
        skill_body,
        "",
    ]

    for ref_name in REF_ORDER:
        ref_text = (SKILL_DIR / "references" / ref_name).read_text(encoding="utf-8").strip()
        out.extend(["---", "", ref_text, ""])

    # Compact JIS/Kasetsu catalog appendix for Web AIs without file access
    out.extend(
        [
            "---",
            "",
            "# 付録：標準部材・地域風速データ抜粋（JSON 原本準拠）",
            "",
            "## 建枠・布枠・筋かい・梁枠・ジャッキベース",
            "```json",
            json.dumps(
                {
                    "frames": materials["frames"],
                    "ledgers": materials["ledgers"],
                    "braces": materials["braces"],
                    "beam_frames": materials["beam_frames"],
                    "jack_bases": materials["jack_bases"],
                    "wall_ties": materials["wall_ties"],
                    "suspension_chains": materials["suspension_chains"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## 単管・角パイプ・足場板・H形鋼・アンカー・コンクリート・溶接許容値",
            "```json",
            json.dumps(
                {
                    "single_pipes": materials["single_pipes"],
                    "plank_brackets": materials["plank_brackets"],
                    "square_pipes": materials["square_pipes"],
                    "planks": materials["planks"],
                    "timbers": materials["timbers"],
                    "h_beams": materials["h_beams"],
                    "anchor_bolts": materials["anchor_bolts"],
                    "concrete_grades": materials["concrete_grades"],
                    "weld_allowables": materials["weld_allowables"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## 47都道府県・地域別 基準風速 Vo / 台風時割増係数 Ke",
            "```json",
            json.dumps(wind["regions_v0"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(out).replace("\r\n", "\n")


def build_llms_txt() -> str:
    lines = [
        "# ashiba-keisan (足場強度計算スキル)",
        "",
        "> Universal AI Agent Skill and Python structural calculation engine for Japanese scaffolding and temporary structures (SUCCES Ver 4.11 / 仮設工業会 / AIJ).",
        "> Supports Frame Scaffolding (枠組足場), Single-Pipe One-Sided Bracket Scaffolding (単管一側ブラケット足場), Scaffold Support Cantilever Brackets (足場受ブラケット), Steel-Frame Suspended Scaffolding (鉄骨吊り足場), and Material Loading Platforms (荷取り構台).",
        "",
        "## Core Skill & Web Prompt",
        f"- [SKILL.md]({RAW_BASE}/skills/ashiba-keisan/SKILL.md): Concise agent workflow, CLI usage, and forbidden-error checklist.",
        f"- [Standalone Web-Chat Prompt Bundle]({RAW_BASE}/dist/ashiba-keisan-web-prompt.md): Single-file knowledge pack for ChatGPT, Claude.ai, Gemini Gems, and NotebookLM.",
        f"- [AGENTS.md]({RAW_BASE}/AGENTS.md): Universal repository instructions for coding agents.",
        "",
        "## Technical Reference Manuals (Japanese)",
        f"- [Wind Load & Wall Ties (仮設工業会)]({RAW_BASE}/skills/ashiba-keisan/references/wind_load.md)",
        f"- [Frame Scaffolding (枠組足場)]({RAW_BASE}/skills/ashiba-keisan/references/wakugumi_ashiba.md)",
        f"- [Single-Pipe Bracket Scaffolding (単管一側ブラケット足場)]({RAW_BASE}/skills/ashiba-keisan/references/tankan_issoku.md)",
        f"- [Scaffold Support Cantilever Bracket (足場受ブラケット)]({RAW_BASE}/skills/ashiba-keisan/references/ashiba_uke_bracket.md)",
        f"- [Steel-Frame Suspended Scaffolding (鉄骨吊り足場)]({RAW_BASE}/skills/ashiba-keisan/references/tekkotsu_tsuri.md)",
        f"- [Material Loading Platform (荷取り構台)]({RAW_BASE}/skills/ashiba-keisan/references/nitori_koudai.md)",
        "",
        "## Standard Lookup Data (JSON)",
        f"- [Wind Tables (47 Prefectures, Terrain I-V, Gust S)]({RAW_BASE}/skills/ashiba-keisan/data/wind_tables.json)",
        f"- [JIS & Scaffolding Materials Catalog]({RAW_BASE}/skills/ashiba-keisan/data/materials.json)",
        "",
        "## Executable Engine & Examples",
        f"- [CLI Entrypoint (calculate.py)]({RAW_BASE}/skills/ashiba-keisan/scripts/calculate.py)",
        f"- [Full 5-Module Benchmark Input (KTS Building)]({RAW_BASE}/skills/ashiba-keisan/examples/kts_building_full.json)",
        f"- [Generated Sample Report (Markdown)]({RAW_BASE}/skills/ashiba-keisan/examples/kts_building_report.md)",
        "",
    ]
    return "\n".join(lines).replace("\r\n", "\n")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated files differ from disk.")
    args = parser.parse_args()

    targets = {
        REPO_ROOT / "dist" / "ashiba-keisan-web-prompt.md": build_web_prompt(),
        REPO_ROOT / "llms.txt": build_llms_txt(),
    }

    if args.check:
        stale = []
        for path, expected in targets.items():
            actual = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else ""
            if actual != expected:
                stale.append(str(path.relative_to(REPO_ROOT)))
        if stale:
            print(f"Stale generated files (run python scripts/build_web_bundle.py): {stale}", file=sys.stderr)
            return 1
        print("Web bundle and llms.txt are up to date.")
        return 0

    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"Generated: {path.relative_to(REPO_ROOT)} ({len(content)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
