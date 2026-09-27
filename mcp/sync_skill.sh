#!/usr/bin/env bash
# Vendors the repo skill into mcp/skill/ so the Hugging Face Space (which only
# contains mcp/) serves the same method files. Run after editing skill/.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rsync -a --delete "$HERE/../skill/" "$HERE/skill/"
echo "Synced $HERE/../skill -> $HERE/skill"
