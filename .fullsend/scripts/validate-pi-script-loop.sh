#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
"$script_dir/validate-output-schema.sh"
python3 - <<'PY'
import json
from pathlib import Path
output = Path('output')
result = json.loads((output / 'agent-result.json').read_text())
assert result['status'] == 'ok', result
expected = ['script_started']
for step in ['plan', 'review', 'summarize']:
    expected += [f'call_started:{step}', f'call_completed:{step}']
    assert (output / f'{step}.txt').read_text().strip(), step
expected += ['script_completed']
actual = (output / 'loop-trace.txt').read_text().splitlines()
assert actual == expected, actual
if result['mode'] == 'live':
    for step in ('plan', 'review', 'summarize'):
        call = json.loads((output / f'{step}-call.json').read_text())
        assert call['isError'] is False and call['stopReason'] == 'stop', step
        assert call['model'] == 'anthropic-vertex/claude-haiku-4-5', step
        assert call['usage']['input'] > 0 and call['usage']['output'] > 0, step
elif result['mode'] == 'proof':
    for step in ('plan', 'review', 'summarize'):
        assert (output / f'{step}.txt').read_text().strip() == f'MOCK response for {step}'
else:
    raise AssertionError('Unsupported proof mode')
print(f"PASS: Bash completed all three steps in order; mode={result['mode']}")
PY
