#!/usr/bin/env python3
"""
Automated Career Page Notification System
Monitors Google Careers for job count changes and sends email alerts
"""

from playwright.sync_api import sync_playwright
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configuration variables - Multiple URLs to monitor
TARGET_URLS = {
    "google_data": {
        "url": "https://www.google.com/about/careers/applications/jobs/results?location=United%20States&target_level=MID&target_level=EARLY&employment_type=FULL_TIME&degree=ASSOCIATE&degree=BACHELORS&degree=MASTERS&q=%22Data%22&sort_by=date",
        "name": "Google Data Jobs",
        "selector": "span.SWhIm"
    },
    "google_data_engineer": {
        "url": "https://www.google.com/about/careers/applications/jobs/results?q=%22data%20engineer%22&sort_by=date&target_level=MID&target_level=EARLY&location=United%20States&employment_type=FULL_TIME",
        "name": "Google Data Engineer Jobs",
        "selector": "span.SWhIm"
    },
    "google_analyst": {
        "url": "https://www.google.com/about/careers/applications/jobs/results?location=United%20States&target_level=MID&target_level=EARLY&employment_type=FULL_TIME&degree=ASSOCIATE&degree=BACHELORS&degree=MASTERS&q=%22Analyst%22&sort_by=date",
        "name": "Google Analyst Jobs",
        "selector": "span.SWhIm"
    },
    "google_early_analyst": {
        "url": "https://www.google.com/about/careers/applications/jobs/results?q=%22analyst%22&sort_by=date&target_level=EARLY&location=United%20States&employment_type=FULL_TIME",
        "name": "Google Early Career Analyst Jobs",
        "selector": "span.SWhIm"
    },
    "google_software_engineer": {
        "url": "https://www.google.com/about/careers/applications/jobs/results?q=%22Software%20Engineer%22&location=United%20States&target_level=MID&target_level=EARLY&sort_by=date",
        "name": "Google Software Engineer Jobs",
        "selector": "span.SWhIm"
    }
}

SCREENSHOT_PATH = "career_page_screenshot.png"
KNOWN_JOBS_FILE = "known_job_counts.json"  # Changed to JSON for multiple URLs
KNOWN_TOP_JOBS_FILE = "known_top_jobs.json"  # Track top 5 jobs for each category

# Email configuration (will be set via environment variables in GitHub Actions)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
RECIPIENT_EMAILS = os.getenv('RECIPIENT_EMAILS', '')  # Comma-separated list of emails

def extract_job_count(page, selector):
    """Extract the total job count from the career page"""
    print("Extracting job count...")
    
    try:
        # Wait for the job count element to load
        page.wait_for_selector(selector, timeout=10000)
        
        # Get the job count element
        job_count_element = page.query_selector(selector)
        
        if job_count_element:
            job_count_text = job_count_element.inner_text().strip()
            print(f"Raw job count text: '{job_count_text}'")
            
            # Extract the number from the text
            try:
                job_count = int(job_count_text)
                print(f"Successfully extracted job count: {job_count}")
                return job_count
            except ValueError:
                print(f"Could not parse job count from text: '{job_count_text}'")
                return None
        else:
            print("Job count element not found")
            return None
            
    except Exception as e:
        print(f"Error extracting job count: {str(e)}")
        return None

def load_known_job_counts():
    """Load the last known job counts from file"""
    try:
        if os.path.exists(KNOWN_JOBS_FILE):
            with open(KNOWN_JOBS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading known job counts: {str(e)}")
        return {}

def save_job_counts(counts):
    """Save the current job counts to file"""
    try:
        with open(KNOWN_JOBS_FILE, 'w') as f:
            json.dump(counts, f, indent=2)
        print(f"Saved job counts to {KNOWN_JOBS_FILE}")
    except Exception as e:
        print(f"Error saving job counts: {str(e)}")

def extract_top_jobs(page, max_jobs=5):
    """Extract top job titles from the career page"""
    try:
        # Look for job titles with the specific class QJPWVe
        job_elements = page.query_selector_all('h3.QJPWVe')
        jobs = []
        
        for element in job_elements:
            job_title = element.inner_text().strip()
            if job_title and len(job_title) > 5:  # Basic validation
                jobs.append(job_title)
                if len(jobs) >= max_jobs:
                    break
        
        print(f"Extracted {len(jobs)} job titles from h3.QJPWVe elements")
        return jobs[:max_jobs]  # Return only top 5
        
    except Exception as e:
        print(f"Error extracting job titles: {str(e)}")
        return []

def load_known_top_jobs():
    """Load previously known top jobs from JSON file"""
    try:
        if os.path.exists(KNOWN_TOP_JOBS_FILE):
            with open(KNOWN_TOP_JOBS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading known top jobs: {str(e)}")
        return {}

def save_top_jobs(top_jobs):
    """Save top jobs to JSON file"""
    try:
        with open(KNOWN_TOP_JOBS_FILE, 'w') as f:
            json.dump(top_jobs, f, indent=2)
        print(f"Saved top jobs to {KNOWN_TOP_JOBS_FILE}")
    except Exception as e:
        print(f"Error saving top jobs: {str(e)}")

def compare_top_jobs(current_jobs, previous_jobs, source_name):
    """Compare current and previous top jobs and return changes"""
    changes = []
    
    if not previous_jobs:
        # First run - all jobs are new
        for job in current_jobs:
            changes.append({
                'action': 'new',
                'job_title': job,
                'position': current_jobs.index(job) + 1
            })
        return changes
    
    # Check for new jobs
    for i, job in enumerate(current_jobs):
        if job not in previous_jobs:
            changes.append({
                'action': 'new',
                'job_title': job,
                'position': i + 1
            })
    
    # Check for removed jobs
    for job in previous_jobs:
        if job not in current_jobs:
            changes.append({
                'action': 'removed',
                'job_title': job,
                'position': previous_jobs.index(job) + 1
            })
    
    # Check for position changes
    for i, job in enumerate(current_jobs):
        if job in previous_jobs:
            old_position = previous_jobs.index(job) + 1
            new_position = i + 1
            if old_position != new_position:
                changes.append({
                    'action': 'moved',
                    'job_title': job,
                    'old_position': old_position,
                    'new_position': new_position
                })
    
    return changes

def send_email_alert(changes, job_changes=None):
    """Send personalized email alert when job counts change or top jobs change"""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAILS]):
        print("Email configuration incomplete. Skipping email alert.")
        return False
    
    # Parse recipient emails (comma-separated)
    recipient_list = [email.strip() for email in RECIPIENT_EMAILS.split(',') if email.strip()]
    if not recipient_list:
        print("No valid recipient emails found. Skipping email alert.")
        return False
    
    try:
        # Create personalized subject based on what changed
        if len(changes) == 1:
            source_name = list(changes.values())[0]['name']
            change = list(changes.values())[0]['current'] - list(changes.values())[0]['previous']
            change_text = f"+{change}" if change > 0 else str(change)
            subject = f"🚨 {source_name} Alert: {change_text} jobs"
        else:
            subject = f"🚨 Multiple Job Alerts: {len(changes)} categories changed"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(recipient_list)  # Show all recipients in To field
        msg['Subject'] = subject
        
        # Build personalized email body
        body = "🎯 Google Careers Job Monitoring Alert\n"
        body += "=" * 50 + "\n\n"
        body += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add personalized message based on changes
        total_new_jobs = sum(data['current'] - data['previous'] for data in changes.values() if data['current'] > data['previous'])
        total_removed_jobs = sum(data['previous'] - data['current'] for data in changes.values() if data['current'] < data['previous'])
        
        if total_new_jobs > 0:
            body += f"🎉 Great news! {total_new_jobs} new job(s) posted!\n\n"
        if total_removed_jobs > 0:
            body += f"📉 {total_removed_jobs} job(s) were removed.\n\n"
        
        # Add job changes if any
        if job_changes:
            body += "🆕 NEW JOB POSTINGS:\n"
            body += "-" * 30 + "\n\n"
            for source, changes_list in job_changes.items():
                if changes_list:
                    body += f"📋 {source}:\n"
                    for change in changes_list:
                        if change['action'] == 'new':
                            body += f"   • #{change['position']}: {change['job_title']}\n"
                        elif change['action'] == 'removed':
                            body += f"   • ❌ Removed: {change['job_title']}\n"
                        elif change['action'] == 'moved':
                            body += f"   • 🔄 Moved: {change['job_title']} (#{change['old_position']} → #{change['new_position']})\n"
                    body += "\n"
        
        body += "📊 DETAILED BREAKDOWN:\n"
        body += "-" * 30 + "\n\n"
        
        for source, data in changes.items():
            change = data['current'] - data['previous']
            change_text = f"+{change}" if change > 0 else str(change)
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            
            body += f"{emoji} {data['name']}:\n"
            body += f"   • Previous: {data['previous']} jobs\n"
            body += f"   • Current: {data['current']} jobs\n"
            body += f"   • Change: {change_text} jobs\n"
            body += f"   • 🔗 View Jobs: {data['url']}\n\n"
        
        body += "🤖 This is an automated alert from your career monitoring system.\n"
        body += "💡 Set up job alerts on Google Careers for instant notifications!"
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email to all recipients
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient_list, text)
        server.quit()
        
        print(f"📧 Personalized email alert sent to {len(recipient_list)} recipient(s)! {len(changes)} source(s) changed.")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def main():
    """Main function to monitor multiple job sources and send alerts"""
    print("Starting multi-source career monitoring system...")
    print(f"Monitoring {len(TARGET_URLS)} job sources:")
    for key, config in TARGET_URLS.items():
        print(f"  • {config['name']}")
    
    try:
        with sync_playwright() as p:
            # Launch browser
            print("\nLaunching browser...")
            browser = p.chromium.launch(headless=True)  # Headless for GitHub Actions
            page = browser.new_page()
            
            # Load previous job counts and top jobs
            known_counts = load_known_job_counts()
            known_top_jobs = load_known_top_jobs()
            current_counts = {}
            current_top_jobs = {}
            changes = {}
            increases = {}  # Track only increases for email alerts
            job_changes = {}  # Track changes in top jobs
            
            # Monitor each URL
            for source_key, config in TARGET_URLS.items():
                print(f"\n--- Monitoring {config['name']} ---")
                print(f"URL: {config['url']}")
                
                try:
                    # Navigate to the URL
                    page.goto(config['url'], wait_until="networkidle")
                    
                    # Extract job count
                    current_count = extract_job_count(page, config['selector'])
                    
                    if current_count is None:
                        print(f"Failed to extract job count for {config['name']}")
                        continue
                    
                    current_counts[source_key] = current_count
                    previous_count = known_counts.get(source_key)
                    
                    print(f"Current count: {current_count}")
                    
                    # Extract top 5 jobs
                    print("Extracting top 5 jobs...")
                    current_jobs = extract_top_jobs(page)
                    current_top_jobs[source_key] = current_jobs
                    
                    # Compare with previous top jobs
                    previous_jobs = known_top_jobs.get(source_key, [])
                    job_changes_list = compare_top_jobs(current_jobs, previous_jobs, config['name'])
                    
                    if job_changes_list:
                        job_changes[config['name']] = job_changes_list
                        print(f"Job changes detected: {len(job_changes_list)} changes")
                        for change in job_changes_list:
                            if change['action'] == 'new':
                                print(f"  🆕 New: #{change['position']} {change['job_title']}")
                            elif change['action'] == 'removed':
                                print(f"  ❌ Removed: {change['job_title']}")
                            elif change['action'] == 'moved':
                                print(f"  🔄 Moved: {change['job_title']} (#{change['old_position']} → #{change['new_position']})")
                    else:
                        print("No job changes detected in top 5")
                    
                    if previous_count is None:
                        # First run for this source
                        print(f"First run for {config['name']}. Saving initial count.")
                    else:
                        print(f"Previous count: {previous_count}")
                        
                        if current_count != previous_count:
                            # Job count changed
                            change = current_count - previous_count
                            change_text = f"+{change}" if change > 0 else str(change)
                            print(f"Job count changed! {previous_count} → {current_count} ({change_text})")
                            
                            # Record the change
                            changes[source_key] = {
                                'name': config['name'],
                                'url': config['url'],
                                'previous': previous_count,
                                'current': current_count
                            }
                            
                            # Track increases separately for email alerts
                            if current_count > previous_count:
                                increases[source_key] = changes[source_key]
                        else:
                            print("No changes detected.")
                
                except Exception as e:
                    print(f"Error monitoring {config['name']}: {str(e)}")
                    continue
            
            # Close browser
            browser.close()
            
            # Send email if there were increases OR job changes
            if increases or job_changes:
                print(f"\n📧 Sending email alert...")
                if increases:
                    print(f"  • {len(increases)} source(s) with increased job counts")
                if job_changes:
                    print(f"  • {len(job_changes)} source(s) with job changes")
                
                if send_email_alert(increases, job_changes):
                    print("Email alert sent successfully!")
                else:
                    print("Failed to send email alert.")
            elif changes:
                print(f"\n📊 {len(changes)} source(s) changed but no increases or job changes detected. No email sent.")
            else:
                print("\n✅ No changes detected across all sources.")
            
            # Update stored counts and top jobs
            save_job_counts(current_counts)
            save_top_jobs(current_top_jobs)
            
            print("\n🎯 Multi-source monitoring completed successfully!")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("Script completed successfully!")
    else:
        print("Script failed!")
