#!/usr/bin/env python3
"""
Automated Career Page Notification System
Monitors Google Careers for job count changes and sends email alerts
"""

from playwright.sync_api import sync_playwright
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configuration variables
TARGET_URL = "https://www.google.com/about/careers/applications/jobs/results?location=United%20States&target_level=MID&target_level=EARLY&employment_type=FULL_TIME&degree=ASSOCIATE&degree=BACHELORS&degree=MASTERS&q=%22Data%22&sort_by=relevance"
JOB_COUNT_SELECTOR = "span.SWhIm"  # Selector for the job count number
SCREENSHOT_PATH = "career_page_screenshot.png"
KNOWN_JOBS_FILE = "known_job_count.txt"

# Email configuration (will be set via environment variables in GitHub Actions)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', '')

def extract_job_count(page):
    """Extract the total job count from the career page"""
    print("Extracting job count...")
    
    try:
        # Wait for the job count element to load
        page.wait_for_selector(JOB_COUNT_SELECTOR, timeout=10000)
        
        # Get the job count element
        job_count_element = page.query_selector(JOB_COUNT_SELECTOR)
        
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

def load_known_job_count():
    """Load the last known job count from file"""
    try:
        if os.path.exists(KNOWN_JOBS_FILE):
            with open(KNOWN_JOBS_FILE, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        return None
    except Exception as e:
        print(f"Error loading known job count: {str(e)}")
        return None

def save_job_count(count):
    """Save the current job count to file"""
    try:
        with open(KNOWN_JOBS_FILE, 'w') as f:
            f.write(str(count))
        print(f"Saved job count {count} to {KNOWN_JOBS_FILE}")
    except Exception as e:
        print(f"Error saving job count: {str(e)}")

def send_email_alert(previous_count, current_count):
    """Send email alert when job count changes"""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]):
        print("Email configuration incomplete. Skipping email alert.")
        return False
    
    try:
        # Calculate change
        change = current_count - previous_count
        change_text = f"+{change}" if change > 0 else str(change)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"Google Careers Alert: Job Count Changed ({change_text})"
        
        # Email body
        body = f"""
Google Careers Job Monitoring Alert

Job count has changed:
• Previous count: {previous_count}
• Current count: {current_count}
• Change: {change_text} jobs

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

View jobs: {TARGET_URL}

This is an automated alert from your career monitoring system.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)
        server.quit()
        
        print(f"Email alert sent successfully! Change: {change_text}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def main():
    """Main function to monitor job count changes and send alerts"""
    print("Starting career page monitoring system...")
    print(f"Target URL: {TARGET_URL}")
    print(f"Job count selector: {JOB_COUNT_SELECTOR}")
    
    try:
        with sync_playwright() as p:
            # Launch browser
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)  # Headless for GitHub Actions
            page = browser.new_page()
            
            # Navigate to the target URL
            print(f"Navigating to {TARGET_URL}...")
            page.goto(TARGET_URL, wait_until="networkidle")
            
            # Get page title to verify we're on the right page
            page_title = page.title()
            print(f"Page loaded successfully. Title: {page_title}")
            
            # Extract current job count
            current_count = extract_job_count(page)
            
            if current_count is None:
                print("Failed to extract job count. Exiting.")
                browser.close()
                return False
            
            print(f"\nCurrent job count: {current_count}")
            
            # Load previous job count
            previous_count = load_known_job_count()
            
            if previous_count is None:
                # First run - save current count
                print("First run detected. Saving initial job count.")
                save_job_count(current_count)
                print(f"Initial job count {current_count} saved. No alert sent.")
            else:
                # Compare counts
                print(f"Previous job count: {previous_count}")
                
                if current_count != previous_count:
                    # Job count changed - send alert
                    change = current_count - previous_count
                    change_text = f"+{change}" if change > 0 else str(change)
                    print(f"Job count changed! {previous_count} → {current_count} ({change_text})")
                    
                    # Send email alert
                    if send_email_alert(previous_count, current_count):
                        print("Email alert sent successfully!")
                    else:
                        print("Failed to send email alert.")
                    
                    # Update the stored count
                    save_job_count(current_count)
                else:
                    print("No changes detected. Job count remains the same.")
            
            # Close browser
            browser.close()
            
            print("Monitoring completed successfully!")
            
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
