#!/usr/bin/env bash
# PostToolUse hook: display fal.ai spending after Bash commands
# Reads the live cost file written by FalCostTracker and prints a summary to stderr.

LIVE_FILE="/workspaces/novel-to-toon/poc/workflow-0.2.0/reports/cost_live.json"

# Only print if the live cost file exists (no noise before PoC starts)
if [ ! -f "$LIVE_FILE" ]; then
    exit 0
fi

# Read stdin (PostToolUse JSON) but we don't need to filter — the matcher
# in settings.local.json already limits this to Bash tool calls.
cat > /dev/null

# Parse the live cost file with Python (available in this environment)
python3 -c "
import json, sys
try:
    with open('$LIVE_FILE') as f:
        d = json.load(f)
    total = d['total_cost_usd']
    budget = d['budget_usd']
    pct = d['percent_used']
    calls = d['total_calls']
    last = d.get('last_call', {})
    model_short = last.get('model', '').split('/')[-1]
    last_cost = last.get('cost_usd', 0)
    panel = last.get('panel_id', '?')
    print(f'[cost] \${total:.2f} / \${budget:.2f} ({pct}%) | {calls} calls | last: {model_short} \${last_cost:.2f} ({panel})', file=sys.stderr)
except Exception:
    pass
"
