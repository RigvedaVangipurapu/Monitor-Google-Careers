# Google Careers Job Monitor

An automated system that monitors Google Careers for job count changes and sends email alerts when new jobs are posted.

## Features

- 🔍 Monitors Google Careers job count every hour (Data-related jobs)
- 📧 Sends email alerts when job count changes
- 🚀 Runs automatically using GitHub Actions (FREE)
- 📊 Tracks changes across all job pages
- 🔒 Secure email configuration using GitHub Secrets

## Setup Instructions

### 1. Create GitHub Repository

1. Create a new repository on GitHub
2. Upload all files from this project to the repository
3. Make sure the repository is public (for free GitHub Actions)

### 2. Configure Email Settings

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SMTP_SERVER` | Your email provider's SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (usually 587) | `587` |
| `SENDER_EMAIL` | Your email address | `your.email@gmail.com` |
| `SENDER_PASSWORD` | Your email password or app password | `your_password` |
| `RECIPIENT_EMAIL` | Where to send alerts | `alerts@yourdomain.com` |

### 3. Email Provider Setup

#### For Gmail:
1. Enable 2-factor authentication
2. Generate an "App Password" for this application
3. Use the app password as `SENDER_PASSWORD`

#### For Outlook/Hotmail:
- Use `smtp-mail.outlook.com` as SMTP_SERVER
- Use your regular password

#### For Other Providers:
- Check your email provider's SMTP settings

### 4. Enable GitHub Actions

1. Go to your repository → Actions tab
2. Click "I understand my workflows, go ahead and enable them"
3. The workflow will start running automatically every hour

## How It Works

1. **Every hour**, GitHub Actions runs the monitoring script
2. **Extracts** the current job count from Google Careers
3. **Compares** with the previously stored count
4. **Sends email** if the count has changed
5. **Updates** the stored count for the next run

## Monitoring

- Check the **Actions** tab in your repository to see run history
- View logs to see what the script detected
- Email alerts will be sent to your configured recipient

## Customization

### Change Monitoring Frequency
Edit `.github/workflows/career-monitor.yml`:
```yaml
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
  - cron: '0 9,17 * * *'  # 9 AM and 5 PM daily
```

### Change Target URL
Edit `career_monitor.py`:
```python
TARGET_URL = "your_custom_career_page_url"
```

### Change Job Selector
If the job count element changes, update:
```python
JOB_COUNT_SELECTOR = "your_new_selector"
```

## Files

- `career_monitor.py` - Main monitoring script
- `.github/workflows/career-monitor.yml` - GitHub Actions workflow
- `requirements.txt` - Python dependencies
- `known_job_count.txt` - Stores the last known job count (auto-created)

## Troubleshooting

### No emails received?
1. Check GitHub Secrets are set correctly
2. Verify email credentials work
3. Check Actions logs for errors
4. Ensure recipient email is correct

### Script not running?
1. Check Actions tab for failed runs
2. Verify the workflow file is in `.github/workflows/`
3. Make sure the repository is public (for free tier)

### Job count not detected?
1. Check if Google changed their page structure
2. Update `JOB_COUNT_SELECTOR` if needed
3. Check Actions logs for specific errors

## Cost

- **GitHub Actions**: FREE for public repositories
- **Email**: Uses your existing email account
- **Total cost**: $0

## Support

If you encounter issues:
1. Check the Actions logs in your repository
2. Verify all secrets are set correctly
3. Test email credentials manually
4. Check if the target website structure changed
