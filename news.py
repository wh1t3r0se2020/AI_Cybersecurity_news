import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser

# 1. Function to fetch and parse RSS feeds
def fetch_ai_sec_news() -> list:
    # Reliable RSS feeds for AI and Cybersecurity
    rss_urls = [
        "https://feeds.feedburner.com/DarkReading-Security",
        "https://krebsonsecurity.com/feed/",
        "https://www.bleepingcomputer.com/feed/",
        "https://www.darkreading.com/rss.xml",
        "https://thehackernews.com/rss.xml",
        "https://www.schneier.com/blog/atom.xml"
    ]
    
    keywords = ["ai", "llm", "vulnerability", "breach", "exploit", "agent", "prompt injection", "ransomware", "malware", "zero-day", "cve", "cyberattack"]

    curated_news = []

    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title.lower()
            summary = entry.summary.lower() if 'summary' in entry else ""
            
            # Check if any keyword matches the title or summary
            if any(kw in title or kw in summary for kw in keywords):
                curated_news.append({
                    "title": entry.title,
                    "link": entry.link
                })
                
    # Deduplicate and return top findings
    return curated_news[:10]

# 2. Function to format the email body
def create_email_body(news_list: list) -> str:
    if not news_list:
        return "No major AI & Cybersecurity news found matching keywords today."
    
    body = "Here is your automated daily digest for AI & Cybersecurity:\n\n"
    for idx, item in enumerate(news_list, 1):
        body += f"{idx}. {item['title']}\n   Link: {item['link']}\n\n"
        
    return body

# 3. Function to send Gmail notification
def send_gmail_notification(email_body: str):
    sender_email = "akki18990@gmail.com"
    app_password = "kuag yquv qswo ptrt"  # Use Google App Password, not main password
    receiver_email = "akki18990@gmail.com"
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "🛡️ Daily AI & CyberSec Threat Intel Digest"
    
    message.attach(MIMEText(email_body, "plain"))
    
    try:
        # Connecting to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("✅ Intel digest successfully sent to your Gmail!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# --- Main Execution Flow ---
if __name__ == "__main__":
    print("Fetching intelligence feeds...")
    news = fetch_ai_sec_news()
    
    print(f"Found {len(news)} relevant articles. Composing email...")
    digest = create_email_body(news)
    
    print("Sending email...")
    send_gmail_notification(digest)