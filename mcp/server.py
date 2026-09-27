"""Seeri: standalone MCP server (streamable HTTP). Reasoning by SERV."""

import base64
import json
import mimetypes
import os
import re

import anyio
from mcp.server.fastmcp import FastMCP
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from seeri import pipeline, serv, skill_loader, sources

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

mcp = FastMCP(
    "Seeri",
    instructions=("Verifiable deep research for anything onchain. Reasoning by SERV. "
                  "Call seeri_skill('SKILL.md') to read the method."),
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 7860)),
    stateless_http=True,
    json_response=False,
    streamable_http_path="/mcp",
)


@mcp.tool()
async def deep_research(question: str, decision: str = "", domain: str = "auto", depth: str = "standard") -> str:
    """Run a full verifiable deep-research pass on an onchain question and return a markdown report.

    Args:
        question: The research question (e.g. a token, protocol, vault, or market claim).
        decision: Optional decision this research informs.
        domain: Domain pack hint: auto, robinhood-chain, agentkit-base, ixs-rwa-vaults, memecoin-markets, general.
        depth: quick or standard.
    """
    report = await anyio.to_thread.run_sync(
        lambda: pipeline.deep_research(question, decision, domain, depth))
    return pipeline.render_markdown(report)


@mcp.tool()
async def deep_research_json(question: str, decision: str = "", domain: str = "auto", depth: str = "standard") -> str:
    """Same as deep_research but returns the full structured report as a JSON string.

    Args:
        question: The research question.
        decision: Optional decision this research informs.
        domain: Domain pack hint: auto, robinhood-chain, agentkit-base, ixs-rwa-vaults, memecoin-markets, general.
        depth: quick or standard.
    """
    report = await anyio.to_thread.run_sync(
        lambda: pipeline.deep_research(question, decision, domain, depth))
    return json.dumps(report, indent=2, default=str)


@mcp.tool()
async def verify_claim(claim: str, domain: str = "auto") -> str:
    """Verify a single claim against gathered evidence and return a graded markdown verdict.

    Args:
        claim: The claim to verify.
        domain: Domain pack hint (auto detected if omitted).
    """
    report = await anyio.to_thread.run_sync(lambda: pipeline.verify_claim(claim, domain))
    return pipeline.render_markdown(report)


@mcp.tool()
async def robinhood_token_dossier(ticker_or_address: str, network: str = "mainnet") -> str:
    """Token dossier on Robinhood Chain: contract identity, ticker collisions, and pools.

    Args:
        ticker_or_address: Ticker symbol or 0x contract address.
        network: mainnet or testnet.
    """
    return await anyio.to_thread.run_sync(_dossier, ticker_or_address, network)


def _dossier(ticker_or_address: str, network: str) -> str:
    items = sources.robinhood_token(ticker_or_address, network)
    addresses = [e.raw.get("address") for e in items if e.raw and e.raw.get("address")]
    for addr in list(dict.fromkeys(addresses))[:3]:
        items.extend(sources.geckoterminal_token("robinhood", addr))
    if not items:
        return f"No onchain evidence found for `{ticker_or_address}` on Robinhood Chain ({network})."
    collision = next((e for e in items if e.id == "collision"), None)
    token_items = [e for e in items if e.raw and e.raw.get("symbol") is not None]
    lines = [f"# Token dossier: {ticker_or_address} ({network})", ""]
    if collision:
        lines += ["**TICKER COLLISION WARNING**", "", collision.excerpt, ""]
    if token_items:
        lines += ["## Contract identity", "",
                  "| symbol | name | address | decimals | total supply | pool | liquidity USD | 24h vol USD | explorer |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for e in token_items:
            r = e.raw or {}
            supply = r.get("total_supply_human", r.get("total_supply", ""))
            lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | [link]({}) |".format(
                r.get("symbol", ""), r.get("name", ""), r.get("address", ""),
                r.get("decimals", ""), supply,
                r.get("pool_name", ""), r.get("reserve_in_usd", ""),
                r.get("volume_h24", ""), e.url))
        lines.append("")
    lines += ["## What this token represents", "",
              "A matching ticker does not prove this is the official Stock Token. "
              "Verify the issuer registry and contract provenance before treating any match as canonical.", "",
              "## Evidence", ""]
    for e in items:
        lines += [f"### {e.title}", "", e.excerpt, "", f"Source: {e.url}", ""]
    lines.append("Not investment, legal, or tax advice.")
    return "\n".join(lines)


@mcp.tool()
async def protocol_snapshot(name: str) -> str:
    """DefiLlama snapshot for a protocol or chain: TVL, chains, category.

    Args:
        name: Protocol or chain name (e.g. uniswap, robinhood).
    """
    items = await anyio.to_thread.run_sync(sources.defillama_protocol, name)
    if not items:
        return f"No DefiLlama data found for `{name}`."
    lines = [f"# DefiLlama snapshot: {name}", ""]
    for e in items:
        lines += [f"## {e.title}", "", e.excerpt, "", f"Source: {e.url}", ""]
    lines.append("Not investment, legal, or tax advice.")
    return "\n".join(lines)


@mcp.tool()
async def web_evidence(query: str, max_results: int = 6) -> str:
    """Search the web and return a classified source list for a query.

    Args:
        query: Search query.
        max_results: Maximum number of sources to fetch (1-10).
    """
    max_results = max(1, min(int(max_results), 10))
    items = await anyio.to_thread.run_sync(lambda: sources.web_search(query, max_results))
    if not items:
        return f"No sources found for `{query}`."
    lines = [f"# Web evidence: {query}", ""]
    for e in items:
        lines.append(f"- `{e.id}` [{e.category}/{e.interest}/{e.freshness}] "
                     f"[{e.title[:80]}]({e.url})")
    lines.append("")
    lines.append("Not investment, legal, or tax advice.")
    return "\n".join(lines)


@mcp.tool()
async def seeri_skill(file: str = "SKILL.md") -> str:
    """Read the Seeri research method.

    Args:
        file: Path within the skill, e.g. SKILL.md, research-workflow.md, domains/robinhood-chain.md.
    """
    text = await anyio.to_thread.run_sync(skill_loader.read_file, file)
    if not text:
        return f"No readable skill file at `{file}`. Try list_skill_files for valid paths."
    return text


@mcp.tool()
async def list_skill_files() -> str:
    """List every markdown file in the loaded Seeri skill."""
    files = await anyio.to_thread.run_sync(skill_loader.list_files)
    if not files:
        return "Skill not found."
    d = skill_loader.skill_dir()
    return f"Skill at `{d}` ({len(files)} files):\n\n" + "\n".join(f"- {f}" for f in files)


@mcp.resource("seeri://skill/{path}")
def skill_resource(path: str) -> str:
    """A file from the Seeri skill (method or domain pack)."""
    return skill_loader.read_file(path) or f"No skill file at {path}."


@mcp.prompt()
def research_brief(question: str, decision: str = "") -> str:
    """Seeri intake template for framing a research question."""
    return (
        "Research question: " + question + "\n"
        "Decision this informs: " + (decision or "(none given)") + "\n\n"
        "Apply the Seeri method: decompose into 5-8 sub-questions covering the domain pack's "
        "required grid rows, gather evidence across at least three source categories, grade each "
        "claim (high/medium/low with basis and gaps), then synthesize a thesis, caveats, "
        "what-would-change-my-mind, and next checks. Call the deep_research tool for the automated pass.")


def _status() -> str:
    if serv.available():
        model = os.environ.get("SERV_MODEL", serv.DEFAULT_MODEL)
        serv_line = f"SERV: connected ({model})"
    else:
        serv_line = "SERV: not configured, running local reasoning"
    files = skill_loader.list_files()
    skill_line = f"Skill: loaded ({len(files)} files)" if files else "Skill: NOT FOUND"
    return f"{serv_line} | {skill_line}"


def _partner_img(filename: str, alt: str, dark: bool = False) -> str:
    path = os.path.join(ASSETS, "partners", filename)
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except OSError:
        return alt
    mime = mimetypes.guess_type(path)[0] or "image/png"
    bg = "#0B1220" if dark else "#ffffff"
    return (f'<span style="display:inline-flex;align-items:center;background:{bg};'
            f'border:1px solid #e5e5e5;border-radius:6px;padding:4px 10px;height:36px">'
            f'<img src="data:{mime};base64,{b64}" alt="{alt}" '
            f'style="height:28px;width:auto;display:block"></span>')


def _landing_html() -> str:
    try:
        with open(os.path.join(ASSETS, "logo.svg")) as f:
            logo = f.read()
        logo = re.sub(r'\s(width|height)="[^"]*"', "", logo, count=2).replace("<svg", '<svg width="72" height="72"', 1)
    except OSError:
        logo = ""
    partners = (
        '<a href="https://openserv.ai" target="_blank">' + _partner_img("openserv.svg", "OpenServ") + "</a>"
        '<span style="font-size:13px;color:#666;margin-left:14px">Research surfaces</span>'
        '<a href="https://robinhood.com" target="_blank">' + _partner_img("robinhood.svg", "Robinhood", dark=True) + "</a>"
        '<a href="https://www.coinbase.com" target="_blank">' + _partner_img("coinbase.png", "Coinbase") + "</a>"
        '<a href="https://ixs.finance" target="_blank">' + _partner_img("ixs.png", "IXS Finance") + "</a>"
    )
    tools = [
        ("deep_research", "Full pipeline: decompose, gather, classify, grade, synthesize (markdown)"),
        ("deep_research_json", "Same pipeline, structured JSON output"),
        ("verify_claim", "Grade a single claim against gathered evidence"),
        ("robinhood_token_dossier", "Contract identity, ticker collisions, pools on Robinhood Chain"),
        ("protocol_snapshot", "DefiLlama TVL, chains, category for a protocol or chain"),
        ("web_evidence", "Web search with classified source list"),
        ("seeri_skill", "Read a Seeri skill file (the method)"),
        ("list_skill_files", "List every file in the loaded skill"),
    ]
    tool_rows = "".join(f"<tr><td><code>{n}</code></td><td>{d}</td></tr>" for n, d in tools)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Seeri</title>
<style>body{{font-family:-apple-system,sans-serif;max-width:780px;margin:40px auto;padding:0 20px;color:#1a1a1a}}
code,pre{{background:#f4f2ec;padding:2px 6px;border-radius:4px}}
pre{{padding:12px;overflow-x:auto}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #eee;padding:6px 8px;text-align:left;font-size:14px}}
.status{{color:#555;font-size:14px}}</style></head><body>
<div style="width:72px">{logo}</div>
<h1>Seeri</h1>
<p>Verifiable deep research for anything onchain. Reasoning by SERV.</p>
<p class="status">{_status()}</p>
<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:6px 0">
<span style="font-size:13px;color:#666">Reasoning by</span>{partners}</div>
<h2>Connect</h2>
<p>MCP endpoint (streamable HTTP):</p>
<pre>https://pima5-seeri.hf.space/mcp</pre>
<pre>claude mcp add --transport http seeri https://pima5-seeri.hf.space/mcp</pre>
<h2>Tools</h2>
<table>{tool_rows}</table>
<p class="status">Educational research output. Not investment, legal, or tax advice.</p>
</body></html>"""


async def landing(request):
    return HTMLResponse(_landing_html())


async def health(request):
    return JSONResponse({
        "status": "ok",
        "serv": bool(serv.available()),
        "skill_files": len(skill_loader.list_files()),
    })


app = mcp.streamable_http_app()
app.routes.insert(0, Route("/health", health))
app.routes.insert(0, Route("/", landing))
