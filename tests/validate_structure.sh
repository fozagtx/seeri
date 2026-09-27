#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required_files=(
  ".gitignore"
  "ARTICLE.md"
  "README.md"
  "LICENSE"
  "CLAUDE.md"
  "SUBMISSION.md"
  "install.sh"
  "install-custom.sh"
  "skill/SKILL.md"
  "skill/research-workflow.md"
  "skill/source-map.md"
  "skill/evidence-grid.md"
  "skill/article-synthesis.md"
  "skill/hackathon-submission.md"
  "skill/resources.md"
  "skill/reasoning-serv.md"
  "skill/domains/robinhood-chain.md"
  "skill/domains/agentkit-base.md"
  "skill/domains/ixs-rwa-vaults.md"
  "skill/domains/memecoin-markets/SKILL.md"
  "skill/domains/memecoin-markets/glossary.md"
  "skill/domains/memecoin-markets/patterns.md"
  "skill/domains/memecoin-markets/cheatsheet.md"
  "mcp/server.py"
  "mcp/Dockerfile"
  "mcp/requirements.txt"
  "mcp/README.md"
  "mcp/seeri/prompts.py"
  "mcp/seeri/skill_loader.py"
  "mcp/sync_skill.sh"
  "mcp/skill/SKILL.md"
  "mcp/assets/logo.svg"
  "agents/research-analyst.md"
  "agents/source-verifier.md"
  "agents/article-synthesizer.md"
  "agents/skill-demo-coach.md"
  "commands/research-sprint.md"
  "commands/verify-claim.md"
  "commands/article-brief.md"
  "commands/skill-demo.md"
  "rules/evidence-integrity.md"
  "tests/validate_structure.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$ROOT_DIR/$file" ]]; then
    echo "Missing required file: $file" >&2
    exit 1
  fi
done

if ! grep -q '^name: seeri$' "$ROOT_DIR/skill/SKILL.md"; then
  echo "Missing skill name frontmatter." >&2
  exit 1
fi

if ! grep -q '^description: .*Use when ' "$ROOT_DIR/skill/SKILL.md"; then
  echo "Missing actionable description frontmatter." >&2
  exit 1
fi

if ! grep -q '^name: seeri-memecoin-markets$' "$ROOT_DIR/skill/domains/memecoin-markets/SKILL.md"; then
  echo "Missing memecoin-markets skill name frontmatter." >&2
  exit 1
fi

for linked in research-workflow.md source-map.md evidence-grid.md article-synthesis.md hackathon-submission.md resources.md reasoning-serv.md domains/robinhood-chain.md domains/memecoin-markets/SKILL.md; do
  if ! grep -q "$linked" "$ROOT_DIR/skill/SKILL.md"; then
    echo "SKILL.md does not link $linked" >&2
    exit 1
  fi
done

bash -n "$ROOT_DIR/install.sh"
bash -n "$ROOT_DIR/install-custom.sh"
bash -n "$ROOT_DIR/tests/validate_structure.sh"
bash -n "$ROOT_DIR/mcp/sync_skill.sh"

while IFS= read -r py; do
  if ! python3 -m py_compile "$py"; then
    echo "Python compile failed: $py" >&2
    exit 1
  fi
done < <(find "$ROOT_DIR/mcp" -name '*.py' -not -path '*/.venv/*')

blocked_terms=(
  "$(printf "%s%s" "Co" "dex")"
  "$(printf "%s%s" "Anth" "ropic")"
  "$(printf "%s%s%s" "Co-Authored-" "By:" " ")"
  "$(printf "%s%s" "noreply@" "anthropic.com")"
)

for term in "${blocked_terms[@]}"; do
  if grep -R -n --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=node_modules -- "$term" "$ROOT_DIR" >/tmp/seeri_hygiene.txt; then
    cat /tmp/seeri_hygiene.txt >&2
    echo "Attribution hygiene check failed." >&2
    exit 1
  fi
done

echo "Structure validation passed."
