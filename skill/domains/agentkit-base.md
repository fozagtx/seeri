# Domain Pack: Coinbase AgentKit and Base

Use this pack when the question involves an agent with a wallet, Coinbase AgentKit, the Coinbase Developer Platform, or an asset or protocol on Base.

## Primary Sources, In Order Of Trust

1. Chain state on Base: Basescan or Blockscout API, or `eth_call` against a Base RPC. Confirms contracts, balances, holders, transfers.
2. Coinbase Developer Platform docs and the AgentKit repository: the authority on what AgentKit can and cannot do (wallet providers, action providers, supported networks). Project-reported for adoption claims.
3. Market aggregators: DefiLlama (Base chain and protocol TVL), GeckoTerminal (pools). Indexers, not primary state.
4. Protocol docs and audits for anything the agent would touch (lending, DEX, bridges). Project-reported unless the audit is by a named third party.
5. Social and news: secondary.

## Verify First

- Custody model. Who holds the key: the developer, a CDP-managed wallet, or the user. This determines every risk statement that follows.
- Network. Base mainnet versus Base Sepolia. Testnet activity is not adoption.
- Action scope. Which action providers are enabled. An agent that can only read is a different risk class from one that can transfer.
- Spend controls. Whether any cap, allowlist, or confirmation gate exists. Absence is a finding.

## Traps

- Counting testnet transactions or faucet balances as usage.
- Treating a wallet address with activity as proof that an agent, rather than a person, controls it.
- Quoting AgentKit feature lists as if they were deployed integrations.

## Output Additions

Include grid rows for: custody model, network, enabled actions, spend controls, and the audit status of any protocol the agent interacts with.
