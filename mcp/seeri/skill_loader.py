"""Loads the Seeri skill (skill/ directory) so the MCP server reasons with the skill's own method.

The skill files are the source of truth. This module reads them at runtime and hands them to
SERV as method context, so a change to the skill changes how the server researches.
"""

import os
import re
from functools import lru_cache

# Repo layout: <root>/skill and <root>/mcp/seeri/skill_loader.py. Vendored copy for the Space: <mcp>/skill.
_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("SEERI_SKILL_DIR", ""),
    os.path.join(_HERE, "..", "skill"),
    os.path.join(_HERE, "..", "..", "skill"),
]

METHOD_FILES = ["SKILL.md", "research-workflow.md", "source-map.md", "evidence-grid.md", "reasoning-serv.md"]
SYNTHESIS_FILES = ["article-synthesis.md"]

DOMAIN_FILES = {
    "robinhood-chain": "domains/robinhood-chain.md",
    "agentkit-base": "domains/agentkit-base.md",
    "ixs-rwa-vaults": "domains/ixs-rwa-vaults.md",
    "memecoin-markets": "domains/memecoin-markets/SKILL.md",
}

# Domain keyword routing, mirrors the "Domain Packs" section of SKILL.md.
DOMAIN_KEYWORDS = {
    "robinhood-chain": r"robinhood|\bhood\b|stock token",
    "agentkit-base": r"agentkit|\bbase\b|coinbase",
    "ixs-rwa-vaults": r"\bixs\b|\brwa\b|vault|treasur",
    "memecoin-markets": r"pump|memecoin|meme coin|launch|bundl|snipe",
}


def skill_dir() -> str | None:
    for c in _CANDIDATES:
        if c and os.path.isfile(os.path.join(c, "SKILL.md")):
            return os.path.abspath(c)
    return None


def _read(rel: str) -> str:
    d = skill_dir()
    if not d:
        return ""
    try:
        with open(os.path.join(d, rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)


def detect_domain(text: str) -> str:
    t = text.lower()
    for name, pattern in DOMAIN_KEYWORDS.items():
        if re.search(pattern, t):
            return name
    return "general"


@lru_cache(maxsize=None)
def method_context() -> str:
    """The skill's core method: SKILL.md, workflow, source map, evidence grid, SERV rules."""
    parts = []
    for rel in METHOD_FILES:
        body = _strip_frontmatter(_read(rel)).strip()
        if body:
            parts.append(f"<!-- skill/{rel} -->\n{body}")
    return "\n\n".join(parts)


@lru_cache(maxsize=None)
def domain_context(domain: str) -> str:
    """The domain pack for a subject area, or empty for general."""
    rel = DOMAIN_FILES.get(domain)
    if not rel:
        return ""
    body = _strip_frontmatter(_read(rel)).strip()
    return f"<!-- skill/{rel} -->\n{body}" if body else ""


@lru_cache(maxsize=None)
def synthesis_context() -> str:
    parts = [_strip_frontmatter(_read(rel)).strip() for rel in SYNTHESIS_FILES]
    return "\n\n".join(p for p in parts if p)


def domain_output_rows(domain: str) -> list[str]:
    """Rows the domain pack says the evidence grid must include ("Output Additions" section)."""
    ctx = domain_context(domain)
    m = re.search(r"## Output Additions\n(.*?)(?:\n## |\Z)", ctx, flags=re.DOTALL)
    if not m:
        return []
    text = m.group(1)
    rows = re.search(r"rows for:\s*(.*?)(?:\.\s|\.$|\n\n)", text, flags=re.DOTALL)
    if not rows:
        return []
    items = re.split(r",\s*(?![^()]*\))", rows.group(1).replace("\n", " "))
    out = []
    for i in items:
        i = re.sub(r"^and\s+", "", i.strip(" ."))
        if i:
            out.append(i)
    return out


def list_files() -> list[str]:
    d = skill_dir()
    if not d:
        return []
    out = []
    for root, _, files in os.walk(d):
        for fn in files:
            if fn.endswith(".md"):
                out.append(os.path.relpath(os.path.join(root, fn), d))
    return sorted(out)


def read_file(rel: str) -> str:
    rel = rel.strip().lstrip("/")
    if ".." in rel.split("/") or not rel.endswith(".md"):
        return ""
    return _read(rel)
