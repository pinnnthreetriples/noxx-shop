"""The coins OrbChain accepts on the hosted invoice, with display metadata for
the in-app picker. Codes match OrbChain's `pay_currency` values exactly."""

ORBCHAIN_COINS = [
    {"code": "BTC", "ticker": "BTC", "name": "Bitcoin", "network": "Bitcoin", "color": "#f7931a"},
    {"code": "ETH", "ticker": "ETH", "name": "Ethereum", "network": "Ethereum", "color": "#627eea"},
    {"code": "LTC", "ticker": "LTC", "name": "Litecoin", "network": "Litecoin", "color": "#345d9d"},
    {"code": "DOGE", "ticker": "DOGE", "name": "Dogecoin", "network": "Dogecoin", "color": "#c2a633"},
    {"code": "SOL", "ticker": "SOL", "name": "Solana", "network": "Solana", "color": "#9945ff"},
    {"code": "TRX", "ticker": "TRX", "name": "TRON", "network": "TRON", "color": "#eb0029"},
    {"code": "BNB", "ticker": "BNB", "name": "BNB", "network": "BNB Smart Chain", "color": "#f0b90b"},
    {"code": "POL", "ticker": "POL", "name": "Polygon", "network": "Polygon", "color": "#8247e5"},
    {"code": "XRP", "ticker": "XRP", "name": "XRP", "network": "XRP Ledger", "color": "#23292f"},
    {"code": "TON", "ticker": "TON", "name": "Toncoin", "network": "TON", "color": "#0098ea"},
    {"code": "NOT", "ticker": "NOT", "name": "Notcoin", "network": "TON", "color": "#000000"},
    {"code": "DOGS", "ticker": "DOGS", "name": "Dogs", "network": "TON", "color": "#f0a71b"},
    {"code": "SHIB", "ticker": "SHIB", "name": "Shiba Inu", "network": "Ethereum", "color": "#f00500"},
    {"code": "DAI", "ticker": "DAI", "name": "Dai", "network": "Ethereum", "color": "#f5ac37"},
    {"code": "USDT_ERC20", "ticker": "USDT", "name": "Tether USD", "network": "Ethereum · ERC-20", "color": "#26a17b"},
    {"code": "USDT_TRC20", "ticker": "USDT", "name": "Tether USD", "network": "TRON · TRC-20", "color": "#26a17b"},
    {"code": "USDT_BEP20", "ticker": "USDT", "name": "Tether USD", "network": "BNB · BEP-20", "color": "#26a17b"},
    {"code": "USDT_POL", "ticker": "USDT", "name": "Tether USD", "network": "Polygon", "color": "#26a17b"},
    {"code": "USDT_SOL", "ticker": "USDT", "name": "Tether USD", "network": "Solana", "color": "#26a17b"},
    {"code": "USDT_TON", "ticker": "USDT", "name": "Tether USD", "network": "TON", "color": "#26a17b"},
    {"code": "USDC_ERC20", "ticker": "USDC", "name": "USD Coin", "network": "Ethereum · ERC-20", "color": "#2775ca"},
    {"code": "USDC_TRC20", "ticker": "USDC", "name": "USD Coin", "network": "TRON · TRC-20", "color": "#2775ca"},
    {"code": "USDC_BEP20", "ticker": "USDC", "name": "USD Coin", "network": "BNB · BEP-20", "color": "#2775ca"},
    {"code": "USDC_POL", "ticker": "USDC", "name": "USD Coin", "network": "Polygon", "color": "#2775ca"},
    {"code": "USDC_SOL", "ticker": "USDC", "name": "USD Coin", "network": "Solana", "color": "#2775ca"},
]

VALID_COIN_CODES = {c["code"] for c in ORBCHAIN_COINS}
