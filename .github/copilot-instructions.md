# GitHub Copilot Instructions

This repository contains the `ashiba-keisan` scaffolding structural calculation skill (`SUCCES Ver 4.11` / `仮設工業会` / `AIJ`).

- Read `skills/ashiba-keisan/SKILL.md` before modifying calculation formulas or running engineering checks.
- Keep `skills/ashiba-keisan/scripts/` dependency-free (Python 3 standard library only).
- Verify 100% pass rate on `python -m unittest discover -s skills/ashiba-keisan/tests -v` and regenerate web bundles with `python scripts/build_web_bundle.py` after doc/catalog updates.
