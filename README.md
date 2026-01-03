# 🎯 Job Aggregator

A Python-based job aggregation system that automatically fetches jobs from multiple sources, filters them based on your criteria, stores them in MongoDB, and sends daily email notifications via Gmail SMTP (or any SMTP server).

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)
![SMTP](https://img.shields.io/badge/Email-Gmail%20SMTP-red.svg)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-black.svg)

## ✨ Features

- **Multi-Source Job Fetching**: Aggregates jobs from Remotive, RemoteOK, Arbeitnow, and Google Jobs
- **Smart Filtering**: Filter by keywords, designation, field, location, and posting date
- **Deduplication**: Automatically removes duplicate jobs across sources
- **MongoDB Storage**: Stores jobs with automatic cleanup (keeps last 2 days only)
- **Email Notifications**: Beautiful HTML email digests via Gmail SMTP (or any SMTP server)
- **Scheduled Runs**: GitHub Actions cron job runs daily at 7:30 AM (your timezone)
- **Local UI Dashboard**: Static HTML dashboard to view fetched jobs
- **Manual Triggers**: Run on-demand via GitHub Actions or command line

## 📧 Email Preview

Each morning, you receive an email like:

**Subject**: `🎯 CRM/Martech Jobs - Last 24h - Tue, Nov 04`

The email contains:
- Clickable job titles
- Company names and locations
- Matched keywords badges
- Direct "Apply" links

If no new jobs are found, you get a friendly notification instead.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier works)
- Gmail account with App Password enabled (for SMTP)
- GitHub account (for automated runs)

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/yourusername/job-aggregator.git
cd job-aggregator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your values:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# MongoDB (see setup instructions below)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/job_aggregator

# SMTP (Gmail recommended - use an App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true

# Email addresses
FROM_EMAIL=your_gmail@gmail.com
TO_EMAILS=your_email@gmail.com

# Search Configuration
SEARCH_KEYWORDS=CRM,Retention,Martech,Customer Success
PREFERRED_LOCATIONS=Remote,USA
USER_TIMEZONE=America/New_York
```

### 3. Run Locally

```bash
# Run full pipeline (fetch, store, email)
python run.py

# Run in test mode (no email)
python run.py --test

# View statistics
python run.py --stats

# Start local UI server
python run.py --ui
```

### 4. Set Up GitHub Actions

For automated daily runs, add secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:

| Secret | Description | Example |
|--------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username (Gmail address) | `your@gmail.com` |
| `SMTP_PASSWORD` | SMTP password (Gmail App Password) | `xxxx xxxx xxxx xxxx` |
| `FROM_EMAIL` | Sender email (often same as SMTP_USER) | `jobs@domain.com` |
| `TO_EMAILS` | Recipient emails (comma-separated) | `email1@gmail.com,email2@gmail.com` |
| `SEARCH_KEYWORDS` | Keywords to search | `CRM,Retention,Martech` |
| `USER_TIMEZONE` | Your timezone | `America/New_York` |
| `PREFERRED_LOCATIONS` | Locations to search | `Remote,USA,India` |

Optional secrets:
- `FROM_NAME`: Sender name (default: "Job Aggregator")
- `FILTER_DESIGNATIONS`: Job titles to filter (e.g., "Manager,Director,Lead")
- `FILTER_FIELDS`: Job categories (e.g., "Marketing,Sales")
- `MONGODB_DATABASE`: Database name (default: "job_aggregator")

---

## 🗄️ MongoDB Atlas Setup

### Step 1: Create Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Click **"Try Free"** and sign up
3. Choose the **FREE** tier (M0 Sandbox)

### Step 2: Create Cluster

1. Select cloud provider (any works, AWS recommended)
2. Choose region closest to you
3. Keep cluster name as `Cluster0` or customize
4. Click **"Create Cluster"** (takes 1-3 minutes)

### Step 3: Configure Access

**Database User:**
1. Go to **Database Access** (left sidebar)
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Enter username and password (save these!)
5. Set privileges to **"Read and write to any database"**
6. Click **"Add User"**

**Network Access:**
1. Go to **Network Access** (left sidebar)
2. Click **"Add IP Address"**
3. For GitHub Actions, click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ For production, consider using a static IP service
4. Click **"Confirm"**

### Step 4: Get Connection String

1. Go to **Database** (left sidebar)
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Select **Python** and version **3.11 or later**
5. Copy the connection string
6. Replace `<password>` with your database user password
7. Add database name before `?`: `.../job_aggregator?retryWrites=...`

Example connection string:
```
mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/job_aggregator?retryWrites=true&w=majority
```

---

## 📧 Gmail SMTP Setup

1. Ensure **2-Step Verification** is enabled on your Google account.
2. Open [App Passwords](https://myaccount.google.com/apppasswords).
3. Choose **Mail** as the app and **Other** for device (e.g., "Job Aggregator"), then click **Create**.
4. Copy the 16-character App Password (no spaces) and set it as `SMTP_PASSWORD` in `.env`.
5. Use your Gmail address for `SMTP_USER` (and typically `FROM_EMAIL`).
6. Keep `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, and `SMTP_USE_TLS=true`.

For other SMTP providers, update the host/port/user/password accordingly.

---

## 📁 Project Structure

```
job-aggregator/
├── .github/workflows/
│   └── job-fetch.yml        # GitHub Actions cron job
├── src/
│   ├── scrapers/            # Job source scrapers
│   │   ├── base_scraper.py  # Base scraper class
│   │   ├── remotive.py      # Remotive API
│   │   ├── remoteok.py      # RemoteOK API
│   │   ├── arbeitnow.py     # Arbeitnow API
│   │   └── google_jobs.py   # Google Jobs scraper
│   ├── database/            # MongoDB operations
│   │   ├── connection.py    # Database connection
│   │   ├── models.py        # Job schema
│   │   └── operations.py    # CRUD operations
│   ├── notifications/       # Email sending
│   │   └── email_sender.py  # SMTP integration
│   ├── utils/               # Utilities
│   │   ├── config.py        # Configuration loader
│   │   ├── filters.py       # Job filtering
│   │   └── timezone.py      # Timezone handling
│   └── main.py              # Main orchestrator
├── ui/                      # Local dashboard
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── api/
│   └── server.py            # Flask API server
├── run.py                   # Entry point
├── requirements.txt
└── README.md
```

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `MONGODB_URI` | ✅ | MongoDB connection string | - |
| `SMTP_HOST` | ❌ | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | ❌ | SMTP server port | `587` |
| `SMTP_USER` | ✅ | SMTP username (email) | - |
| `SMTP_PASSWORD` | ✅ | SMTP password/App Password | - |
| `SMTP_USE_TLS` | ❌ | Use STARTTLS | `true` |
| `FROM_EMAIL` | ✅ | Sender email address | `SMTP_USER` |
| `TO_EMAILS` | ✅ | Recipient emails (comma-separated) | - |
| `SEARCH_KEYWORDS` | ✅ | Keywords to search (comma-separated) | - |
| `USER_TIMEZONE` | ❌ | Your timezone | `UTC` |
| `PREFERRED_LOCATIONS` | ❌ | Locations to search | `Remote` |
| `FILTER_DESIGNATIONS` | ❌ | Job titles to filter | All |
| `FILTER_FIELDS` | ❌ | Job categories to filter | All |
| `FROM_NAME` | ❌ | Sender name | `Job Aggregator` |
| `MONGODB_DATABASE` | ❌ | Database name | `job_aggregator` |

### Timezone Examples

- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Los_Angeles` - Pacific Time
- `Europe/London` - UK Time
- `Asia/Kolkata` - India Time
- `Asia/Tokyo` - Japan Time

[Full list of timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

---

## 🖥️ Local UI Dashboard

Start the local UI server to view fetched jobs:

```bash
python run.py --ui
```

Then open http://localhost:5000 in your browser.

**Features:**
- View all fetched jobs
- Search by title, company, location
- Filter by source, time, new jobs only
- Click to view job details
- Direct apply links

The UI can also work offline by opening `ui/index.html` directly (uses `jobs_data.json`).

---

## 📅 Adjusting Schedule

The default schedule is 7:30 AM EST (12:30 UTC). To change:

1. Edit `.github/workflows/job-fetch.yml`
2. Modify the cron expression:

```yaml
schedule:
  - cron: '30 12 * * *'  # minute hour * * *
```

**Common schedules:**
- `30 12 * * *` = 7:30 AM EST / 6:30 AM CST
- `30 14 * * *` = 7:30 AM PST
- `30 7 * * *` = 7:30 AM UTC
- `0 2 * * *` = 7:30 AM IST (2:00 UTC)

Use [crontab.guru](https://crontab.guru) to calculate your timezone's UTC equivalent.

---

## 🔍 Job Sources

| Source | Type | Jobs | Notes |
|--------|------|------|-------|
| **Remotive** | API | Remote tech jobs | Reliable, good data |
| **RemoteOK** | API | Remote jobs | Large volume |
| **Arbeitnow** | API | Remote & EU jobs | Good for Europe |
| **Google Jobs** | Scraper | Aggregated jobs | May be less reliable |

---

## 🛠️ CLI Commands

```bash
# Full run (fetch, store, email)
python run.py

# Test mode (no email)
python run.py --test

# Start UI server
python run.py --ui

# Export jobs to JSON
python run.py --export

# View database stats
python run.py --stats

# Send test email
python run.py --test-email your@email.com
```

---

## 🐛 Troubleshooting

### "MONGODB_URI is required"
- Make sure `.env` file exists with `MONGODB_URI` set
- Check for typos in the connection string
- Ensure password doesn't contain special characters (or URL-encode them)

### "Connection refused" / Timeout
- Check MongoDB Atlas Network Access settings
- Add `0.0.0.0/0` to allow all IPs (for GitHub Actions)
- Verify cluster is running (not paused)

### "Email not sending"
- Confirm `SMTP_USER`/`SMTP_PASSWORD` are correct (for Gmail, use an App Password)
- Ensure `SMTP_HOST/PORT` are set for your provider (Gmail: smtp.gmail.com:587 with TLS)
- Look for errors in console output

### "No jobs found"
- Try broader keywords
- Check if job sources are accessible
- Some sources may rate-limit requests

### GitHub Actions failing
- Check all required secrets are set
- View workflow logs for specific errors
- Try running manually with test mode first

---

## 📄 License

MIT License - feel free to use and modify as needed.

---

## 🤝 Contributing

Contributions welcome! Please open an issue or PR for any improvements.

---

Built with ❤️ for job seekers everywhere.
