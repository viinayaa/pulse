import requests
import smtplib
import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from bs4 import BeautifulSoup

def get_weather(city="Thiruvananthapuram"):
    url = f"https://wttr.in/{city}?format=3"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        return f"Weather unavailable ({e})"

def get_weather_alert(city="Thiruvananthapuram"):
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        alert = ""
        if temp > 35:
            alert = f"ALERT: Temperature is {temp}°C - Stay hydrated!"
        if "rain" in description.lower():
            alert += f" ALERT: Rain predicted - {description}"
        return temp, description, alert
    except Exception as e:
        return None, None, f"Weather alert unavailable ({e})"

def get_quote():
    url = "https://zenquotes.io/api/random"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        quote = data[0]["q"]
        author = data[0]["a"]
        return f'"{quote}" - {author}'
    except Exception as e:
        return f"Quote unavailable ({e})"

def scrape_ndtv():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get("https://feeds.feedburner.com/ndtvnews-top-stories", headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.findAll("item")[:3]
        headlines = []
        for item in items:
            headlines.append({
                "title": item.title.text,
                "link": item.link.text,
                "published": item.pubDate.text[:16] if item.pubDate else "N/A",
                "source": "NDTV"
            })
        return headlines
    except Exception as e:
        return []

def scrape_hindu():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get("https://www.thehindu.com/news/national/feeder/default.rss", headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.findAll("item")[:3]
        headlines = []
        for item in items:
            headlines.append({
                "title": item.title.text,
                "link": item.link.text,
                "published": item.pubDate.text[:16] if item.pubDate else "N/A",
                "source": "The Hindu"
            })
        return headlines
    except Exception as e:
        return []

def scrape_toi():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.findAll("item")[:3]
        headlines = []
        for item in items:
            headlines.append({
                "title": item.title.text,
                "link": item.link.text,
                "published": item.pubDate.text[:16] if item.pubDate else "N/A",
                "source": "Times of India"
            })
        return headlines
    except Exception as e:
        return []
def get_news_api_fallback():
    api_key = os.environ.get("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/top-headlines?country=in&pageSize=9&apiKey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        headlines = []
        for article in data["articles"]:
            headlines.append({
                "title": article["title"],
                "link": article["url"],
                "published": article.get("publishedAt", "")[:10],
                "source": article["source"]["name"]
            })
        return headlines
    except Exception as e:
        return []
def build_news_html(all_news):
    rows = ""
    for item in all_news:
        rows += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;">
                <a href="{item['link']}" style="color:#1a0dab;font-weight:bold;text-decoration:none;">{item['title']}</a><br>
                <small style="color:#888;">{item['source']} &nbsp;|&nbsp; {item['published']}</small>
            </td>
        </tr>"""
    return rows

def get_github_repos():
    token = os.environ.get("GH_TOKEN")
    headers = {"Authorization": f"token {token}"}
    url = "https://api.github.com/user/repos?sort=updated&per_page=10"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        repos = response.json()
        projects = []
        for repo in repos:
            projects.append({
                "name": repo["name"],
                "description": repo["description"] or "",
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "updated": repo["updated_at"][:10]
            })
        return projects
    except Exception as e:
        print(f"GitHub repos unavailable ({e})")
        return []

def update_portfolio(projects):
    token = os.environ.get("GH_TOKEN")
    username = "viinayaa"
    repo = "pulse"
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    content = json.dumps(projects, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    get_url = f"https://api.github.com/repos/{username}/{repo}/contents/projects.json"
    get_response = requests.get(get_url, headers=headers)
    payload = {
        "message": "Auto-update projects.json",
        "content": encoded
    }
    if get_response.status_code == 200:
        payload["sha"] = get_response.json()["sha"]
    requests.put(get_url, headers=headers, json=payload)
    print("Portfolio updated.")

def send_email(subject, html_body, plain_body=""):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_body or html_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("Email sent.")
    except Exception as e:
        print(f"Email failed ({e})")

def run():
    today = date.today().strftime("%A, %d %B %Y")
    weather = get_weather()
    quote = get_quote()
    temp, description, alert = get_weather_alert()

    ndtv = scrape_ndtv()
    hindu = scrape_hindu()
    toi = scrape_toi()
    all_news = ndtv + hindu + toi
    if len(all_news) < 3:
        all_news = get_news_api_fallback()

    news_rows = build_news_html(all_news)

    alert_banner = ""
    if alert:
        alert_banner = f'<div style="background:#ff4444;color:white;padding:15px;border-radius:8px;margin-bottom:20px;"><strong>⚠️ {alert}</strong></div>'

    html_body = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px;background:#f9f9f9;">
        <div style="background:#1a1a2e;color:white;padding:25px;border-radius:10px;text-align:center;margin-bottom:20px;">
            <h1 style="margin:0;">⚡ PULSE</h1>
            <p style="margin:5px 0;opacity:0.8;">Daily Summary — {today}</p>
        </div>
        {alert_banner}
        <div style="background:white;padding:20px;border-radius:10px;margin-bottom:20px;">
            <h2 style="color:#1a1a2e;">🌤️ Weather</h2>
            <p style="font-size:18px;">{weather}</p>
        </div>
        <div style="background:white;padding:20px;border-radius:10px;margin-bottom:20px;">
            <h2 style="color:#1a1a2e;">💬 Quote of the Day</h2>
            <p style="font-style:italic;font-size:16px;">{quote}</p>
        </div>
        <div style="background:white;padding:20px;border-radius:10px;">
            <h2 style="color:#1a1a2e;">📰 Top Headlines</h2>
            <table width="100%" cellpadding="0" cellspacing="0">
                {news_rows}
            </table>
        </div>
    </body>
    </html>
    """

    summary_plain = f"PULSE - Daily Summary\n{today}\n\nWEATHER\n{weather}\n\nQUOTE\n{quote}\n\n"
    for item in all_news:
        summary_plain += f"- {item['title']} ({item['source']})\n  {item['link']}\n\n"

    with open("daily_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary_plain)

    send_email(f"⚡ Pulse Daily Summary — {today}", html_body, summary_plain)

    if alert:
        send_email("⚠️ Pulse Weather Alert!", f"<h2>{alert}</h2>", alert)

    projects = get_github_repos()
    if projects:
        update_portfolio(projects)

    print("Pulse ran successfully.")

if __name__ == "__main__":
    run()