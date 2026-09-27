# Submission: SERV Reasoning Hackathon, Edition 01

## Project

Seeri: verifiable deep research for anything onchain. Reasoning by SERV.

- Live MCP server and demo UI: https://pima5-seeri.hf.space
- MCP endpoint (streamable HTTP): https://pima5-seeri.hf.space/mcp
- Source: https://github.com/fozagtx/seeri

## Tracks

- Primary: Open Track. A research agent whose every reasoning step (decompose, classify sources, grade claims, synthesize) runs on SERV Reasoning, with an audit trail of calls and tokens in each report.
- Secondary: Mainnet & MCP. The flagship demo researches Stock Tokens on Robinhood Chain over MCP, reading chain state directly from the mainnet RPC.

## Problem

Agents that act on money (trading, payments, vault allocation) inherit whatever research they were fed. Today that research is "search and summarize": a thread, a dashboard number, and a project announcement get equal weight. Nobody grades the evidence, nobody checks the contract address behind the ticker, and the agent acts anyway.

## What Seeri Does

Seeri is two things that share one method:

1. A skill (`skill/`): a written research method any agent can load. Intake, decomposition into 5-8 sub-questions, source categories, triangulation of the highest-stakes claim, an evidence grid with confidence rules, and a thesis that states what would change it. Domain packs add the verify-first list, traps, and required grid rows for Robinhood Chain, Coinbase AgentKit on Base, IXS RWA vaults, and memecoin markets.
2. An MCP server (`mcp/`): the same method, executed. It loads the skill files at runtime and hands them to SERV as the system context on every call, gathers evidence from primary sources (Robinhood Chain RPC, GeckoTerminal, DefiLlama, the open web), and returns a graded report. Change the skill and the server's behavior changes.

## Why SERV

Every judgment step is a SERV call with a strict JSON contract. SERV's bounded reasoning is what makes 25 small structured calls per report reliable enough to trust: 0 failed calls in the final demo run, 33 seconds end to end on `gpt-5.4-mini`. The report footer shows the exact call and token count so a reader knows how much of the grading was machine-done.

## MCP Tools

| Tool | What it does |
| --- | --- |
| `deep_research` | Full pipeline. Returns a markdown report: thesis, key findings, evidence grid, domain checklist, sources, caveats, what would change my mind, audit footer. |
| `deep_research_json` | Same report as JSON for downstream agents. |
| `verify_claim` | Triangulate one claim across source categories and grade it. |
| `robinhood_token_dossier` | Resolve a ticker or address on Robinhood Chain: RPC-decoded contract identity, pools, liquidity, 24h volume, and a ticker-collision warning when several tokens share the symbol. |
| `protocol_snapshot` | DefiLlama TVL and chain footprint for a protocol or chain. |
| `web_evidence` | Search, fetch, and classify web sources by category, interest, and freshness. |
| `seeri_skill` | Read any file of the research method. |
| `list_skill_files` | List the skill files. |

## Demo Moment

Ask for the `HOOD` dossier. Robinhood Chain has at least six distinct tokens that match that ticker (HOOD, HOODS, HOODCATS, HOODRAT, HOODIE, pHOOD3x). Seeri resolves every one through the mainnet RPC, shows the pool liquidity behind each, and refuses to attribute a price or premium to "HOOD" until the contract is confirmed against the issuer registry. That is the behavior an agent about to trade needs.

## Demo Prompts

```text
Is the HOOD Stock Token on Robinhood Chain trading at a premium to the underlying, and how deep is its liquidity?
```

```text
What does an IXS licensed RWA vault actually license, who can deposit, and where does the yield come from?
```

```text
Verify: Robinhood Chain TVL is above $100M.
```

## Connect To Claude

Claude.ai or Claude Desktop: add a custom connector with the URL `https://pima5-seeri.hf.space/mcp`.

Claude Code:

```bash
claude mcp add --transport http seeri https://pima5-seeri.hf.space/mcp
```

## Revenue Path

- Hosted research API metered per report, with the audit footer as the billing unit.
- Domain packs as paid modules for chains, RWA issuers, and trading desks that need their own verify-first lists.
- Pre-trade research gate for agent frameworks: an agent calls `verify_claim` before it calls `execute_swap`.

## Safety

- Read-only. Seeri holds no wallet and signs nothing.
- Educational research output. Not investment, legal, or tax advice.
- SERV output is never cited as a source; it only organizes evidence.
- Refusal detection and local fallback: if SERV is unavailable the report says so and downgrades confidence.
