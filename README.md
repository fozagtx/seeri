<p align="center">
  <img src="mcp/assets/logo.svg" width="96" alt="Seeri">
</p>

# Seeri

Verifiable deep research for anything onchain. Reasoning by SERV.

Seeri turns an ambiguous question about a token, protocol, chain, RWA vault, or market move into research someone can defend: every claim is tied to a source category, every conclusion carries a confidence level, and every thesis states what would change it.

It ships as two things that share one method:

- **A skill** (`skill/`): the written research method any agent can load. Domain packs cover Robinhood Chain, Coinbase AgentKit on Base, IXS RWA vaults, and memecoin markets.
- **An MCP server** (`mcp/`): the same method, executed. It loads the skill at runtime, hands it to SERV Reasoning as the system context on every call, gathers evidence from primary sources, and returns a graded report. Live at https://pima5-seeri.hf.space.

Built for the SERV Reasoning Hackathon (Open Track, with Robinhood Chain as the flagship MCP demo). See [SUBMISSION.md](SUBMISSION.md).

---

## How A Report Is Built

1. **Intake and decomposition**: SERV breaks the question into 5-8 sub-questions, each targeting one evidence type, including a counterargument.
2. **Evidence gathering**: primary sources first. Robinhood Chain mainnet RPC (`eth_call` for contract identity), GeckoTerminal pools, DefiLlama, then the open web.
3. **Source classification**: SERV labels each source by category, interest (independent, interested, project-reported), freshness, and any domain trap it could trigger.
4. **Grading**: SERV grades each sub-question against the evidence using the skill's confidence rules. High requires a primary source plus independent corroboration across two categories.
5. **Synthesis**: thesis, key findings, domain checklist, caveats, what would change my mind, next checks, and an audit footer with the SERV call and token count.

SERV output is never cited as a source. It organizes evidence; it does not create it.

---

## MCP Tools

| Tool | What it does |
| --- | --- |
| `deep_research` | Full pipeline, markdown report. |
| `deep_research_json` | Same report as JSON. |
| `verify_claim` | Triangulate and grade one claim. |
| `robinhood_token_dossier` | Resolve a ticker or address on Robinhood Chain with a ticker-collision warning. |
| `protocol_snapshot` | DefiLlama TVL and chain footprint. |
| `web_evidence` | Search, fetch, classify web sources. |
| `seeri_skill` | Read a file of the research method. |
| `list_skill_files` | List the skill files. |

### Connect to Claude

Claude.ai or Claude Desktop: add a custom connector with `https://pima5-seeri.hf.space/mcp`.

```bash
claude mcp add --transport http seeri https://pima5-seeri.hf.space/mcp
```

### Run the MCP locally

```bash
export SERV_API_KEY="..."        # from console.openserv.ai; without it Seeri runs local fallback reasoning
cd mcp
./sync_skill.sh                  # vendor skill/ into mcp/skill for the server
pip install -r requirements.txt
uvicorn server:app --port 7860   # landing page on /, MCP at /mcp
```

---

## Repository Structure

```text
.
├── README.md
├── SUBMISSION.md               # Hackathon submission notes and demo prompts
├── ARTICLE.md                  # Example long-form output (RWA distribution research)
├── CLAUDE.md                   # Agent system prompt and progressive disclosure guide
├── install.sh                  # Install the skill to ~/.agents/skills/seeri
├── install-custom.sh           # Install to a custom path
├── skill/
│   ├── SKILL.md                # Entrypoint, routing, confidence rules, boundaries
│   ├── research-workflow.md    # Intake to synthesis
│   ├── source-map.md           # Source categories and evaluation
│   ├── evidence-grid.md        # Findings grid and confidence scoring
│   ├── article-synthesis.md    # Articles, memos, threads
│   ├── reasoning-serv.md       # How the skill uses SERV Reasoning
│   ├── hackathon-submission.md
│   ├── resources.md
│   └── domains/
│       ├── robinhood-chain.md  # Chain facts, sources, verify-first, traps, required grid rows
│       ├── agentkit-base.md
│       ├── ixs-rwa-vaults.md
│       └── memecoin-markets/   # Memecoin knowledge base (13 chapters, glossary, patterns, cheatsheet)
├── mcp/
│   ├── server.py               # MCP server (streamable HTTP) + landing page
│   ├── Dockerfile              # Space deployment (docker sdk)
│   ├── seeri/
│   │   ├── skill_loader.py     # Loads skill/ at runtime
│   │   ├── prompts.py          # SERV step prompts wrapping the skill method
│   │   ├── serv.py             # SERV client with audit trail and refusal handling
│   │   ├── sources.py          # RPC, GeckoTerminal, DefiLlama, web fetchers
│   │   └── pipeline.py         # Decompose, gather, classify, grade, synthesize
│   ├── skill/                  # Vendored copy of skill/ for the Space (./sync_skill.sh)
│   ├── assets/                 # Seeri mark and official partner logos (see assets/partners/SOURCES.md)
│   └── README.md               # Hugging Face Space card
├── agents/                     # Agent configurations
├── commands/                   # Slash commands
├── rules/                      # Evidence integrity guardrails
└── tests/
    └── validate_structure.sh   # Structure, link, and hygiene validator
```

---

## Install The Skill

```bash
./install.sh -y                                       # ~/.agents/skills/seeri
./install-custom.sh                                   # choose a target
```

## Validate

```bash
bash tests/validate_structure.sh
```

---

Educational research output. Not investment, legal, or tax advice.

## License

MIT
