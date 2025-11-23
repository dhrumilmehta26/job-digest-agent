# main.py
import os
import smtplib
import yaml
import datetime
from email.message import EmailMessage
from serpapi import GoogleSearch
from pathlib import Path

# Load config
CONFIG_PATH = Path(__file__).parent / "sources.yaml"
config = yaml.safe_load(open(CONFIG_PATH))

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
GMAIL_USER = os.environ.get("GMAIL_USER")  # e.g. your.email@gmail.com
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # app password

# helper: build query list
def build_queries(keywords, locations):
    queries = []
    for kw in keywords:
        for loc in locations:
            queries.append(f"{kw} jobs {loc}")
    return queries

def fetch_jobs_from_serpapi(query, serp_api_key):
    params = {
        "engine": "google_jobs",
        "q": query,
        "api_key": serp_api_key,
        "hl": "en"
    }
    search = GoogleSearch(params)
    result = search.get_dict()
    # serpapi returns 'jobs_results' sometimes
    jobs = result.get("jobs_results") or []
    out = []
    for j in jobs:
        out.append({
            "title": j.get("title"),
            "company": j.get("company_name"),
            "location": j.get("location"),
            "link": j.get("apply_link") or j.get("detected_extensions", {}).get("link") or j.get("link"),
            "posted": j.get("posted_at") or j.get("date") or ""
        })
    return out

def filter_and_dedupe(jobs, keywords, locations, max_age_hours):
    # simple filter by location and dedupe by (title+company+location)
    seen = set()
    filtered = []
    now = datetime.datetime.utcnow()
    for j in jobs:
        key = (j.get("title") or "") + (j.get("company") or "") + (j.get("location") or "")
        if key in seen:
            continue
        seen.add(key)
        # basic location match
        if not any(loc.lower() in (j.get("location") or "").lower() for loc in locations):
            continue
        filtered.append(j)
    return filtered

def build_html_email(jobs, subject_date):
    if not jobs:
        html = f"<p>No new roles in the last 24 hours. Try expanding keywords or locations.</p>"
    else:
        rows = ""
        for j in jobs:
            title = j.get("title") or "No title"
            company = j.get("company") or "Unknown"
            loc = j.get("location") or ""
            link = j.get("link") or "#"
            rows += f"<li><a href='{link}' target='_blank'>{title}</a> — {company} <em>({loc})</em></li>"
        html = f"<p>Found {len(jobs)} roles in the last 24 hours:</p><ul>{rows}</ul>"
    return f"""
    <html>
      <body>
        <h2>{os.getenv('EMAIL_SUBJECT', 'CRM/Retention Jobs')} — {subject_date}</h2>
        {html}
        <hr/>
        <p style='font-size:smaller;color:gray'>Powered by job-digest-agent</p>
      </body>
    </html>
    """

def send_email_html(to_email, subject, html_content):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg.set_content("Open HTML capable email client to view the job digest.")
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)

def main():
    queries = build_queries(config['keywords'], config['locations'])
    all_jobs = []
    for q in queries:
        try:
            jobs = fetch_jobs_from_serpapi(q, SERPAPI_KEY)
            all_jobs.extend(jobs)
        except Exception as e:
            print("Error fetching", q, e)

    jobs_filtered = filter_and_dedupe(all_jobs, config['keywords'], config['locations'], config.get('max_age_hours', 24))
    subject_date = datetime.datetime.now().strftime("%a, %b %d")
    subject = f"{config.get('email_subject_prefix', 'Jobs') } {subject_date}"
    html = build_html_email(jobs_filtered, subject_date)
    recipient = os.environ.get("RECIPIENT_EMAIL") or GMAIL_USER
    send_email_html(recipient, subject, html)
    print("Email sent to", recipient)

if __name__ == "__main__":
    main()
