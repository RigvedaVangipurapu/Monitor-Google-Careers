#!/bin/bash

echo "🚀 Setting up Google Careers Job Monitor for GitHub Actions"
echo "=========================================================="

echo ""
echo "📋 Next steps:"
echo "1. Create a new repository on GitHub"
echo "2. Upload all files from this directory to the repository"
echo "3. Go to repository Settings → Secrets and variables → Actions"
echo "4. Add these secrets:"
echo "   - SMTP_SERVER: smtp.gmail.com"
echo "   - SMTP_PORT: 587"
echo "   - SENDER_EMAIL: your.email@gmail.com"
echo "   - SENDER_PASSWORD: your_app_password"
echo "   - RECIPIENT_EMAIL: alerts@yourdomain.com"
echo "5. Go to Actions tab and enable workflows"
echo "6. The monitor will run every hour automatically!"

echo ""
echo "📧 For Gmail setup:"
echo "1. Enable 2-factor authentication"
echo "2. Generate an 'App Password' for this application"
echo "3. Use the app password as SENDER_PASSWORD"

echo ""
echo "✅ Setup complete! Check README.md for detailed instructions."
