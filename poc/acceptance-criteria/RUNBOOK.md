# Acceptance Criteria Runbook (Phase 5)

This framework is the **end-of-POC quality gate** for final generated panels.
It must run after `phase5_generation` is complete for each POC version.

## When to run

Run in this order for every iterative POC (`v0.2.1`, `v0.2.2`, ...):

1. Complete generation for all target scenes in `poc/workflow-<version>/phase5_generation/`.
2. Verify phase5 outputs exist (`scene_*/panels/*.png` and metadata JSON).
3. Run acceptance evaluation for the new version.
4. Review per-image and per-scene failures.
5. If scores fail thresholds, fix/regenerate and rerun.
6. Commit updated evaluation artifacts.

## Command

From repo root:

```bash
.venv/bin/python poc/acceptance-criteria/scripts/run_evaluation.py --versions <new_version>
```

Example:

```bash
.venv/bin/python poc/acceptance-criteria/scripts/run_evaluation.py --versions 0.2.1
```

## Outputs

Written to `poc/acceptance-criteria/reports/`:

- `evaluation_v<version>.json`: detailed report for that version
- `comparison.json`: rolling cross-version comparison

## Rolling comparison behavior (important for iterative POCs)

`comparison.json` is cumulative:

- The runner loads existing `evaluation_v*.json` files in `poc/acceptance-criteria/reports/`.
- It merges in the newly generated report(s).
- It rewrites `comparison.json` including **all historical versions found**.

This means after each POC, just run the new version; previous runs remain part of comparison automatically.

## Suggested release gate

A POC is considered acceptable only if:

- Tier 1 technical validity passes for all panels.
- Tier 2 panel-level quality passes threshold.
- Tier 3 scene consistency passes threshold.
- Tier 4 storytelling/emotional arc passes threshold.

If not, treat as a failed candidate and iterate before comparing as a winner.

## Evaluator modes

- `claude` mode: enabled when `ANTHROPIC_API_KEY` is set (recommended for production-quality judging).
- `heuristic_offline`: fallback mode for environments without API access.

Use `claude` mode for real acceptance decisions.
