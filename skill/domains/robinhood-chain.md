# Domain Pack: Robinhood Chain

Use this pack when the question involves Robinhood Chain, a Stock Token, a chain-native launch, or an agent acting on the chain.

## Facts To Anchor On

| Item | Mainnet | Testnet |
| --- | --- | --- |
| Chain ID | 4663 | 46630 |
| Public RPC | `https://rpc.mainnet.chain.robinhood.com` | `https://rpc.testnet.chain.robinhood.com` |
| Explorer | `https://robinhoodchain.blockscout.com` | `https://explorer.testnet.chain.robinhood.com` |
| Gas token | ETH | ETH |

Robinhood Chain launched on mainnet in July 2026. Treat anything that predates that as pre-launch or testnet and label it.

## Primary Sources, In Order Of Trust

1. Chain state: Blockscout API (`/api/v2/tokens/{address}`, `/api/v2/addresses/{address}`, `/api/v2/tokens/{address}/holders`, `/api/v2/search?q=`), or `eth_call` against the public RPC. This is the only category that can confirm a contract exists, its supply, its holders, and its transfers.
2. Price feeds: Chainlink feeds on-chain for Stock Tokens; DEX price from Uniswap v3 pools. The gap between them is the premium or discount and is a claim worth triangulating.
3. Market aggregators: GeckoTerminal (pools, volume, liquidity), DefiLlama (chain TVL, protocol TVL). These are indexers, not primary state. Cite them as such.
4. Robinhood's own announcements and docs: project-reported. Useful for intent and product claims; not proof of usage.
5. Social and news: interested or secondary. Never the only source for a claim.

## Verify First

- Contract identity. Tickers collide on purpose. Resolve the ticker through the explorer or a registry, confirm the address, and check creation date and verified source before anything else.
- What a Stock Token represents. Tokenized equity exposure is not direct share ownership unless the issuer documentation proves it. State what the token holder actually has a claim on and cite the document.
- Multipliers and splits. Stock Token balances may carry a multiplier. A raw balance is not a share count until the multiplier is applied.
- Liquidity depth versus headline price. A price from a thin pool is a low-confidence price. Report liquidity alongside it.
- Oracle versus DEX. If the two disagree by more than a few percent, that is a finding, not noise.

## Traps

- Recently deployed tokens that reuse an existing ticker. Treat ticker matches as candidates until the contract address is confirmed against an official registry.
- Headline volume without liquidity context. Report pool count and reserves alongside it.
- Confusing Robinhood the broker, Robinhood Chain the network, and Robinhood MCP the agent tooling. Say which one the claim is about.
- Assuming a launch platform's listing is a quality signal. It is only proof of a deployment.

## Existing Agent Tooling

Read-only MCP servers already exist for the chain (`robinhood-chain-mcp`, `hood-mcp`). They return chain state, token metadata, quotes, and pairs. They do not verify claims or grade evidence. Seeri sits above them: use their output as source category 1 or 2 and grade it.

## Output Additions

When the subject is on Robinhood Chain, the evidence grid must include rows for: contract identity, what the token represents, on-chain holders and supply, oracle price, DEX price and liquidity, and the premium or discount between them.
