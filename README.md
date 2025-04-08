🔮 Vybe Analytics Telegram Bot
A feature-rich Telegram bot that delivers real-time, actionable crypto insights using the Vybe API. Built for crypto traders, investors, and community mods looking for on-chain alpha, whale alerts, and wallet tracking—right in their Telegram chats.

🚀 Created for the Vybe Telegram Bot Challenge, this bot empowers communities with plug-and-play crypto analytics, fully open-source and ready to scale.

🧠 Features
✅ Real-time Analytics:
Wallet Overview
/wallet <wallet_address> — Get SOL balance, token count, staked amount, and wallet value.

Whale Alerts
/whales <cap> — Detect large transfers on-chain above a specified USD value.

Token Metrics
/prices <count> — List live token prices, market caps, and supply data.

Token Lookup
/token <mint_address> — Fetch detailed metrics of any token.

Top Token Holders
/holders <mint_address> <count> — List top holders of any token by balance.

🔐 Powered by Vybe APIs
Fast and reliable endpoints with real-time blockchain indexing.

Asynchronous implementation with proper error handling.

🔧 Setup
1. Clone the Repo
bash
Copy
Edit
git clone https://github.com/yourusername/vybe-telegram-bot.git
cd vybe-telegram-bot
2. Install Dependencies
Make sure Python 3.8+ is installed.

bash
Copy
Edit
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the root directory:

env
Copy
Edit
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
VYBE_API_KEY=your_vybe_api_key
🛡️ Get your Vybe API key by messaging @ericvybes on Telegram.

▶️ Run the Bot
bash
Copy
Edit
python bot.py
The bot will start and respond to commands on Telegram.

💬 Commands & Examples
Command	Description	Example
/wallet <address>	Get wallet balance and activity	/wallet FJrH...n4rR
/whales <cap>	Show whale transfers over USD cap	/whales 5000
/prices <count>	Show top token prices	/prices 5
/token <mint_address>	Detailed token info	/token So11111111111111111111111111111111111111112
/holders <mint_address> <count>	Top token holders	/holders So111...1112 10
⚙️ Project Structure
bash
Copy
Edit
.
├── bot.py          # Telegram bot core logic
├── utils.py        # API integrations and formatting
├── .env            # Environment variables (not committed)
├── requirements.txt
└── README.md       # This file!
✨ Innovation Highlights
Uses Vybe’s full suite of APIs to provide token, wallet, and transfer intelligence.

Modular, async architecture built for speed and extensibility.

Focused on community empowerment with actionable Telegram-native insights.

Pluggable design ready for commercial integration or community bot deployments.

🏁 Deployment & Scalability
This bot is fully compatible with cloud deployment options like:

Railway

Render

AWS Lambda

Fly.io

Docker containers

Just plug in your environment variables and deploy.

📜 License
This project is open-source under the MIT License.

👨‍💻 Contributors
You! 🚀

Built for the Vybe Telegram Bot Challenge

🧪 Live Demo
👉 Try the bot on Telegram @VybeVigil_bot
