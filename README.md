# ashiba-keisan (足場強度計算スキル / Skill Tính Toán Giàn Giáo Chuẩn Nhật)

[![CI](https://github.com/RingLord3812/ashiba-keisan/actions/workflows/ci.yml/badge.svg)](https://github.com/RingLord3812/ashiba-keisan/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Standard: Agent Skills](https://img.shields.io/badge/Standard-agentskills.io-0369a1.svg)](https://agentskills.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B%20(Zero%20Deps)-3776ab.svg)](./skills/ashiba-keisan/scripts/calculate.py)

**日本語** | **Tiếng Việt** | **English**

日本の建築仮設基準（一般社団法人 仮設工業会『改訂 風荷重に対する足場の安全技術指針』、日本建築学会『鋼構造設計規準』、**SUCCES for Windows Ver 4.11** 様式）に準拠した足場強度計算スキルおよび Python 計算エンジン・足場計算書（A4印刷対応HTML＋SVG図面 / Markdown / JSON）ジェネレーター。

Bộ kỹ năng (AI Agent Skill) và động cơ tính toán kết cấu giàn giáo theo tiêu chuẩn Nhật Bản (`SUCCES Ver 4.11` / `仮設工業会` / `AIJ`), đóng gói theo chuẩn mở [`agentskills.io`](https://agentskills.io) để cài đặt và sử dụng trên **mọi nền tảng AI** (Antigravity, Claude Code, Codex, Cursor, Windsurf, GitHub Copilot, Gemini CLI, ChatGPT, Claude.ai, Gemini Gems).

Universal AI Agent Skill and zero-dependency Python 3 structural calculation engine for Japanese scaffolding and temporary structures (`足場計算書`), verified across all 31 report pages of the SUCCES Ver 4.11 benchmark.

---

## 対応構造モジュール / 5 Mô-đun Tính Toán / Supported Modules

| モジュール (`type`) | 日本語名称 | Tiếng Việt | 照査項目 / Verification Scope |
| :--- | :--- | :--- | :--- |
| `wakugumi` | 枠組足場 | Giàn giáo khung | 壁つなぎ(2構面風荷重)・建枠・開口部梁枠($W_1+W_2$)・ジャッキベース |
| `tankan_issoku` | 単管一側ブラケット足場 | Giàn giáo ống đơn 1 hàng cột | 荷重・壁つなぎ(1構面)・建地座屈($\lambda\le\Lambda$ / $\lambda>\Lambda$)＋偏心曲げ中期1.25倍・足場板 |
| `bracket_support` | 足場受ブラケット | Hệ công-xôn thép hình đỡ giàn giáo | 大引(横座屈)・片持ブラケット・溶接部($\sigma_b,\tau,\sigma_{MQ}$)・アンカーボルト(埋込長)・コンクリート支圧・ベースプレート |
| `tsuri_ashiba` | 鉄骨吊り足場 | Giàn giáo treo kết cấu thép | ループ吊りチェーン・足場板・根太・大引(対称2点集中)・張り出し部(片持梁) |
| `nitori_koudai` | 荷取り構台 | Sàn tiếp liệu | 衝撃割増(1.1倍)・床板・根太・大引(部分等分布)・本設梁(部分等分布) |

- **単位系 / Units**: `kgf/cm²` + `(N/mm²)`・`(N)`・`(kN・mm)` 併記（SUCCES 準拠 $g = 9.81$・有効数字3桁切上げ）
- **収録データ / Built-in Data**: 47都道府県別基準風速 $V_0$・台風時割増係数 $K_e$・粗度区分Ⅰ〜Ⅴ×高さ0–100m 瞬間風速分布係数 $S$・JIS H形鋼 / 単管 / 角パイプ / 建枠 / アンカーボルト / コンクリートカタログ
- **拡張オプション / Flags**: `--deflection-limit 300`（$L/300$ たわみ制限警告）、`--strict-aij`（厳密重ね合わせ・AIJ理論対照）

---

## どの AI でも使えるインストール方法 / Cài đặt cho mọi AI / Universal Installation

### 1. Universal CLI (`npx skills add`) — Khuyên dùng / Recommended
Tương thích / Works with: **Claude Code, Antigravity, Codex, Cursor, Windsurf, GitHub Copilot, Gemini CLI, Cline, Roo Code, OpenCode, Amp**
```bash
npx skills add RingLord3812/ashiba-keisan
```

### 2. Một lệnh cài hàng loạt cho mọi AI trên máy / One-Line Cross-Platform Installer

**Windows (PowerShell):**
```powershell
# Cài vào ~/.agents/skills/ashiba-keisan (chuẩn chung)
irm https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main/install.ps1 | iex

# Hoặc clone rồi cài cùng lúc cho TẤT CẢ AI (Antigravity, Claude, Codex, Cursor, Gemini, Copilot, Windsurf)
git clone https://github.com/RingLord3812/ashiba-keisan.git
cd ashiba-keisan
.\install.ps1 -Target all
```

**macOS / Linux (Bash):**
```bash
# Cài chuẩn chung (~/.agents/skills/ashiba-keisan)
curl -fsSL https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main/install.sh | bash

# Cài cùng lúc cho TẤT CẢ AI trên máy
curl -fsSL https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main/install.sh | bash -s -- --target all
```
Supported `--target` values: `agents`, `antigravity`, `claude`, `codex`, `cursor`, `gemini`, `copilot`, `windsurf`, `project`, `all`.

### 3. Claude Code Native Plugin Marketplace
```text
/plugin marketplace add RingLord3812/ashiba-keisan
/plugin install ashiba-keisan@ashiba-keisan
```

### 4. Gemini CLI Extension
```bash
gemini extensions install https://github.com/RingLord3812/ashiba-keisan
```

### 5. Web Chat AI không có Terminal (ChatGPT Custom GPT / Claude.ai Projects / Gemini Gems / NotebookLM)
Không cần cài đặt hay chạy dòng lệnh / No shell required:
1. Tải file tổng hợp tự chứa [`dist/ashiba-keisan-web-prompt.md`](./dist/ashiba-keisan-web-prompt.md) (chứa toàn bộ công thức chuẩn Nhật + bảng tra 47 tỉnh và vật liệu JIS).
2. Dán vào **System Instructions** hoặc tải lên mục **Project Knowledge / Files** của ChatGPT, Claude.ai, Gemini Gems hoặc NotebookLM.
3. Với các AI duyệt web trực tiếp, chỉ cần gửi link [`llms.txt`](https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main/llms.txt).

---

## クイックスタート / Chạy thử nhanh / Quick Start (Python 3.10+, Zero Dependencies)

```bash
# 1. 全5モジュール一括計算（(仮称)KTSビル新築工事・PDF全31ページ完全再現）
python skills/ashiba-keisan/scripts/calculate.py run skills/ashiba-keisan/examples/kts_building_full.json --format all

# 2. たわみ制限 L/300 付き照査 & 厳密AIJモード対照
python skills/ashiba-keisan/scripts/calculate.py run skills/ashiba-keisan/examples/kts_building_full.json --deflection-limit 300 --strict-aij

# 3. 仮設工業会指針 風荷重・壁つなぎ単体照査
python skills/ashiba-keisan/scripts/calculate.py lookup-wind \
  --location "東京都（23区内）" --terrain 一般市街地 --z 27.5 \
  --height 31 --length 25 --phi 0.7 --position B --tie-h 3.6 --tie-v 3.4 --planes 2

# 4. ブラケット接合部（溶接・アンカー・コンクリート支圧・ベースプレート）単体照査
python skills/ashiba-keisan/scripts/calculate.py check-connection \
  --moment 417930 --shear 5572.4 --bolt M20 --nt 4 --nc 2

# 5. カタログ照会 & 自動テスト実行 (17 tests)
python skills/ashiba-keisan/scripts/calculate.py catalog --category h_beams
python -m unittest discover -s skills/ashiba-keisan/tests -v
```

生成された [`kts_building_report.html`](./skills/ashiba-keisan/examples/kts_building_report.html) をブラウザで開き `Ctrl + P`（A4印刷）すると、表紙・承認印欄・検討概要書・検討結果概要・SVG構造図付きの **足場計算書 PDF** をそのまま出力できます。

---

## リポジトリ構成 / Cấu trúc Repository

```text
ashiba-keisan/
├── skills/ashiba-keisan/          # Canonical Agent Skill (agentskills.io)
│   ├── SKILL.md                   # Skill entrypoint & anti-error rules
│   ├── data/                      # wind_tables.json (47都道府県), materials.json (JIS/仮設)
│   ├── references/                # 6 Japanese technical calculation manuals
│   ├── scripts/                   # Zero-dependency Python engine, SVG & A4 HTML/MD generator
│   ├── examples/                  # KTS Building 5-module benchmark & Osaka single-module sample
│   └── tests/                     # 17 unit & 31-page PDF benchmark tests
├── dist/ashiba-keisan-web-prompt.md  # Single-file bundle for ChatGPT / Claude.ai / Gemini Gems
├── llms.txt                       # Raw URL index for web-enabled LLMs
├── install.ps1 / install.sh       # Cross-platform 1-command installers for all AI tools
├── AGENTS.md / CLAUDE.md / GEMINI.md # Universal coding-agent repo entrypoints
├── .claude-plugin/                # Claude Code plugin & marketplace manifests
├── .antigravity-plugin/           # Google Antigravity plugin manifest (+ root plugin.json)
├── .codex-plugin/                 # OpenAI Codex plugin manifest
├── .cursor-plugin/ & .cursor/rules/ # Cursor plugin manifest & MDC rule
├── .github/                       # GitHub Copilot instructions & Cross-OS CI workflow
└── gemini-extension.json          # Gemini CLI extension manifest
```

---

## 免責事項 / Lưu ý kỹ thuật / Disclaimer

本ツールの計算結果は設計補助・検算を目的としたものです。実現場への適用・労働基準監督署への設置届出にあたっては、必ず有資格者（建築士・施工管理技士等）が使用部材の最新の仮設工業会認定値および現場条件を確認のうえ最終承認を行ってください。

## License

[MIT](./LICENSE) © 2026 RingLord3812
