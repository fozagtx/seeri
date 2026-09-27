# Chapter 6: Trading Platforms & Tools

## Core Idea
Tools should reduce friction and improve information quality, but they become dangerous when treated as automatic buy signals. Use trading terminals, wallet apps, explorers, and social feeds to verify, not outsource judgment.

## Frameworks Introduced
- **Friction reduction stack**: a beginner-friendly terminal can simplify cross-chain buying and social discovery.
  - When to use: when setting up trading infrastructure.
  - How: use the app for execution, social notes, holdings visibility, and chain abstraction while keeping key backups secure.
- **Wallet discovery workflow**: identify a trader's wallet from app holdings and chain explorer data.
  - When to use: when you want to monitor a credible trader or whale.
  - How: find token chain, copy CA, inspect holders on the chain explorer, match token amount and recent transactions.
- **Blockchain workshop separation**: keep trading wallets separate from wallets used to connect to random dapps.
  - When to use: before browsing dapps, claiming rent, or testing tools.
  - How: use a separate Phantom or similar wallet for exploration; keep your active trading wallet limited.
- **Social-layer skepticism**: app follows and notifications are information, not orders.
  - When to use: when a high-followed trader buy notification hits.
  - How: consider side wallets, private positions, and the possibility that public app activity is used to create exit liquidity.

## Key Concepts
- **Trading terminal**: app or web interface used for buying, selling, charting, and discovery.
- **Bridge**: mechanism to move value across chains.
- **Solscan/Etherscan**: chain explorers for inspecting wallets, transactions, and token holders.
- **Token account**: Solana account created to hold a specific token for a wallet.
- **Rent reclaim**: closing empty token accounts to recover locked SOL.
- **Private key export**: obtaining wallet keys for backup or import into another wallet app.

## Mental Models
- Treat **apps as dashboards**, not brains.
- Use **chain explorers as ground truth** when people make claims.
- Think of **wallet separation as blast-radius control**: one compromised wallet should not drain the whole setup.
- Treat **public buys by followed accounts as potentially staged** until verified.

## Anti-patterns
- **Not backing up private keys**: losing login access can strand funds if keys are not saved.
- **Using one wallet for everything**: trading, browsing, dapps, and long-term storage should not share the same risk surface.
- **Copying app notifications**: visible buys can be used to move followers while side wallets sell.
- **Clicking search-result dapps**: official links should be verified through trusted channels and URL checks.

## Worked Example
You notice a large app user holding a token. To find the wallet, identify the chain, copy the token CA, open the chain explorer, go to holders, and match the user's displayed token amount. Then verify with recent transactions. This lets you monitor behavior directly instead of relying on social claims.

## Key Takeaways
1. Use terminals for execution and discovery, but keep decision-making separate.
2. Export and store keys before funding meaningful amounts.
3. Learn to read chain explorers; wallet activity is harder to fake than posts.
4. Separate trading, browsing, and long-term custody wallets.
5. Social feeds are useful but can be gamed.

## Connects To
- **Ch 2**: provides the token and wallet concepts needed for explorer work.
- **Ch 5**: explains why public social signals need incentive analysis.
- **Ch 12**: gives the broader safety model for wallet and link risk.
