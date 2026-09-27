# Deep Mantle Researcher

A research-agent skill that turns ambiguous onchain-finance questions into source-mapped evidence grids, confidence ratings, and defensible articles or memos.

Built for the Mantle ecosystem, RWA research, tokenized equities, DeFi liquidity, and AI research-agent workflows.

---

## What It Does

Most AI research workflows stop at generic search-and-summarize. **Deep Mantle Researcher** enforces rigorous onchain analysis:

1. **Intake & Decomposition**: Breaks messy questions into verifiable sub-claims with clear failure costs.
2. **Source Mapping**: Classifies sources by category (primary releases, technical docs, onchain analytics, market data, regulatory framing).
3. **Evidence Grids**: Maps claims to confidence scores and flags contradictions directly.
4. **Article & Memo Synthesis**: Generates publication-ready articles, research briefs, or X threads with explicit caveats.

---

## Repository Structure

```text
.
├── ARTICLE.md                  # Complete published research article (RWA Distribution & Mantle)
├── CLAUDE.md                   # Agent system prompt & progressive disclosure guide
├── SUBMISSION.md               # Hackathon project summary & demo prompts
├── LICENSE                     # MIT License
├── install.sh                  # Local installer script
├── install-custom.sh           # Custom environment installer
├── skill/
│   ├── SKILL.md                # Skill entrypoint & routing logic
│   ├── research-workflow.md    # 4-stage intake-to-thesis workflow
│   ├── source-map.md           # Source categorization & evaluation
│   ├── evidence-grid.md        # Structured findings & confidence scoring
│   ├── article-synthesis.md    # Formatting for articles, memos, & threads
│   ├── hackathon-submission.md # Hackathon packaging instructions
│   └── resources.md            # Mantle ecosystem references & live sources
├── agents/                     # Specialized agent configurations
│   ├── research-analyst.md
│   ├── source-verifier.md
│   ├── article-synthesizer.md
│   └── skill-demo-coach.md
├── commands/                   # Agent slash commands
│   ├── research-sprint.md
│   ├── verify-claim.md
│   ├── article-brief.md
│   └── skill-demo.md
├── rules/                      # Guardrails & safety rules
│   └── evidence-integrity.md
└── tests/
    └── validate_structure.sh   # Structure & hygiene validator
```

---

## Installation

Install the skill locally into your agent environment:

```bash
./install.sh -y
```

Or for custom target paths:

```bash
./install-custom.sh --target ~/.agents/skills/deep-mantle-researcher
```

---

## Validation

Run the structure and hygiene validation test suite:

```bash
bash tests/validate_structure.sh
```

---

## License

MIT
