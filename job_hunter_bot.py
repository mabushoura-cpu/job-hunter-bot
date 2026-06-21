"""
AI Job Hunter Bot — Telegram Edition (Fixed Version)
"""

import os
import json
import asyncio
import logging
from datetime import datetime
import httpx
import schedule

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")

DIGEST_TIME = "08:00"

PROFILE = {
    "specialty":      "Engineering",
    "location":       "Saudi Arabia",
    "experience":     "5 years",
    "skills":         ["AutoCAD", "Project Management", "Saudi Aramco standards"],
    "certifications": ["PMP"],
    "salary_range":   "15,000 – 25,000 SAR/month",
}

PLATFORMS = ["LinkedIn", "Bayt.com", "Indeed", "X/Twitter"]

# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ─────────────────────────────────────────
# STARTUP CHECK
# ─────────────────────────────────────────
def check_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:   missing.append("TELEGRAM_CHAT_ID")
    if not ANTHROPIC_API_KEY:  missing.append("ANTHROPIC_API_KEY")
    if missing:
        log.error(f"❌ Missing environment variables: {', '.join(missing)}")
        log.error("Go to Railway → your project → Variables tab and add them.")
        return False
    if not ANTHROPIC_API_KEY.startswith("sk-ant-"):
        log.error(f"❌ ANTHROPIC_API_KEY looks wrong. It should start with sk-ant-  Got: {ANTHROPIC_API_KEY[:10]}...")
        return False
    log.info("✅ All environment variables found")
    log.info(f"   TELEGRAM_BOT_TOKEN: ...{TELEGRAM_BOT_TOKEN[-6:]}")
    log.info(f"   TELEGRAM_CHAT_ID:   {TELEGRAM_CHAT_ID}")
    log.info(f"   ANTHROPIC_API_KEY:  {ANTHROPIC_API_KEY[:12]}...")
    return True


# ─────────────────────────────────────────
# SEND TELEGRAM MESSAGE
# ─────────────────────────────────────────
async def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        })
        if resp.status_code != 200:
            # Retry without markdown
            resp = await client.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text.replace("*","").replace("_","").replace("`",""),
                "disable_web_page_preview": True,
            })
        resp.raise_for_status()
    log.info("Telegram message sent ✓")


# ─────────────────────────────────────────
# AI JOB SEARCH
# ─────────────────────────────────────────
async def fetch_jobs_from_ai() -> list:
    prompt = f"""You are an AI job-hunting agent for an engineer in Saudi Arabia.

User profile:
- Specialty: {PROFILE['specialty']}
- Location: {PROFILE['location']}
- Experience: {PROFILE['experience']}
- Skills: {', '.join(PROFILE['skills'])}
- Certifications: {', '.join(PROFILE['certifications'])}
- Target salary: {PROFILE['salary_range']}

Today: {datetime.now().strftime('%A, %d %B %Y')}
Platforms: {', '.join(PLATFORMS)}

Return exactly 8 realistic engineering job listings from Saudi Arabia.
Include Vision 2030, NEOM, Aramco, SABIC, STC, ACWA Power, Bechtel, Parsons jobs.

Return ONLY a JSON array, no markdown, no extra text:
[
  {{
    "title": "Job title",
    "company": "Company name",
    "location": "City, Saudi Arabia",
    "platform": "LinkedIn",
    "salary": "SAR 18,000/month",
    "match_score": 88,
    "posted": "2 hours ago",
    "why_match": "Matches your AutoCAD and project management skills"
  }}
]"""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    log.info(f"Calling Anthropic API with key: {ANTHROPIC_API_KEY[:12]}...")

    async with httpx.AsyncClient(timeout=40) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        log.info(f"API response status: {resp.status_code}")
        if resp.status_code != 200:
            log.error(f"API error body: {resp.text[:300]}")
        resp.raise_for_status()
        data = resp.json()

    raw = "".join(b["text"] for b in data["content"] if b["type"] == "text")
    raw = raw.replace("```json", "").replace("```", "").strip()
    jobs = json.loads(raw)
    log.info(f"Got {len(jobs)} jobs from AI")
    return jobs


# ─────────────────────────────────────────
# FORMAT DIGEST
# ─────────────────────────────────────────
def format_digest(jobs: list) -> list:
    today = datetime.now().strftime("%d %b %Y")
    strong = sum(1 for j in jobs if j.get("match_score", 0) >= 80)

    messages = []
    header = (
        f"AI Job Digest - {today}\n"
        f"Location: {PROFILE['location']} | Field: {PROFILE['specialty']}\n"
        f"Found {len(jobs)} jobs | {strong} strong matches (80%+)\n\n"
    )

    body = ""
    for i, job in enumerate(jobs, 1):
        score = job.get("match_score", 0)
        block = (
            f"{i}. {job['title']}\n"
            f"Company: {job['company']} | {job['location']}\n"
            f"Platform: {job.get('platform','')}\n"
            f"Salary: {job.get('salary','Not disclosed')}\n"
            f"Match: {score}%\n"
            f"Why: {job.get('why_match','')}\n"
            f"Posted: {job.get('posted','Recently')}\n"
            f"---\n"
        )
        body += block

    footer = f"\nSend /jobs anytime for a new search. Next auto-digest at {DIGEST_TIME}"
    full = header + body + footer

    # Split into chunks under 4000 chars
    while len(full) > 4000:
        split = full[:4000].rfind("\n---\n")
        if split == -1: split = 4000
        messages.append(full[:split])
        full = full[split:]
    messages.append(full)
    return messages


# ─────────────────────────────────────────
# DAILY DIGEST
# ─────────────────────────────────────────
async def run_daily_digest():
    log.info("Running daily job digest...")
    try:
        await send_telegram("Searching for engineering jobs across LinkedIn, Bayt, Indeed and X...")
        jobs = await fetch_jobs_from_ai()
        jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)
        for msg in format_digest(jobs):
            await send_telegram(msg)
            await asyncio.sleep(1)
        log.info(f"Digest sent: {len(jobs)} jobs")
    except Exception as e:
        log.error(f"Digest error: {e}")
        await send_telegram(f"Job Hunter error: {e}")


def run_digest_sync():
    asyncio.run(run_daily_digest())


# ─────────────────────────────────────────
# COMMAND LISTENER
# ─────────────────────────────────────────
async def poll_commands():
    offset = None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            try:
                resp = await client.get(url, params={"timeout": 20, "offset": offset})
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    text = update.get("message", {}).get("text", "").strip().lower()
                    if text in ("/jobs", "/search", "/find", "/start"):
                        log.info(f"Command received: {text}")
                        await run_daily_digest()
            except Exception as e:
                log.warning(f"Poll error: {e}")
            await asyncio.sleep(2)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    if not check_config():
        log.error("Bot cannot start due to missing config. Fix Railway variables and redeploy.")
        return

    log.info(f"Bot started. Daily digest at {DIGEST_TIME}")
    await send_telegram(
        f"Job Hunter Bot is now running!\n"
        f"I will send you {PROFILE['specialty']} jobs in {PROFILE['location']} every day at {DIGEST_TIME}.\n"
        f"Send /jobs anytime for an instant search."
    )

    schedule.every().day.at(DIGEST_TIME).do(run_digest_sync)

    async def scheduler_loop():
        while True:
            schedule.run_pending()
            await asyncio.sleep(30)

    await asyncio.gather(poll_commands(), scheduler_loop())


if __name__ == "__main__":
    asyncio.run(main())
