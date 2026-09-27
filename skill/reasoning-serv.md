# Reasoning With SERV

Seeri uses SERV Reasoning (OpenServ) for the steps that require judgment: decomposing a question, classifying sources, grading confidence, spotting contradictions, and synthesizing a thesis. SERV is an inference API with a reasoning compiler; it is OpenAI- and Claude-SDK compatible, so it is a base URL and key change.

SERV does not fetch evidence. Evidence always comes from the sources in [source-map.md](source-map.md) and the domain packs. SERV organizes and grades what those sources return.

## Setup

The user is expected to have a key already exported in their shell:

```bash
export SERV_API_KEY="..."          # from console.openserv.ai
export SERV_MODEL="gpt-5.4-mini"   # optional, any model in the SERV catalog
```

Check for the key before any reasoning call. If `SERV_API_KEY` is missing:

1. Say so in one line and point to `console.openserv.ai`.
2. Continue the workflow using your own reasoning. Do not block the research.
3. Mark the output header `reasoning: local` instead of `reasoning: serv`.

Never ask the user to paste the key into chat. Never write the key into any file in the repo.

## Endpoints

Base URL: `https://inference-api.openserv.ai`

| Path | Format | Use |
| --- | --- | --- |
| `POST /v1/chat/completions` | OpenAI Chat Completions | Default. Works with every model in the catalog. |
| `POST /v1/responses` | OpenAI Responses | OpenAI models only. Use when the reasoning trace is wanted. |
| `POST /v1/messages` | Messages format (Claude SDK) | Claude-shaped clients. |

Rules that trip people up:

- Every request must include a system prompt (`system` message, `instructions`, or developer message). Requests without one are rejected.
- OpenAI-shape SDKs take `/v1` in the base URL. The official Claude SDK does not; it appends `/v1/messages` itself.
- Auth is `Authorization: Bearer $SERV_API_KEY` in every format.

Minimal call:

```bash
curl https://inference-api.openserv.ai/v1/chat/completions \
  -H "Authorization: Bearer $SERV_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {"role": "system", "content": "You are Seeri, a research analyst. Return JSON only."},
      {"role": "user", "content": "Decompose: Is HOOD stock token on Robinhood Chain trading at a premium to the underlying?"}
    ]
  }'
```

## Where SERV Is Used In The Workflow

| Workflow step | SERV call | Output contract |
| --- | --- | --- |
| Decompose question | `decompose` | 5-8 sub-questions, each with `why_it_matters` and `source_categories` (at least 3 across the set) |
| Classify a source | `classify_source` | `category`, `interest` (independent / interested / project-reported), `freshness` |
| Grade a claim | `grade_claim` | `confidence` (high / medium / low), `basis`, `contradictions`, `gaps` |
| Synthesize | `synthesize` | `thesis`, `caveats`, `what_would_change_my_mind`, `next_checks` |

Every call gets the same system prompt core:

> You are Seeri, a verifiable research analyst. You reason over evidence supplied to you. You never invent facts, numbers, sources, or URLs. If evidence is missing you say so and lower confidence. Label project-reported and interested-party claims. Never give investment, legal, or tax advice. Return only the JSON schema requested.

Attach the step-specific instructions and the evidence payload as the user message. Ask for JSON and validate it. If the JSON fails to parse, retry once with "Return valid JSON only"; then fall back to local reasoning and flag it.

## Audit Trail

Record for every SERV call: step name, model, prompt token count, completion token count, and whether the response validated. Put the totals in the output footer so a reader can see how much of the report was machine-graded.

## Boundaries

- SERV output is never cited as a source.
- A high confidence grade from SERV still requires the underlying evidence to meet the rules in [evidence-grid.md](evidence-grid.md).
- If SERV and your own reading disagree on a grade, keep the lower confidence and note the disagreement.
