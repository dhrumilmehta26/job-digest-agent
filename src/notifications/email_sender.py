"""
SMTP email integration for Job Aggregator.
Sends daily job digest emails to configured recipients using Gmail (or any SMTP server).
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Template


class EmailSender:
    """Send job digest emails via SMTP."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: str = 'Job Aggregator',
        use_tls: bool = True
    ):
        """
        Initialize SMTP email sender.
        
        Args:
            smtp_host: SMTP server host (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (e.g., 587)
            smtp_user: SMTP username (for Gmail, your Gmail address)
            smtp_password: SMTP password or Gmail App Password
            from_email: Sender email address
            from_name: Sender name
            use_tls: Whether to use STARTTLS
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
    
    def send_job_digest(
        self,
        to_emails: List[str],
        jobs: List[Dict[str, Any]],
        keywords: str,
        date_str: str = None
    ) -> bool:
        """
        Send job digest email to recipients.
        
        Args:
            to_emails: List of recipient email addresses
            jobs: List of job dictionaries
            keywords: Keywords string for subject line
            date_str: Date string for subject (defaults to today)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not to_emails:
            print("   ⚠ No recipient emails configured")
            return False
        
        if date_str is None:
            date_str = datetime.now().strftime('%a, %b %d')
        
        # Generate email content
        if jobs:
            subject = f"🎯 {keywords} Jobs - Last 24h - {date_str}"
            html_content = self._generate_jobs_html(jobs, keywords, date_str)
        else:
            subject = f"📭 {keywords} Jobs - No New Roles - {date_str}"
            html_content = self._generate_no_jobs_html(keywords, date_str)
        
        # Create email
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = formataddr((self.from_name, self.from_email))
        message['To'] = ", ".join(to_emails)
        message.attach(MIMEText(html_content, 'html'))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.ehlo()
                if self.use_tls:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_emails, message.as_string())

            print(f"   ✓ Email sent successfully to {len(to_emails)} recipient(s)")
            return True

        except Exception as e:
            print(f"   ❌ Failed to send email: {e}")
            return False
    
    def _generate_jobs_html(
        self,
        jobs: List[Dict[str, Any]],
        keywords: str,
        date_str: str
    ) -> str:
        """Generate HTML email content with jobs."""
        
        template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0 0 10px 0;
            font-size: 24px;
        }
        .header .subtitle {
            color: #666;
            font-size: 14px;
        }
        .stats {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 25px;
        }
        .stats .number {
            font-size: 32px;
            font-weight: bold;
        }
        .job-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: box-shadow 0.2s;
        }
        .job-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .job-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0 0 8px 0;
        }
        .job-title a {
            color: #3498db;
            text-decoration: none;
        }
        .job-title a:hover {
            text-decoration: underline;
        }
        .job-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .job-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .keywords {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }
        .keyword {
            background: #e8f4fd;
            color: #2980b9;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .apply-btn {
            display: inline-block;
            background: #27ae60;
            color: white !important;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            margin-top: 10px;
        }
        .apply-btn:hover {
            background: #219a52;
        }
        .source-badge {
            background: #f0f0f0;
            color: #666;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            text-transform: uppercase;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #888;
            font-size: 12px;
        }
        .divider {
            height: 1px;
            background: #e0e0e0;
            margin: 20px 0;
        }
        @media (max-width: 600px) {
            body { padding: 10px; }
            .container { padding: 20px; }
            .job-meta { flex-direction: column; gap: 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 {{ keywords }} Jobs</h1>
            <div class="subtitle">Daily Digest • {{ date_str }}</div>
        </div>
        
        <div class="stats">
            <div class="number">{{ jobs|length }}</div>
            <div>new jobs found in the last 24 hours</div>
        </div>
        
        {% for job in jobs %}
        <div class="job-card">
            <h3 class="job-title">
                <a href="{{ job.url }}" target="_blank">📌 {{ job.title }}</a>
            </h3>
            <div class="job-meta">
                <span>🏢 {{ job.company or 'Company not specified' }}</span>
                <span>📍 {{ job.location or 'Location not specified' }}</span>
                <span class="source-badge">{{ job.source }}</span>
            </div>
            {% if job.keywords %}
            <div class="keywords">
                {% for kw in job.keywords %}
                <span class="keyword">{{ kw }}</span>
                {% endfor %}
            </div>
            {% endif %}
            <a href="{{ job.url }}" class="apply-btn" target="_blank">Apply Now →</a>
        </div>
        {% endfor %}
        
        <div class="footer">
            <p>This email was sent by Job Aggregator</p>
            <p>Jobs are aggregated from: Remotive, RemoteOK, Arbeitnow, Google Jobs</p>
        </div>
    </div>
</body>
</html>
        ''')
        
        return template.render(
            jobs=jobs,
            keywords=keywords,
            date_str=date_str
        )
    
    def _generate_no_jobs_html(self, keywords: str, date_str: str) -> str:
        """Generate HTML for no jobs found."""
        
        template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #2c3e50;
            margin: 0 0 15px 0;
        }
        .message {
            color: #666;
            font-size: 16px;
            margin-bottom: 20px;
        }
        .info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            color: #555;
            font-size: 14px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #888;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📭</div>
        <h1>No New {{ keywords }} Jobs</h1>
        <p class="message">We didn't find any new roles matching your criteria in the last 24 hours.</p>
        <div class="info">
            <p><strong>Don't worry!</strong> We'll keep searching and notify you when new opportunities appear.</p>
            <p>Search keywords: {{ keywords }}</p>
        </div>
        <div class="footer">
            <p>Job Aggregator • {{ date_str }}</p>
        </div>
    </div>
</body>
</html>
        ''')
        
        return template.render(
            keywords=keywords,
            date_str=date_str
        )
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify configuration.
        
        Args:
            to_email: Recipient email address
        
        Returns:
            True if sent successfully
        """
        test_jobs = [
            {
                'title': 'Test Job - Senior CRM Manager',
                'company': 'Test Company Inc.',
                'location': 'Remote, USA',
                'url': 'https://example.com/job/test',
                'source': 'test',
                'keywords': ['CRM', 'Marketing'],
            }
        ]
        
        return self.send_job_digest(
            to_emails=[to_email],
            jobs=test_jobs,
            keywords='Test',
            date_str=datetime.now().strftime('%a, %b %d')
        )


