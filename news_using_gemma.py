import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import feedparser
import ollama
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Fetch credentials securely from environment variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

OLLAMA_MODEL = "gemma2"


def fetch_raw_news() -> list:
  """Step 1: Fetch raw entries from multiple reliable RSS feeds"""
  rss_urls = [
      "https://thehackernews.com/rss.xml",
      "https://www.bleepingcomputer.com/feed/",
      "https://www.darkreading.com/rss.xml",
      "https://krebsonsecurity.com/feed/",
      "https://www.schneier.com/blog/atom.xml",
  ]

  raw_entries = []
  pre_filter_keywords = [
      "ai",
      "llm",
      "gpt",
      "model",
      "agent",
      "autonomous",
      "threat actor",
      "malware",
      "vulnerability",
      "exploit",
  ]

  for url in rss_urls:
    feed = feedparser.parse(url)
    for entry in feed.entries:
      title = entry.title
      summary = entry.summary if "summary" in entry else ""

      combined_text = (title + " " + summary).lower()
      if any(kw in combined_text for kw in pre_filter_keywords):
        raw_entries.append(
            {"title": title, "link": entry.link, "summary": summary[:300]}
        )

  return raw_entries


def evaluate_with_ollama(article: dict) -> dict:
  """Step 2: Use Ollama as a security analyst brain to filter true AI-cyberattacks"""
  prompt = f"""
    You are an expert AI Security Analyst and Red Teamer. 
    Analyze the following article and determine if it is STRICTLY relevant to:
    1. Threat actors or hackers using Artificial Intelligence / LLMs to launch cyberattacks, social engineering, or automated exploits.
    2. AI-specific vulnerabilities (like prompt injection, model poisoning, data exfiltration via APIs).
    
    Article Title: {article['title']}
    Article Summary: {article['summary']}

    Answer strictly in this format:
    RELEVANT: YES or NO
    REASON: One short sentence explaining how it fits the criteria (or why it doesn't).
    """

  try:
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    reply = response["message"]["content"].strip()

    is_relevant = "RELEVANT: YES" in reply.upper()
    reason = ""
    for line in reply.split("\n"):
      if "REASON:" in line.upper():
        reason = line.replace("REASON:", "").strip()

    return {
        "is_relevant": is_relevant,
        "reason": reason or "No specific reason provided.",
    }
  except Exception as e:
    print(f"Ollama evaluation error: {e}")
    return {"is_relevant": False, "reason": "Error connecting to local LLM."}


def curate_intelligence() -> list:
  """Step 3: Combine fetching and local AI filtering"""
  print("🔄 Fetching feeds and pre-filtering candidates...")
  candidates = fetch_raw_news()
  print(
      f"🔍 Found {len(candidates)} potential candidates. Running local AI"
      f" evaluation via Ollama ({OLLAMA_MODEL})..."
  )

  curated_news = []
  for item in candidates:
    evaluation = evaluate_with_ollama(item)
    if evaluation["is_relevant"]:
      print(f"✅ Approved: {item['title']}")
      curated_news.append({
          "title": item["title"],
          "link": item["link"],
          "reason": evaluation["reason"],
      })
    else:
      print(f"❌ Skipped: {item['title']}")

  return curated_news


def create_email_body(news_list: list) -> str:
  """Step 4: Format the curated intel into a clean email report"""
  if not news_list:
    return (
        "No high-priority AI & Cyberattack threat intel matched your criteria"
        " today."
    )

  body = "🛡️ DAILY AI THREAT INTELLIGENCE DIGEST (Filtered by Local Ollama Brain)\n"
  body += "=" * 70 + "\n\n"

  for idx, item in enumerate(news_list, 1):
    body += f"{idx}. {item['title']}\n"
    body += f"   🔗 Link: {item['link']}\n"
    body += f"   💡 AI Analysis: {item['reason']}\n\n"

  return body


def send_gmail_notification(email_body: str):
  """Step 5: Dispatch to Gmail using secure env variables"""
  if not SENDER_EMAIL or not APP_PASSWORD:
    print(
        "❌ Error: SENDER_EMAIL or APP_PASSWORD not found in environment"
        " variables or .env file."
    )
    return

  message = MIMEMultipart()
  message["From"] = SENDER_EMAIL
  message["To"] = RECEIVER_EMAIL
  message["Subject"] = "🚨 AI Cyberattack & Threat Intel Digest"

  message.attach(MIMEText(email_body, "plain"))

  try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
    server.quit()
    print("🚀 Smart intel digest successfully sent to your Gmail!")
  except Exception as e:
    print(f"❌ Failed to send email: {e}")


if __name__ == "__main__":
  curated_digest = curate_intelligence()
  final_body = create_email_body(curated_digest)
  send_gmail_notification(final_body)