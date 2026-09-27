"""Evidence fetchers. All free, no API keys required."""

import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser

import httpx
from pydantic import BaseModel, Field

UA = "Seeri-Research/1.0 (+https://huggingface.co/spaces/pima5/seeri)"
TIMEOUT = httpx.Timeout(10.0)

ROBINHOOD_MAINNET = "https://robinhoodchain.blockscout.com/api/v2"
ROBINHOOD_TESTNET = "https://explorer.testnet.chain.robinhood.com/api/v2"
ROBINHOOD_CHAIN_ID = 4663
ROBINHOOD_EXPLORER = "https://robinhoodchain.blockscout.com"
ROBINHOOD_RPC = "https://rpc.mainnet.chain.robinhood.com"
GECKO_BASE = "https://api.geckoterminal.com/api/v2"


class Evidence(BaseModel):
    """A single piece of fetched evidence."""

    id: str
    url: str
    title: str
    excerpt: str
    category: str = "unknown"
    interest: str = "independent"
    freshness: str = "undated"
    relevance: float = 0.0
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw: dict | None = None


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def _get(url: str, **kwargs) -> httpx.Response:
    return httpx.get(url, timeout=TIMEOUT, follow_redirects=True,
                     headers={"User-Agent": UA}, **kwargs)


_GT_CACHE: dict[str, tuple[float, object]] = {}
_GT_TTL = 300.0


def _gecko_get(path: str, params: dict | None = None):
    """GeckoTerminal GET with a 300s in-process cache and one 429 retry."""
    url = f"{GECKO_BASE}{path}"
    key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    hit = _GT_CACHE.get(key)
    if hit and time.time() - hit[0] < _GT_TTL:
        return hit[1]
    data = None
    for attempt in range(2):
        try:
            r = _get(url, params=params)
            if r.status_code == 429:
                if attempt == 0:
                    time.sleep(2)
                    continue
                break
            if r.status_code == 200:
                data = r.json()
            break
        except Exception:
            break
    if data is not None:
        _GT_CACHE[key] = (time.time(), data)
    return data


def _rpc_call(method: str, params: list):
    try:
        r = httpx.post(ROBINHOOD_RPC, timeout=TIMEOUT,
                       json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        if r.status_code == 200:
            return r.json().get("result")
    except Exception:
        pass
    return None


def _eth_call(address: str, selector: str):
    return _rpc_call("eth_call", [{"to": address, "data": selector}, "latest"])


def _decode_uint(hexdata) -> int | None:
    if not hexdata or hexdata == "0x":
        return None
    try:
        return int(hexdata, 16)
    except (ValueError, TypeError):
        return None


def _decode_abi_string(hexdata) -> str | None:
    """Decode an ABI-encoded string (or bytes32-style short string)."""
    if not hexdata or hexdata == "0x":
        return None
    raw = hexdata[2:] if hexdata.startswith("0x") else hexdata
    try:
        if len(raw) >= 128:
            strlen = int(raw[64:128], 16)
            return bytes.fromhex(raw[128:128 + strlen * 2]).decode("utf-8", "replace")
        if len(raw) == 64:
            return bytes.fromhex(raw).rstrip(b"\x00").decode("utf-8", "replace")
        strlen = int(raw[:64], 16)
        return bytes.fromhex(raw[64:64 + strlen * 2]).decode("utf-8", "replace")
    except (ValueError, IndexError):
        return None


def _token_identity(address: str) -> dict | None:
    """ERC-20 identity via JSON-RPC eth_call/eth_getCode on Robinhood mainnet."""
    code = _rpc_call("eth_getCode", [address, "latest"])
    if not code or code == "0x":
        return None
    name = _decode_abi_string(_eth_call(address, "0x06fdde03")) or ""
    symbol = _decode_abi_string(_eth_call(address, "0x95d89b41")) or ""
    decimals = _decode_uint(_eth_call(address, "0x313ce567"))
    supply = _decode_uint(_eth_call(address, "0x18160ddd"))
    human = None
    if supply is not None:
        human = supply / (10 ** decimals) if decimals else float(supply)
    return {"address": address, "name": name, "symbol": symbol,
            "decimals": decimals, "total_supply": supply, "total_supply_human": human}


def web_search(query: str, max_results: int = 6) -> list[Evidence]:
    """DuckDuckGo text search, then fetch and strip each result page."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []
    def _fetch_excerpt(hit) -> str:
        url = hit.get("href") or hit.get("link") or ""
        try:
            page = _get(url)
            ct = page.headers.get("content-type", "")
            if "text" in ct or "html" in ct:
                text = _html_to_text(page.text)
                if text:
                    return text[:1500]
        except Exception:
            pass
        return hit.get("body") or ""

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as pool:
        excerpts = list(pool.map(_fetch_excerpt, hits))
    out: list[Evidence] = []
    for i, (hit, excerpt) in enumerate(zip(hits, excerpts)):
        url = hit.get("href") or hit.get("link") or ""
        out.append(Evidence(
            id=f"web{i+1}", url=url, title=hit.get("title") or url, excerpt=excerpt[:1500],
            category="news", interest="independent", freshness="undated",
        ))
    return out


def _robinhood_blockscout(query: str, base: str) -> list[Evidence]:
    out: list[Evidence] = []
    tag = f"Robinhood Chain (chain id {ROBINHOOD_CHAIN_ID}, explorer {ROBINHOOD_EXPLORER})"

    def ev(eid, url, title, excerpt, raw=None):
        out.append(Evidence(id=eid, url=url, title=title,
                            excerpt=f"[{tag}] {excerpt}"[:1500],
                            category="chain_state", interest="independent",
                            freshness="current", raw=raw))

    if re.fullmatch(r"0x[a-fA-F0-9]{40}", query.strip()):
        addr = query.strip()
        try:
            r = _get(f"{base}/tokens/{addr}")
            if r.status_code == 200:
                d = r.json()
                ev("rh_token", f"{ROBINHOOD_EXPLORER}/token/{addr}",
                   f"Token {d.get('name', '?')} ({d.get('symbol', '?')})",
                   f"name={d.get('name')} symbol={d.get('symbol')} decimals={d.get('decimals')} "
                   f"total_supply={d.get('total_supply')} holders={d.get('holders')} "
                   f"address={addr}", d)
        except Exception:
            pass
        try:
            r = _get(f"{base}/tokens/{addr}/counters")
            if r.status_code == 200:
                d = r.json()
                ev("rh_counters", f"{ROBINHOOD_EXPLORER}/token/{addr}",
                   f"Token counters for {addr[:10]}...",
                   f"transfers={d.get('transfers_count')} holders={d.get('token_holders_count')}", d)
        except Exception:
            pass
        try:
            r = _get(f"{base}/addresses/{addr}")
            if r.status_code == 200:
                d = r.json()
                ev("rh_address", f"{ROBINHOOD_EXPLORER}/address/{addr}",
                   f"Address {addr[:10]}...",
                   f"is_contract={d.get('is_contract')} balance={d.get('coin_balance')} "
                   f"tx_count={d.get('transactions_count', d.get('tx_count'))}", d)
        except Exception:
            pass
        return out

    try:
        r = _get(f"{base}/search", params={"q": query})
        if r.status_code != 200:
            return out
        data = r.json()
        items = data.get("items", data if isinstance(data, list) else [])
        tokens = [it for it in items if it.get("type") in ("token", None)
                  and (it.get("symbol") or it.get("name") or it.get("address"))]
        note = f"{len(tokens)} tokens match this ticker. " if len(tokens) > 1 else ""
        for i, it in enumerate(tokens[:8]):
            addr = it.get("address") or it.get("address_hash") or ""
            ev(f"rh_search{i+1}",
               f"{ROBINHOOD_EXPLORER}/token/{addr}" if addr else ROBINHOOD_EXPLORER,
               f"{it.get('name', '?')} ({it.get('symbol', '?')})",
               f"{note}name={it.get('name')} symbol={it.get('symbol')} "
               f"address={addr} type={it.get('type')} "
               f"total_supply={it.get('total_supply')} holders={it.get('holders_count', it.get('holders'))}", it)
    except Exception:
        pass
    return out


def _robinhood_gecko_pools(query: str) -> list[dict]:
    """Distinct base-token addresses + pool stats from GeckoTerminal search."""
    data = _gecko_get("/search/pools", params={"query": query, "network": "robinhood"})
    if not data:
        return []
    seen: dict[str, dict] = {}
    for p in data.get("data", []):
        a = p.get("attributes", {})
        base_id = (p.get("relationships", {}).get("base_token", {})
                   .get("data", {}) or {}).get("id", "")
        addr = base_id.split("_", 1)[1] if "_" in base_id else base_id
        if not re.fullmatch(r"0x[a-fA-F0-9]{40}", addr or "") or addr in seen:
            continue
        seen[addr] = {
            "address": addr,
            "pool_name": a.get("name", "?"),
            "pool_address": a.get("address", ""),
            "reserve_in_usd": a.get("reserve_in_usd"),
            "volume_h24": (a.get("volume_usd") or {}).get("h24"),
        }
        if len(seen) >= 6:
            break
    return list(seen.values())


def robinhood_token(query: str, network: str = "mainnet") -> list[Evidence]:
    """Token dossier on Robinhood Chain. Blockscout first; GeckoTerminal+RPC fallback."""
    base = ROBINHOOD_TESTNET if network == "testnet" else ROBINHOOD_MAINNET
    tag = f"Robinhood Chain (chain id {ROBINHOOD_CHAIN_ID}, explorer {ROBINHOOD_EXPLORER})"

    out = _robinhood_blockscout(query, base)
    if out or network == "testnet":
        return out

    # Mainnet fallback: Blockscout is Cloudflare-gated, use GeckoTerminal + RPC.
    is_addr = bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", query.strip()))
    if is_addr:
        addr = query.strip()
        ident = _token_identity(addr)
        if not ident:
            return []
        excerpt = (f"symbol={ident['symbol']} name={ident['name']} address={addr} "
                   f"decimals={ident['decimals']} totalSupply={ident['total_supply_human']} "
                   f"[{tag}]")
        data = _gecko_get(f"/networks/robinhood/tokens/{addr}")
        if data:
            ga = data.get("data", {}).get("attributes", {})
            excerpt += (f" price_usd={ga.get('price_usd')} fdv_usd={ga.get('fdv_usd')} "
                        f"volume_24h={(ga.get('volume_usd') or {}).get('h24')}")
            ident.update({"price_usd": ga.get("price_usd"), "fdv_usd": ga.get("fdv_usd")})
        return [Evidence(id="rh_token", url=f"{ROBINHOOD_EXPLORER}/token/{addr}",
                         title=f"{ident['name'] or '?'} ({ident['symbol'] or '?'}) on Robinhood Chain",
                         excerpt=excerpt[:1500], category="chain_state",
                         interest="independent", freshness="current", raw=ident)]

    pools = _robinhood_gecko_pools(query)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as pool:
        idents = list(pool.map(lambda p: _token_identity(p["address"]), pools))
    tokens = [(p, i) for p, i in zip(pools, idents) if i]
    if not tokens:
        return []

    collision = ""
    if len(tokens) > 1:
        members = ", ".join(f"{i['symbol'] or '?'} ({i['address'][:10]}…)" for _, i in tokens[:3])
        collision = (f"TICKER COLLISION: {len(tokens)} distinct tokens match '{query}' "
                     f"on Robinhood Chain: {members}, …. ")
        full = ", ".join(f"{i['symbol'] or '?'} ({i['address']})" for _, i in tokens)
        out.append(Evidence(
            id="collision", url=ROBINHOOD_EXPLORER,
            title=f"Ticker collision: {len(tokens)} tokens match '{query}'",
            excerpt=f"TICKER COLLISION: {len(tokens)} distinct tokens match '{query}' "
                    f"on Robinhood Chain: {full}. "
                    "Verify the official issuer registry before treating any match as canonical.",
            category="chain_state", interest="independent", freshness="current",
            raw={"matches": [i for _, i in tokens]}))
    for idx, (pool, ident) in enumerate(tokens):
        excerpt = (collision +
                   f"symbol={ident['symbol']} name={ident['name']} address={ident['address']} "
                   f"decimals={ident['decimals']} totalSupply={ident['total_supply_human']} "
                   f"pool={pool['pool_name']} liquidity_usd={pool['reserve_in_usd']} "
                   f"volume_24h_usd={pool['volume_h24']} pools_seen={len(tokens)} [{tag}]")
        out.append(Evidence(
            id=f"rh_token{idx+1}", url=f"{ROBINHOOD_EXPLORER}/token/{ident['address']}",
            title=f"{ident['name'] or '?'} ({ident['symbol'] or '?'}) on Robinhood Chain",
            excerpt=excerpt[:1500], category="chain_state",
            interest="independent", freshness="current",
            raw={**ident, **pool}))
    return out


def geckoterminal_token(network_slug: str, address: str) -> list[Evidence]:
    """Token info and top pools from GeckoTerminal."""
    if network_slug == "robinhood":
        slug = _gecko_slug()
        if not slug:
            return []
        network_slug = slug
    out: list[Evidence] = []
    data = _gecko_get(f"/networks/{network_slug}/tokens/{address}")
    if data:
        a = data.get("data", {}).get("attributes", {})
        out.append(Evidence(
            id="gt_token",
            url=f"https://www.geckoterminal.com/{network_slug}/tokens/{address}",
            title=f"GeckoTerminal: {a.get('name', '?')} ({a.get('symbol', '?')})",
            excerpt=f"price_usd={a.get('price_usd')} fdv={a.get('fdv_usd')} "
                    f"market_cap={a.get('market_cap_usd')} volume_24h={(a.get('volume_usd') or {}).get('h24')} "
                    f"network={network_slug}"[:1500],
            category="market_data", interest="independent", freshness="current",
            raw=a))
    data = _gecko_get(f"/networks/{network_slug}/tokens/{address}/pools")
    if data:
        for i, p in enumerate(data.get("data", [])[:3]):
            a = p.get("attributes", {})
            out.append(Evidence(
                id=f"gt_pool{i+1}",
                url=f"https://www.geckoterminal.com/{network_slug}/pools/{a.get('address', p.get('id', ''))}",
                title=f"Pool: {a.get('name', '?')}",
                excerpt=f"pool={a.get('name')} reserve_usd={a.get('reserve_in_usd')} "
                        f"volume_24h={(a.get('volume_usd') or {}).get('h24')} "
                        f"price_change_24h={(a.get('price_change_percentage') or {}).get('h24')}"[:1500],
                category="market_data", interest="independent", freshness="current",
                raw=a))
    return out


_GECKO_SLUG_CACHE: dict[str, str | None] = {}


def _gecko_slug() -> str | None:
    if "robinhood" in _GECKO_SLUG_CACHE:
        return _GECKO_SLUG_CACHE["robinhood"]
    slug = "robinhood"
    data = _gecko_get("/networks/robinhood")
    if not data or not data.get("data"):
        slug = None
        try:
            for page in range(1, 6):
                d = _gecko_get("/networks", params={"page": page})
                nets = (d or {}).get("data", [])
                for n in nets:
                    if "robinhood" in (n.get("attributes", {}).get("name") or n.get("id", "")).lower():
                        slug = n["id"]
                        break
                if slug or not nets:
                    break
        except Exception:
            pass
    _GECKO_SLUG_CACHE["robinhood"] = slug
    return slug


def defillama_protocol(name: str) -> list[Evidence]:
    """Protocol TVL/chains from DefiLlama, plus chain-TVL lookup."""
    out: list[Evidence] = []
    q = name.strip().lower()
    try:
        r = _get("https://api.llama.fi/protocols")
        if r.status_code == 200:
            protos = r.json()
            match = next((p for p in protos if p.get("slug", "").lower() == q), None)
            if not match:
                match = next((p for p in protos
                              if q in p.get("name", "").lower() or q in p.get("slug", "").lower()), None)
            if match:
                slug = match["slug"]
                d = _get(f"https://api.llama.fi/protocol/{slug}")
                detail = d.json() if d.status_code == 200 else {}
                tvl = detail.get("tvl")
                if isinstance(tvl, list) and tvl:
                    tvl = tvl[-1].get("totalLiquidityUSD")
                out.append(Evidence(
                    id="dl_protocol",
                    url=f"https://defillama.com/protocol/{slug}",
                    title=f"DefiLlama: {match.get('name', slug)}",
                    excerpt=f"name={match.get('name')} slug={slug} tvl={tvl or match.get('tvl')} "
                            f"chains={detail.get('chains') or match.get('chains')} "
                            f"category={match.get('category')}"[:1500],
                    category="market_data", interest="independent", freshness="current",
                    raw={"protocol": match}))
    except Exception:
        pass
    try:
        r = _get("https://api.llama.fi/v2/chains")
        if r.status_code == 200:
            chain = next((c for c in r.json()
                          if q in str(c.get("name", "")).lower()), None)
            if chain:
                out.append(Evidence(
                    id="dl_chain",
                    url=f"https://defillama.com/chain/{chain.get('name')}",
                    title=f"DefiLlama chain: {chain.get('name')}",
                    excerpt=f"chain={chain.get('name')} tvl={chain.get('tvl')} "
                            f"tokenSymbol={chain.get('tokenSymbol')}"[:1500],
                    category="market_data", interest="independent", freshness="current",
                    raw=chain))
    except Exception:
        pass
    return out
