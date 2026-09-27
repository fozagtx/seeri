# Chapter 2: Core Technical Concepts

## Core Idea
Memecoin trading sits on blockchain mechanics: wallets, liquidity pools, slippage, token authorities, and supply distribution. A trader who does not understand these mechanics is easy prey for avoidable scams and bad fills.

## Frameworks Introduced
- **Blockchain as public logbook**: transactions are recorded into blocks, validated, and chained.
  - When to use: when explaining why wallet activity and token history can be audited.
  - How: follow transactions through explorers such as Solscan rather than relying on claims.
- **Liquidity pool equation**: price moves because buys and sells change the ratio of paired assets.
  - When to use: when judging slippage, TVL, market cap, or sell impact.
  - How: estimate whether the pool has enough depth to absorb your intended entry or exit.
- **LP safety check**: a token outside familiar launchpads needs basic authority and liquidity checks.
  - When to use: before buying tokens not created through trusted launch infrastructure.
  - How: check LP lock/burn status, mint authority, freeze authority, holder concentration, and known scanner results.
- **Bundling detection stack**: one wallet may control many wallets.
  - When to use: before entering low-cap or fresh tokens.
  - How: combine Bubblemaps clusters, top-holder percentage, fresh wallet icons, funding origin, chart shape, market-cap-to-volume, and fee data.

## Key Concepts
- **Blockchain**: public transaction database maintained by validators.
- **Wallet**: crypto account controlled by keys or seed phrase.
- **Token/Coin**: digital asset tradable on a chain.
- **Gas fee**: transaction cost paid to use the network.
- **Liquidity Pool (LP)**: paired assets that enable swaps.
- **Contract Address (CA)**: the unique token or pool identifier used to find the asset.
- **Market Cap (MC)**: token supply multiplied by token price.
- **Total Value Locked (TVL)**: value held inside a liquidity pool or protocol.
- **Slippage**: worse average execution caused by price moving during or because of the trade.
- **Mint authority**: permission to create more tokens.
- **Freeze authority**: permission that can restrict token movement.
- **Honeypot**: a token engineered to lure buys and trap or destroy buyers.
- **Bundling**: one entity controlling supply through multiple wallets.

## Mental Models
- Think of a liquidity pool as a **two-sided box**: pushing one asset in pulls the other out and changes the price.
- Use **pool depth before position size**: your position is only real if the pool can absorb both your entry and exit.
- Treat **fresh low-volume up-only charts** as suspicious until proven otherwise.
- Think of **bundles as hidden gravity**: if one actor controls enough supply, they decide when the chart falls.

## Anti-patterns
- **Ignoring authorities**: buying tokens with unsafe mint/freeze or LP control can make the chart irrelevant.
- **Confusing holder count with distribution**: many wallets can still be one operator.
- **Buying beautiful low-volume charts**: smooth up-only action with few holders often means coordinated manipulation.
- **Assuming a bundle is always bad**: supply control can be strategic for teams, but it must be priced as risk.

## Worked Example
A fresh token appears with a strong chart. Before buying, check whether the LP is locked, mint authority is disabled, and top holders are not clustered. If a single linked cluster controls a crushing share, funding origins match, volume is low relative to MC, and candles look mechanically uniform, the trade should be avoided or sized as extreme risk.

## Key Takeaways
1. Learn LP mechanics before trading low-cap coins.
2. Slippage is normal, but hidden sell impact can erase paper gains.
3. LP lock and disabled mint/freeze authority are baseline safety checks.
4. Bundling is the fastest way many on-chain traders lose money.
5. Use multiple signals for supply-control risk; no one tool is enough.

## Connects To
- **Ch 3**: supply and attention determine which coin category you are trading.
- **Ch 6**: uses Solscan and app tooling to inspect wallets and tokens.
- **Ch 12**: expands authority, phishing, and custody safety.
