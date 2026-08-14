#!/bin/bash
# Idempotent bootstrap of the isolated bench DSH_HOME.
# Creates .dsh-home, writes the llm-pi-ai provider routes (deepseek is the
# native adapter, so only openai/xai need pi-ai routes), auto-initializes the
# headless profile with a trivial run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="$ROOT/.dsh-home"
mkdir -p "$HOME_DIR"

# settings.yaml: provider routes always; agent-default-model pinned per arm by the runner
if [ ! -f "$HOME_DIR/settings.yaml" ]; then
  cat > "$HOME_DIR/settings.yaml" <<'YAML'
agent-default-model:
  provider: deepseek-official
  model: deepseek-v4-flash
  reasoningEffort: high
llm-pi-ai:
  providers:
    openai:
      apiKeyEnv: OPENAI_API_KEY
    xai:
      apiKeyEnv: XAI_API_KEY
      api: openai-completions
      baseURL: https://api.x.ai/v1
      models:
        - id: grok-4.6
          reasoningEfforts:
            off:
            low: low
            medium: medium
            high: high
YAML
fi

# credentials into the environment (inherited env wins in dsh-credentials)
eval "$(python3 - <<'EOF'
import sys
sys.path.insert(0, '$ROOT/bin')
from lib.common import load_credentials
for k, v in load_credentials().items():
    print(f'export {k}={v!r}')
EOF
)"

# auto-init the headless profile (one trivial run)
mkdir -p "$ROOT/work/.init" && cd "$ROOT/work/.init"
DSH_HOME="$HOME_DIR" dsh --profile headless "Reply with exactly: OK" >/dev/null 2>&1
echo "bench DSH home ready at $HOME_DIR"
