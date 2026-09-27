# Domain Pack: IXS and Licensed RWA Yield Vaults

Use this pack when the question involves IXS Finance, a real-world-asset yield vault, tokenized credit or treasuries, or an agent allocating capital into a licensed vault.

## Primary Sources, In Order Of Trust

1. Vault contract state: balances, share price, deposits and withdrawals, from the explorer of the chain the vault lives on. The only proof of assets under management.
2. Issuer and licensing documents: the license, the jurisdiction, the regulator, the legal wrapper. Read the document; do not take the word "licensed" from a landing page.
3. Underlying asset attestations: custodian statements, proof-of-reserve reports, audits. Note the attestor, the date, and whether it is independent.
4. IXS docs and Agentic Vault API references: authoritative on mechanics (eligibility, KYC gates, redemption terms). Project-reported on yield and traction.
5. Market aggregators: DefiLlama RWA category, for relative size only.
6. Social and news: secondary.

## Verify First

- What "licensed" means here. Which entity, which regulator, which activity is licensed. A license to issue is not a license to advise.
- Who can deposit. KYC or accreditation gates decide whether the yield is reachable by the user asking.
- Where the yield comes from. Underlying asset, duration, credit quality. "Yield" with no named source is a low-confidence claim.
- Redemption terms. Lockups, notice periods, gates. Liquidity is part of the risk, not a footnote.
- Share price versus quoted APY. APY is a projection; share-price history is the fact.

## Traps

- Confusing the vault token's price on a DEX with the vault's net asset value.
- Quoting a target APY as a realized return.
- Treating an audit of the smart contract as an audit of the underlying asset.

## Output Additions

Include grid rows for: license (entity, regulator, jurisdiction), eligibility, yield source, redemption terms, attestation (attestor and date), and on-chain AUM.

Seeri never recommends an allocation. It reports what is verifiable and what is not.
