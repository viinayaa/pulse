import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

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

def send_email(subject, body):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("Email sent.")
    except Exception as e:
        print(f"Email failed ({e})")

def build_summary():
    today = date.today().strftime("%A, %d %B %Y")
    weather = get_weather()
    quote = get_quote()
    temp, description, alert = get_weather_alert()
    summary = f"""
==================================
PULSE - Daily Summary
{today}
==================================

WEATHER
  {weather}

TODAY'S QUOTE
  {quote}

==================================
"""
    if alert:
        summary += f"\n{alert}\n"
    return summary, alert

def run():
    summary, alert = build_summary()
    print(summary)
    with open("daily_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    if alert:
        send_email("Pulse Weather Alert!", alert)
    print("Pulse ran successfully.")

if __name__ == "__main__":
    run()