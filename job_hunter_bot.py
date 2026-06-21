"""
AI Job Hunter Bot — Telegram Edition (v3 Fixed)
"""

import os
import json
import asyncio
import logging
from datetime import datetime
import httpx
import schedule

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
DIGEST_TIME        = "08:00"

PROFILE = {
    "specialty":      "Engineering",
    "location":       "Saudi Arabia",
    "experience":     "5 years",
    "skills":         ["AutoCAD", "Project Management", "Saudi Aramco standards"],
    "certifications": ["PMP"],
    "salary_range":   "15,000 - 25,000 SAR/month",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


async def send_telegram(text: str):
    """Send a plain text message to Telegram (no markdown to avoid errors)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            log.error(f"Telegram error: {resp.text}")
        resp.raise_for_status()


async def test_api():
    """Send a minimal test call and return the full error if it fails."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 20,
                "messages": [{"role": "user", "content": "Say hi"}],
            },
        )
        log.info(f"Test API status: {resp.status_code}")
        log.info(f"Test API body: {resp.text[:300]}")
        return resp.status_code, resp.text


async def fetch_jobs_from_ai() -> list:
    prompt = f"""You are a job search assistant for an engineer in Saudi Arabia.

Profile:
- Specialty: {PROFILE['specialty']}
- Location: {PROFILE['location']}
- Experience: {PROFILE['experience']}
- Skills: {', '.join(PROFILE['skills'])}

Find 8 realistic engineering jobs in Saudi Arabia today ({datetime.now().strftime('%d %b %Y')}).
Companies like NEOM, Aramco, SABIC, ACWA Power, Bechtel, Parsons, STC.

Return ONLY a JSON array, nothing else, no markdown fences:
[{{"title":"","company":"","location":"","platform":"LinkedIn","salary":"","match_score":85,"posted":"","why_match":""}}]"""

    async with httpx.AsyncClient(timeout=40) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if resp.status_code != 200:
            raise Exception(f"API {resp.status_code}: {resp.text[:200]}")
        data = resp.json()

    raw = "".join(b["text"] for b in data["content"] if b["type"] == "text")
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)


def format_digest(jobs: list) -> str:
    today = datetime.now().strftime("%d %b %Y")
    strong = sum(1 for j in jobs if j.get("match_score", 0) >= 80)
    lines = [
        f"AI Job Digest - {today}",
        f"Field: {PROFILE['specialty']} | Location: {PROFILE['location']}",
        f"Found {len(jobs)} jobs | {strong} strong matches",
        "",
    ]
    for i, job in enumerate(jobs, 1):
        lines += [
            f"{i}. {job.get('title','')}",
            f"   Company : {job.get('company','')}",
            f"   Location: {job.get('location','')}",
            f"   Platform: {job.get('platform','')}",
            f"   Salary  : {job.get('salary','Not disclosed')}",
            f"   Match   : {job.get('match_score',0)}%",
            f"   Why     : {job.get('why_match','')}",
            f"   Posted  : {job.get('posted','Recently')}",
            "",
        ]
    lines.append(f"Send /jobs anytime. Next digest at {DIGEST_TIME}.")
    return "\n".join(lines)


async def run_daily_digest():
    log.info("Running daily digest...")
    try:
        await send_telegram("Searching for engineering jobs... please wait.")
        jobs = await fetch_jobs_from_ai()
        jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)
        digest = format_digest(jobs)
        # Split if too long
        while digest:
            await send_telegram(digest[:3900])
            digest = digest[3900:]
            if digest:
                await asyncio.sleep(1)
        log.info(f"Digest sent: {len(jobs)} jobs")
    except Exception as e:
        log.error(f"Digest error: {e}")
        await send_telegram(f"Job Hunter error: {e}")


def run_digest_sync():
    asyncio.run(run_daily_digest())


async def poll_commands():
    offset = None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            try:
                resp = await client.get(url, params={"timeout": 20, "offset": offset})
                for update in resp.json().get("result", []):
                    offset = update["update_id"] + 1
                    text = update.get("message", {}).get("text", "").strip().lower()
                    if text in ("/jobs", "/search", "/find", "/start"):
                        await run_daily_digest()
                    elif text == "/test":
                        status, body = await test_api()
                        await send_telegram(f"API Test Result:\nStatus: {status}\nBody: {body[:300]}")
            except Exception as e:
                log.warning(f"Poll error: {e}")
            await asyncio.sleep(2)


async def main():
    log.info("Bot starting...")
    log.info(f"ANTHROPIC_API_KEY present: {bool(ANTHROPIC_API_KEY)} | starts with sk-ant-: {ANTHROPIC_API_KEY.startswith('sk-ant-')}")
    log.info(f"TELEGRAM_BOT_TOKEN present: {bool(TELEGRAM_BOT_TOKEN)}")
    log.info(f"TELEGRAM_CHAT_ID present: {bool(TELEGRAM_CHAT_ID)}")

    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ANTHROPIC_API_KEY]):
        log.error("Missing environment variables! Check Railway → Variables.")
        return

    await send_telegram(
        "Job Hunter Bot started!\n"
        "Commands:\n"
        "/jobs - search for engineering jobs now\n"
        "/test - test API connection\n\n"
        f"Auto digest daily at {DIGEST_TIME}"
    )

    schedule.every().day.at(DIGEST_TIME).do(run_digest_sync)

    async def scheduler_loop():
        while True:
            schedule.run_pending()
            await asyncio.sleep(30)

    await asyncio.gather(poll_commands(), scheduler_loop())


if __name__ == "__main__":
    asyncio.run(main())
