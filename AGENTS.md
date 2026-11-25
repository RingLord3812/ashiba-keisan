# AGENTS.md

This repository provides the **`ashiba-keisan`** Agent Skill for Japanese scaffolding and temporary structure strength calculations (`足場計算書` / SUCCES Ver 4.11 / 仮設工業会 / AIJ).

## Required Workflow for Any AI Agent

1. Always read [`skills/ashiba-keisan/SKILL.md`](./skills/ashiba-keisan/SKILL.md) before performing any scaffolding, wall tie, support bracket, suspended scaffold, or loading platform calculation.
2. Never approximate wind loads or member stresses from memory. Execute the bundled zero-dependency Python 3 engine:
   ```bash
   python skills/ashiba-keisan/scripts/calculate.py run <input.json> --format all
   python skills/ashiba-keisan/scripts/calculate.py lookup-wind --help
   python skills/ashiba-keisan/scripts/calculate.py check-connection --help
   python skills/ashiba-keisan/scripts/calculate.py catalog
   ```
3. Run the verification test suite before committing changes:
   ```bash
   python -m unittest discover -s skills/ashiba-keisan/tests -v
   ```
4. If editing `SKILL.md`, `references/*.md`, or `data/*.json`, rebuild the web-chat prompt bundle and `llms.txt`:
   ```bash
   python scripts/build_web_bundle.py
   ```
