
# 🚀 Vybe Analytics Telegram Bot

Vybe Analytics Telegram Bot is a powerful Telegram bot that provides real-time, on-chain insights using Vybe Network APIs. From tracking wallet balances to showing the top token holders and whale alerts, this bot delivers instant analytics to any Telegram user.

## 📌 Features

- 💼 **Wallet Balance**: Check the balance of any Solana wallet.
- 💰 **Token Prices**: Get real-time token price and USD value.
- 🐳 **Whale Alerts**: View the latest large token transfers.
- 📊 **Token Details**: Retrieve full details about any token by its mint address.
- 👑 **Top Token Holders**: View the richest wallets holding a particular token.
<!-- - 🖼️ Token logos and owner logos included for visual context. -->

## 🛠️ Installation

1. Clone the repo:

```bash
git clone https://github.com/your-username/vybe-telegram-bot.git
cd vybe-telegram-bot
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Add your credentials:
   - Get a **Vybe API key** from [Vbenetwork](https://docs.vybenetwork.com/docs/getting-started).
   - Get a **Telegram Bot Token** from [@BotFather](https://t.me/BotFather).
   - Store these in a `.env` file or your preferred config method.

```
VYBE_API_KEY=your_api_key
TELEGRAM_BOT_TOKEN=your_bot_token
```

4. Run the bot:

```bash
python bot.py
```

## 🤖 Bot Commands

```
/start - Show available commands and intro
/balance <wallet_address> - Get wallet token balances
/prices <token_mint> [amount] - Get token price and USD value
/whalealert [threshold] [limit] - Show recent large transactions
/tokendetails <mint_address> - Get metadata of a token
/toptokenholders <mint_address> - Show top holders of the token
📊 /chart <mint_address> - get the price chart for a specified mint address.
🖼 /nft_analysis <collection_address> - Get NFT collection statistics
```

## 🧠 How It Works

- Uses Vybe API endpoints like `/balance`, `/price`, `/chart`, `/token-details`, `/top-holders`, and `/whale-alert`.
- Formats block time into human-readable format using Python's datetime.
- Uses `python-telegram-bot` for asynchronous, user-friendly bot behavior.
<!-- - Token logos and owner logos are embedded via direct URL (Telegram supports image previews). -->

## 📷 Screenshots

| START |
|----------------------------|
| ![Start](imagesforreadme/start.png) |
| Whale Alerts | Top Holders |
|--------------|-------------|
| ![Whale](imagesforreadme/whale.png) | ![TopHolders](imagesforreadme/topholders.png) |
| chart | Token Details |
| ![Chart](imagesforreadme/chart.png) | ![Token Deets](imagesforreadme/tokdeets.png) |


## 💡 Innovation Highlights

- Combines several endpoints into a compact UX.
- Displays both raw data and formatted insights.
- Designed for real-world, commercial-ready use.

## 🏁 Getting Your Vybe API Key

Visit [Vybenetwork](https://docs.vybenetwork.com/docs/getting-started) read the instructions and get your **API key**.

## 📜 License

MIT License - free to use and modify. See `LICENSE` file for details.

<!-- ## 📬 Submit Your Entry

- Publish your repo with an open-source license
- Include a 200-word project summary in your submission
- Provide the deployed Telegram bot link
- Make sure the README is complete and clear

--- -->

Made with 💙 by [Kosisochukwu](https://kosisochukwu.onrender.com) using [Vybe Network](https://vybenetwork.xyz)
