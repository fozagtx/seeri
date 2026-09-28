---
title: Seeri
emoji: 🔎
colorFrom: gray
colorTo: yellow
sdk: docker
app_port: 7860
app_file: server.py
pinned: false
tags:
  - mcp-server-track
  - research
  - openserv
  - robinhood-chain
---

# Seeri

Seeri is a verifiable deep-research workflow for onchain questions, available as an agent skill and as this MCP server. The server loads the skill at runtime and runs it. It decomposes a question into sub-claims, gathers evidence from block explorers, market data, and the web, then grades every claim with SERV Reasoning so each conclusion carries an auditable confidence rating. When no SERV key is configured it runs the same pipeline with deterministic local heuristics and labels the output accordingly.

## Endpoint

Streamable HTTP MCP endpoint:

```
https://pima5-seeri.hf.space/mcp
```

## Connect to Claude

**Claude.ai / Desktop (custom connector):**

```
https://pima5-seeri.hf.space/mcp
```

**Claude Code:**

```bash
claude mcp add --transport http seeri https://pima5-seeri.hf.space/mcp
```

**Cursor / other clients:**

```json
{"url": "https://pima5-seeri.hf.space/mcp"}
```

## Tools

| Tool | What it does |
| --- | --- |
| `deep_research` | Full research pipeline: decompose, gather, classify, grade, synthesize. Returns a markdown report. |
| `deep_research_json` | Same pipeline, returns the full structured report as JSON. |
| `verify_claim` | Grades a single claim against gathered evidence. |
| `robinhood_token_dossier` | Blockscout/RPC identity, ticker-collision check across all same-ticker tokens, and GeckoTerminal pools for a Robinhood Chain token. |
| `protocol_snapshot` | DefiLlama TVL, chains, and category for a protocol or chain. |
| `web_evidence` | Web search with classified source list. |
| `seeri_skill` | Read a file from the Seeri skill (the method the tools apply). |
| `list_skill_files` | List every markdown file in the loaded skill. |

Also exposes resource `seeri://skill/{path}` and prompt `research_brief`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SERV_API_KEY` | OpenServ SERV Reasoning API key. Required for SERV reasoning; without it the pipeline runs local heuristic grading and labels output `reasoning: local`. |
| `SERV_MODEL` | Model override. Defaults to `gpt-5.4-mini`. |
| `PORT` | HTTP port. Defaults to `7860`. |

## Run locally

```bash
cd mcp
./sync_skill.sh   # vendors ../skill into mcp/skill (run after editing the skill)
pip install -r requirements.txt
uvicorn server:app --port 7860
```

`GET /` serves a landing page, `GET /health` a JSON health check, `POST /mcp` the MCP endpoint.

Educational research output. Not investment, legal, or tax advice.
