# AI Job Hunter Bot — Setup Guide
# دليل الإعداد — بوت البحث عن الوظائف

---

## ✅ STEP 1 — Create your Telegram Bot (5 minutes)
## الخطوة 1 — إنشاء بوت تيليجرام

1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. Choose a name, e.g. `My Job Hunter`
4. Choose a username, e.g. `myjobhunter_bot`
5. BotFather will give you a **token** like:
   `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
6. **Copy and save this token** — you'll need it below.

Then get your Chat ID:
1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. It shows your **Chat ID** (a number like `123456789`)

---

## ✅ STEP 2 — Get your Anthropic API Key
## الخطوة 2 — مفتاح Anthropic API

1. Go to: https://console.anthropic.com
2. Sign up / log in
3. Click **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)

---

## ✅ STEP 3 — Deploy for FREE on Railway
## الخطوة 3 — نشر البوت مجاناً

Railway runs your bot 24/7 in the cloud for free.

1. Go to https://railway.app and sign up with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Upload these 3 files to a GitHub repo:
   - `job_hunter_bot.py`
   - `requirements.txt`
   - `Procfile` (content: `worker: python job_hunter_bot.py`)
4. In Railway, go to **Variables** and add:

   | Variable             | Value                        |
   |----------------------|------------------------------|
   | TELEGRAM_BOT_TOKEN   | (your token from Step 1)     |
   | TELEGRAM_CHAT_ID     | (your chat ID from Step 1)   |
   | ANTHROPIC_API_KEY    | (your key from Step 2)       |

5. Click **Deploy** — done! ✅

---

## ✅ STEP 4 — Test it
## الخطوة 4 — اختبار البوت

Open your Telegram bot and send:
```
/jobs
```

The bot will immediately search and send you today's engineering jobs!

---

## 🔧 CUSTOMIZING YOUR PROFILE
## تخصيص ملفك الشخصي

In `job_hunter_bot.py`, edit the `PROFILE` section:

```python
PROFILE = {
    "specialty":    "Civil Engineering",       # ← your specialty
    "location":     "Riyadh",                  # ← your city
    "experience":   "8 years",                 # ← your experience
    "skills":       ["AutoCAD", "Revit", ...], # ← your skills
    "certifications": ["PMP", "PE"],           # ← your certs
    "salary_range": "20,000 – 30,000 SAR/month",
}

DIGEST_TIME = "08:00"  # ← time to receive daily digest
```

---

## 💡 TIPS
- Send `/jobs` anytime for an on-demand search
- The bot runs every day at your chosen time automatically
- Railway free tier = 500 hours/month (enough for 24/7)
- All job data is AI-generated based on Saudi Arabia's real market

---

## 📞 SUPPORT
If you have any issues, ask Claude for help!
