"""Seeri research pipeline: decompose, gather, classify, grade, synthesize."""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import prompts, serv, skill_loader, sources

_TICKER_STOP = {"A", "I", "IS", "ON", "THE", "AND", "OR", "TO", "OF", "IN", "IT", "AT",
                "BY", "FOR", "RWA", "MCP", "API", "DEX", "TVL", "APY", "KYC", "US",
                "USA", "NOT", "VS"}


def _detect_domain(question: str) -> str:
    return skill_loader.detect_domain(question)


def _tickers_and_addresses(question: str, domain: str = "auto") -> list[str]:
    found = re.findall(r"\b0x[a-fA-F0-9]{40}\b", question)
    found += re.findall(r"\$([A-Z]{2,6})\b", question)
    if domain == "robinhood-chain":
        found += [w for w in re.findall(r"\b[A-Z][A-Z0-9]{1,5}\b", question)
                  if w not in _TICKER_STOP]
    return list(dict.fromkeys(found))[:3]


def _fallback_decompose(question: str) -> dict:
    return {
        "sub_questions": [
            {"id": "q1", "text": f"What is the current onchain and market state relevant to: {question}",
             "why_it_matters": "Establishes base facts.", "source_categories": ["chain_state", "market_data"]},
            {"id": "q2", "text": f"What do primary sources and project-reported materials claim about: {question}",
             "why_it_matters": "Separates interested claims from independent evidence.", "source_categories": ["primary_docs"]},
            {"id": "q3", "text": f"What do independent news and social sources say about: {question}",
             "why_it_matters": "Corroborates or contradicts primary claims.", "source_categories": ["news", "social"]},
            {"id": "q4", "text": f"Are there regulatory or structural risks bearing on: {question}",
             "why_it_matters": "Surfaces non-market failure modes.", "source_categories": ["regulatory"]},
            {"id": "q5", "text": f"What evidence is missing to answer: {question}",
             "why_it_matters": "Defines the gaps that cap confidence.", "source_categories": ["news"]},
        ],
        "highest_stakes": "q1",
        "search_queries": [question, f"{question} onchain data", f"{question} official documentation"],
    }


def _fallback_decompose_with_domain(question: str, domain: str) -> dict:
    plan = _fallback_decompose(question)
    for row in skill_loader.domain_output_rows(domain):
        if len(plan["sub_questions"]) >= 8:
            break
        plan["sub_questions"].append({
            "id": f"q{len(plan['sub_questions'])+1}",
            "text": f"Domain grid row '{row}': what is the current value/state relevant to: {question}",
            "why_it_matters": "Required output row in the domain pack.",
            "source_categories": ["chain_state", "market_data"],
        })
    return plan


def _fallback_grade(claim_id: str, claim: str, evidence: list[sources.Evidence]) -> dict:
    independent = [e for e in evidence if e.interest == "independent"]
    confidence = "high" if len(independent) >= 2 else ("medium" if evidence else "low")
    return {
        "id": claim_id, "claim": claim, "confidence": confidence,
        "basis": f"Local heuristic: {len(independent)} independent evidence items.",
        "supporting": [e.id for e in evidence],
        "contradicting": [],
        "contradictions": "",
        "gaps": [] if evidence else ["no evidence was gathered"],
    }


def _serv_client(domain: str = "general"):
    return serv.ServClient(domain) if serv.available() else None


def _skill_meta(domain: str) -> dict:
    d = skill_loader.skill_dir()
    rel = skill_loader.DOMAIN_FILES.get(domain)
    return {"dir": d, "method_files": [f for f in skill_loader.METHOD_FILES if d],
            "domain_pack": rel if (d and rel and os.path.isfile(os.path.join(d, rel))) else None}


def deep_research(question: str, decision: str = "", domain: str = "auto", depth: str = "standard") -> dict:
    """Full research pipeline. Returns a report dict."""
    domain = _detect_domain(question) if domain == "auto" else domain
    client = _serv_client(domain)
    reasoning = "serv" if client else "local"

    # 1. Decompose
    if client:
        res = client.reason("decompose", prompts.DECOMPOSE.format(
            question=question, decision=decision or "general research", domain=domain))
        plan = res["data"] or _fallback_decompose_with_domain(question, domain)
    else:
        plan = _fallback_decompose_with_domain(question, domain)
    sub_questions = plan.get("sub_questions") or _fallback_decompose(question)["sub_questions"]
    queries = plan.get("search_queries") or [question]
    max_q = 3 if depth == "quick" else 6

    # 2. Gather evidence (concurrent): domain fetchers first so chain_state/market_data lead.
    fetchers = []
    if domain == "robinhood-chain":
        for tok in _tickers_and_addresses(question, domain):
            fetchers.append(lambda tok=tok: sources.robinhood_token(tok))
    named = re.findall(r"\b(?:protocol|on|in|for|of)\s+([A-Z][A-Za-z0-9\-]{2,})\b", question)
    for name in named[:2]:
        if len(name) > 2:
            fetchers.append(lambda name=name: sources.defillama_protocol(name))
    for q in queries[:max_q]:
        fetchers.append(lambda q=q: sources.web_search(q, max_results=4))
    evidence: list[sources.Evidence] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(lambda f: f(), fetchers):
            evidence.extend(result)
    for i, e in enumerate(evidence):
        e.id = f"e{i+1}"
        if e.category in ("chain_state", "market_data"):
            e.relevance = 0.8

    # 3. Classify (concurrent)
    if client:
        def _classify(ev):
            res = client.reason("classify_source", prompts.CLASSIFY_SOURCE.format(
                url=ev.url, title=ev.title, excerpt=ev.excerpt[:800], question=question))
            d = res["data"] or {}
            ev.category = d.get("category", ev.category)
            ev.interest = d.get("interest", ev.interest)
            ev.freshness = d.get("freshness", ev.freshness)
            try:
                ev.relevance = float(d.get("relevance", 0.0) or 0.0)
            except (TypeError, ValueError):
                pass
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(_classify, evidence[:16]))
        for e in evidence:
            if e.category in ("chain_state", "market_data"):
                e.relevance = max(e.relevance, 0.8)

    # 4. Grade each sub-question (concurrent)
    relevant = [e for e in evidence
                if e.relevance >= 0.3 or e.category in ("chain_state", "market_data")] or evidence
    ev_payload = json.dumps([e.model_dump(exclude={"raw"}) for e in relevant], default=str)

    def _grade(i, sq):
        fid = sq.get("id", f"q{i+1}")
        if client:
            res = client.reason("grade_claim", prompts.GRADE_CLAIM.format(
                claim=sq["text"], evidence=ev_payload))
            g = res["data"] or {}
            return {
                "id": fid, "claim": sq["text"],
                "confidence": g.get("confidence", "low"), "basis": g.get("basis", ""),
                "supporting": g.get("supporting", []), "contradicting": g.get("contradicting", []),
                "contradictions": g.get("contradictions", ""), "gaps": g.get("gaps", []),
            }
        return _fallback_grade(fid, sq["text"], relevant)

    with ThreadPoolExecutor(max_workers=6) as pool:
        findings = list(pool.map(lambda t: _grade(*t), enumerate(sub_questions)))

    # 5. Synthesize
    if client:
        res = client.reason("synthesize", prompts.SYNTHESIZE.format(
            question=question, decision=decision or "general research", domain=domain,
            findings=json.dumps(findings, default=str)))
        synthesis = res["data"] or {}
    else:
        synthesis = {
            "thesis": "Insufficient graded evidence to form a defensible thesis in local mode. "
                      "Configure SERV_API_KEY for full reasoning.",
            "confidence": "low",
            "key_findings": [f"[{f['id']}] {f['claim']} (confidence: {f['confidence']})" for f in findings],
            "caveats": ["Local heuristic grading only; no SERV reasoning was run."],
            "what_would_change_my_mind": ["Primary source confirmation plus independent corroboration."],
            "next_checks": ["Re-run with SERV_API_KEY set for full grading."],
        }
    synthesis.setdefault("thesis", "")
    synthesis.setdefault("confidence", "low")

    if client:
        validated = [a for a in client.audit if a.get("validated")]
        if not validated:
            reasoning = "local"
            errs = [a.get("error") for a in client.audit if a.get("error")]
            synthesis.setdefault("caveats", [])
            synthesis["caveats"] = list(synthesis["caveats"]) + [
                f"SERV unavailable: {errs[0] if errs else 'all reasoning calls failed'}"]
            synthesis.setdefault("thesis", "")
            if not synthesis["thesis"]:
                synthesis["thesis"] = ("Insufficient graded evidence to form a defensible thesis. "
                                       "SERV reasoning was unavailable.")
                synthesis["confidence"] = "low"

    audit = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "per_step": []}
    if client:
        audit["per_step"] = client.audit
        audit["calls"] = len(client.audit)
        audit["prompt_tokens"] = sum(a["prompt_tokens"] for a in client.audit)
        audit["completion_tokens"] = sum(a["completion_tokens"] for a in client.audit)

    return {
        "question": question, "decision": decision, "domain": domain,
        "reasoning": reasoning, "model": client.model if client else None,
        "sub_questions": sub_questions,
        "evidence": [e.model_dump() for e in evidence],
        "findings": findings, "synthesis": synthesis, "audit": audit,
        "skill": _skill_meta(domain),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def verify_claim(claim: str, domain: str = "auto") -> dict:
    """Grade a single claim against gathered evidence."""
    domain = _detect_domain(claim) if domain == "auto" else domain
    evidence = sources.web_search(claim, max_results=5)
    if domain == "robinhood-chain":
        for tok in _tickers_and_addresses(claim, domain):
            evidence.extend(sources.robinhood_token(tok))
    client = _serv_client(domain)
    if client:
        for ev in evidence[:12]:
            res = client.reason("classify_source", prompts.CLASSIFY_SOURCE.format(
                url=ev.url, title=ev.title, excerpt=ev.excerpt[:800], question=claim))
            d = res["data"] or {}
            ev.interest = d.get("interest", ev.interest)
            try:
                ev.relevance = float(d.get("relevance", 0.0) or 0.0)
            except (TypeError, ValueError):
                pass
        res = client.reason("grade_claim", prompts.GRADE_CLAIM.format(
            claim=claim,
            evidence=json.dumps([e.model_dump(exclude={"raw"}) for e in evidence], default=str)))
        grade = res["data"]
        reasoning, model = "serv", client.model
        if not any(a.get("validated") for a in client.audit):
            reasoning = "local"
            errs = [a.get("error") for a in client.audit if a.get("error")]
            grade = grade or {}
            grade.setdefault("basis", "")
            grade["basis"] = (grade["basis"] +
                              f" SERV unavailable: {errs[0] if errs else 'all calls failed'}").strip()
            if not grade.get("confidence"):
                grade = _fallback_grade("c1", claim, evidence)
                grade["basis"] += f" SERV unavailable: {errs[0] if errs else 'all calls failed'}"
        audit = {"calls": len(client.audit),
                 "prompt_tokens": sum(a["prompt_tokens"] for a in client.audit),
                 "completion_tokens": sum(a["completion_tokens"] for a in client.audit),
                 "per_step": client.audit}
    else:
        grade = _fallback_grade("c1", claim, evidence)
        reasoning, model = "local", None
        audit = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "per_step": []}
    return {
        "question": claim, "decision": "", "domain": domain,
        "reasoning": reasoning, "model": model, "sub_questions": [],
        "evidence": [e.model_dump() for e in evidence],
        "findings": [grade],
        "synthesis": {"thesis": grade.get("basis", ""), "confidence": grade.get("confidence", "low"),
                      "key_findings": [], "caveats": [], "what_would_change_my_mind": [],
                      "next_checks": []},
        "audit": audit, "skill": _skill_meta(domain),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def render_markdown(report: dict) -> str:
    """Render a report dict as markdown."""
    s = report.get("synthesis", {})
    reasoning = report.get("reasoning", "local")
    model = report.get("model") or "none"
    skill = report.get("skill") or {}
    pack = skill.get("domain_pack")
    if pack:
        base = pack.rsplit("/", 1)[-1]
        pack_name = pack.rsplit("/", 2)[-2] if base == "SKILL.md" else base.removesuffix(".md")
    else:
        pack_name = None
    method_line = (f"**Method:** Seeri skill (domain pack: {pack_name or 'none'})"
                   if skill.get("dir") else "**Method:** built-in fallbacks (skill not found)")
    lines = [
        f"# Seeri Research Report",
        f"",
        f"**Question:** {report.get('question', '')}",
        f"**Domain:** {report.get('domain', 'auto')} | **Confidence:** {s.get('confidence', 'low')} | "
        f"**Reasoning:** {reasoning} ({model})",
        method_line,
        f"",
        f"## Thesis",
        f"",
        s.get("thesis", ""),
        f"",
        f"## Key Findings",
        f"",
    ]
    for kf in s.get("key_findings", []):
        lines.append(f"- {kf}")
    lines += ["", "## Evidence Grid", "", "| id | claim | confidence | supporting | gaps |",
              "| --- | --- | --- | --- | --- |"]
    for f in report.get("findings", []):
        sup = ", ".join(f.get("supporting", []))
        gaps = "; ".join(f.get("gaps", []))
        claim = str(f.get("claim", "")).replace("|", "\\|")[:120]
        lines.append(f"| {f.get('id', '')} | {claim} | {f.get('confidence', '')} | {sup} | {gaps} |")
    checklist = s.get("domain_checklist") or []
    if checklist:
        lines += ["", "## Domain checklist", "",
                  "| row | status | findings |", "| --- | --- | --- |"]
        for row in checklist:
            ids = ", ".join(row.get("finding_ids", []))
            lines.append(f"| {row.get('row','')} | {row.get('status','')} | {ids} |")
    lines += ["", "## Sources", ""]
    for e in report.get("evidence", []):
        lines.append(f"- `{e['id']}` [{e.get('category','?')}/{e.get('interest','?')}/{e.get('freshness','?')}] "
                     f"[{e.get('title','')[:80]}]({e.get('url','')})")
    lines += ["", "## Caveats", ""]
    for c in s.get("caveats", []):
        lines.append(f"- {c}")
    open_qs = s.get("open_questions") or []
    if open_qs:
        lines += ["", "## Open questions", ""]
        for o in open_qs:
            lines.append(f"- {o}")
    lines += ["", "## What would change my mind", ""]
    for w in s.get("what_would_change_my_mind", []):
        lines.append(f"- {w}")
    lines += ["", "## Next checks", ""]
    for n in s.get("next_checks", []):
        lines.append(f"- {n}")
    a = report.get("audit", {})
    lines += ["", "---",
              f"Audit: {a.get('calls', 0)} SERV calls, {a.get('prompt_tokens', 0)} prompt / "
              f"{a.get('completion_tokens', 0)} completion tokens.",
              "Not investment, legal, or tax advice."]
    return "\n".join(lines)
