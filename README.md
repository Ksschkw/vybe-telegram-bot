# 🚀 Vybe Analytics Telegram Bot

Vybe Analytics Telegram Bot is a powerful Telegram bot that provides real-time, on-chain insights using Vybe Network APIs. From tracking wallet balances to showing the top token holders and whale alerts, this bot delivers instant analytics to any Telegram user.  
🤖 **Try The Bot**: [VybeVigil](https://t.me/VybeVigil_bot)

## 📝 Project Summary

For the VybeVigil project, I set out to build a cutting-edge Telegram bot that revolutionizes how crypto enthusiasts monitor on-chain analytics. I named the bot VybeVigil to capture its core mission—to be a vigilant guardian of crypto data, constantly alerting users to critical market movements. I engineered the solution using asynchronous programming with `python-telegram-bot` and `aiohttp`, ensuring smooth, real-time interactions with Vybe Network APIs. This design choice made the bot highly responsive, capable of handling dynamic commands with robust error management.

Every reply from VybeVigil is designed not only to provide immediate insights—from wallet balances and token prices to whale alerts and NFT analytics—but also to seamlessly direct users to Alphavybe for deeper, commercial-grade analytics. I implemented a smart command correction system that enhances user experience by suggesting the right commands when typos occur, along with a fully interactive button-driven tutorial that guides users through the bot’s comprehensive functionality.

Although unit tests aren’t part of the current release, my roadmap includes them to further reinforce code reliability and scalability. VybeVigil embodies innovation and technical excellence, poised to make a significant impact in the crypto analytics space.

---

## 🔌 Vybe API Integration

| Command           | Vybe API Endpoint                                                  | Description                               |
|-------------------|--------------------------------------------------------------------|-------------------------------------------|
| `/balance`        | `/account/token-balance/{address}`                                 | Wallet balances and SOL staking data      |
| `/chart`          | `/price/{mint}/token-ohlcv`                                        | OHLCV data for price charts               |
| `/whalealert`     | `/token/transfers`                                                 | Whale transfers filtered by USD threshold |
| `/prices`         | `/tokens`                                                          | Retrieves a list of tracked tokens        |
| `/tokendetails`   | `/token/{mintAddress}`                                             | Retrieves details of the specified token  |
| `/topholders`     | `/token/{mintAddress}/top-holders`                                 | Retrieves the top token holders           |
| `/nft_analysis`   | `/nft/collection-owners/{address}`                                 | Wallets owning NFTs in the collection     |

---

## 📌 Features

- 💼 **Wallet Balance**: Check the balance of any Solana wallet.  
- 📊 **Chart**: Displays the price chart of a specified token over selectable timeframes.  
- 💰 **Token Prices**: Get real-time token price and USD value.  
- 🐳 **Whale Alerts**: View the latest large token transfers with customizable thresholds.  
- 🔍 **Token Details**: Retrieve full details about any token by its mint address.  
- 👑 **Top Token Holders**: View the richest wallets holding a particular token.  
- 🖼 **NFT Analytics**: Analyze NFT collection ownership distributions.  
- 🎮 **Interactive Tutorial**: Step through a guided, button-driven tutorial on all core commands.  

### 🤖 Smart Command Correction

We all make typos! The bot automatically suggests corrections for common mistakes:

- `price` → `/prices`  
- `bal` → `/balance`  
- `walealert` → `/whalealert`  
- `nft` → `/nft_analysis`  
- And many more built-in variants.

**Example Interaction:**  
```
User:  pric solana  
Bot:   ❓ Did you mean /prices?  
       Try: `/prices <token_mint> [count]`  

User:  whal  
Bot:   ❓ Did you mean /whalealert?  
       Try: `/whalealert [threshold] [limit]`
```

---

## 🤖 Interactive Command Flows

For users who prefer buttons and guided prompts, VybeVigil supports fully interactive menus. Simply tap `/start`, then choose from:

| Menu Button       | Description                                                  |
|-------------------|--------------------------------------------------------------|
| **Accounts**      | 💼 View known accounts, check balances, or see balance history. |
| **Prices**        | 📊 Fetch top tokens or lookup a specific mint interactively. |
| **Chart**         | 📈 Select timeframe (7 d or 30 d) then input mint for price charts. |
| **Holders**       | 👑 Tap to request top holders; then send `<mint> <count>`.    |
| **NFT Analytics** | 🖼 Choose “Analyze” and enter a collection address for owner stats. |
| **Pyth OHLC**     | ⚙️ Pick 1 h/4 h/1 d, then supply a mint to get recent OHLC data. |
| **Tutorial**      | 🔰 Step through a multi-page guide on all core commands.      |

---

## 🛠️ Installation

1. **Clone** this repo:
   ```bash
   git clone https://github.com/Ksschkw/vybe-telegram-bot.git
   cd vybe-telegram-bot
   ```

2. **Install** dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure** credentials:
   - Get a **Vybe API Key** from your Vybe contest organizer.  
   - Get a **Telegram Bot Token** from [@BotFather](https://t.me/BotFather).  
   - Create a `.env` file:
     ```
     VYBE_API_KEY=your_api_key
     TELEGRAM_BOT_TOKEN=your_bot_token
     ```

4. **Run** the bot locally:
   ```bash
   python bot.py
   ```

5. **(Optional) Docker**:
   ```bash
   docker build -t vybe-bot .
   docker run --env-file .env vybe-bot
   ```

---

## 🤖 Bot Commands

| Command               | Parameters                       | Description                                               | Example                                                               |
|-----------------------|----------------------------------|-----------------------------------------------------------|-----------------------------------------------------------------------|
| `/start`              | None                             | Show introductory message and interactive menu           | `/start`                                                             |
| `/balance`            | `<wallet_address>`               | Get SOL balance and token holdings                       | `/balance 4DDUJ1rA3Vk...`                                            |
| `/prices`             | `[token_mint] [count]`           | Get token prices (specific or top list)                  | `/prices` <br> `/prices EPj... 15`                                   |
| `/whalealert`         | `[threshold] [limit]`            | Show large transfers (default ≥ $1000, max 7)             | `/whalealert` <br> `/whalealert 500 3`                               |
| `/tokendetails`       | `<mint_address>`                 | Get metadata and stats for a token                       | `/tokendetails EPj...`                                               |
| `/topholders`         | `<mint_address> [count]`         | Show top holders of a token (default top 10)             | `/topholders EPj... 5`                                               |
| `/chart`              | `<mint_address>`                 | Display price chart for a token (last 30 days)           | `/chart EPj...`                                                      |
| `/nft_analysis`       | `<collection_address>`           | Analyze NFT collection ownership distribution             | `/nft_analysis 7VQo9H...`                                            |
| `/tutorial`           | None                             | Shows a guided tutorial on how to use the bot            | `/tutorial`                                                         |

---

## 📷 Screenshots

| START MENU                          | Whale Alerts      | Top Holders      |
|-------------------------------------|-------------------|------------------|
| ![Start](imagesforreadme/start.png) | ![Whale](imagesforreadme/whale.png) | ![TopHolders](imagesforreadme/topholders.png) |

| Chart                                | Token Details     | Tutorial Pages   |
|--------------------------------------|-------------------|------------------|
| ![Chart](imagesforreadme/chart.png)  | ![Token](imagesforreadme/tokdeets.png) | ![Tut1](imagesforreadme/tutorial1.png)<br>![Tut2](imagesforreadme/tutorial2.png) |

---

## 💡 Innovation Highlights

- Combines multiple Vybe API endpoints into a compact, user-friendly UX.  
- Displays both raw data and formatted insights with Markdown and charts.  
- Smart typo correction prevents silent failures and guides users.  
- Fully interactive, button-driven menus for a modern chat experience.  
- Modular design allows easy addition of new Vybe API features.

---

## 🏁 Getting Your Vybe API Key

Visit [Vybe Network Docs](https://docs.vybenetwork.com/docs/getting-started) for instructions on obtaining an API key.

---

## 📜 License

MIT License — free to use and modify. See the [LICENSE](LICENSE) file for details.

---

Made with 💙 by [Kosisochukwu](https://kosisochukwu.onrender.com) using [Vybe Network](https://vybenetwork.xyz).  