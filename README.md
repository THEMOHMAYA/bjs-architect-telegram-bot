# 🤖 Bots.Business (BJS) Architect Telegram Bot

An AI-Powered Telegram Bot that designs and generates production-ready **Bots.Business (BJS - JavaScript)** Telegram bots from user prompts.

## ✨ Features
- **100% Pure Bots.Business BJS Format:** Command names, Wait for Answer (need_reply: ON/OFF) explanations, default Answer texts, Keyboards, and complete BJS JavaScript code.
- **English Explanations:** Clean, structured developer explanations.
- **Interactive Upgrades:** Automatically suggests 3-5 upgrades per bot and applies modifications conversationally.
- **Forced Channel Membership:** Requires users to be active members of `@frozentools` (with continuous real-time membership verification).
- **Free vs Premium Daily Quotas:**
  - Free users: **3 generations per day**.
  - Premium users: **15 generations per day**.
  - Premium validity: **7 days for ₹29**.
  - Automated 2-day pre-expiry warning notifications.
- **Admin Management:**
  - `/addpremium <user_id> [days]`
  - `/removepremium <user_id>`
  - `/stats`
- **Developer Credit:** `@moh_maya_official`

## 🚀 Setup & Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/alonepro098/bjs-architect-telegram-bot.git
   cd bjs-architect-telegram-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create a `.env` file based on `.env.example`:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   AI_PROVIDER=gemini
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## 👨‍💻 Developer
Developed by **[@moh_maya_official](https://t.me/moh_maya_official)**
Official Channel: **[@frozentools](https://t.me/frozentools)**
