# Google Credentials Setup Guide 📅

This guide will walk you through setting up Google credentials for the PM Bot to access Google Calendar and Google Drive for meeting notes processing and document analysis.

## Prerequisites 📋

- Google account with access to Google Cloud Console
- Admin permissions for Google Workspace (if applicable)
- Access to calendars and meetings you want to process

## Overview 🗺️

The PM Bot needs Google credentials to:
- **📅 Access Google Calendar**: Read meeting events and schedules
- **💾 Access Google Drive**: Read meeting recordings and transcripts
- **🤝 Access Google Meet**: Process meeting data and notes

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console:**
   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project:**
   - Click the project dropdown at the top
   - Click **"New Project"**
   - Enter project details:
     ```
     Project name: PM Bot Integration
     Organization: Your organization (if applicable)
     Location: Your organization (if applicable)
     ```
   - Click **"Create"**

3. **Select Your Project:**
   - Ensure your new project is selected in the project dropdown

## Step 2: Enable Required APIs

1. **Navigate to APIs & Services:**
   - In the left sidebar, go to **"APIs & Services" → "Library"**

2. **Enable Google Calendar API:**
   - Search for "Google Calendar API"
   - Click on it and click **"Enable"**

3. **Enable Google Drive API:**
   - Search for "Google Drive API"
   - Click on it and click **"Enable"**

4. **Enable Google Meet API (Optional):**
   - Search for "Google Meet API"
   - Click on it and click **"Enable"**

## Step 3: Choose Authentication Method

### Method A: Service Account (Recommended for Server Applications)

**Best for:** Automated server applications, no user interaction required

#### Create Service Account:

1. **Navigate to Credentials:**
   - Go to **"APIs & Services" → "Credentials"**

2. **Create Service Account:**
   - Click **"+ Create Credentials" → "Service Account"**
   - Enter details:
     ```
     Service account name: pm-bot-service
     Service account ID: pm-bot-service (auto-generated)
     Description: Service account for PM Bot Google integration
     ```
   - Click **"Create and Continue"**

3. **Grant Permissions (Optional):**
   - For basic access, you can skip this step
   - Click **"Continue"** and then **"Done"**

4. **Create and Download Key:**
   - Click on the service account you just created
   - Go to the **"Keys"** tab
   - Click **"Add Key" → "Create new key"**
   - Select **"JSON"** format
   - Click **"Create"**
   - The key file will download automatically

5. **Rename and Place the File:**
   ```bash
   # Move the downloaded file to your project directory
   mv ~/Downloads/pm-bot-service-*.json ./credentials.json
   ```

#### Configure Domain-Wide Delegation (For Google Workspace):

If you need to access other users' calendars:

1. **Enable Domain-Wide Delegation:**
   - Go to your service account settings
   - Check **"Enable Google Workspace Domain-wide Delegation"**
   - Add a product name: "PM Bot"
   - Click **"Save"**

2. **Note the Client ID:**
   - Copy the service account's Client ID (long number)

3. **Configure in Google Workspace Admin:**
   - Go to Google Workspace Admin Console
   - Navigate to **Security → API Controls → Domain-wide delegation**
   - Click **"Add new"**
   - Add the Client ID with these scopes:
     ```
     https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/drive.readonly
     ```

### Method B: OAuth 2.0 (For User Access)

**Best for:** Applications that need user-specific access

#### Configure OAuth Consent Screen:

1. **Navigate to OAuth Consent Screen:**
   - Go to **"APIs & Services" → "OAuth consent screen"**

2. **Choose User Type:**
   - Select **"External"** (unless you have Google Workspace)
   - Click **"Create"**

3. **Fill in App Information:**
   ```
   App name: PM Bot
   User support email: your-email@domain.com
   App logo: (optional)
   App domain: (optional)
   Developer contact information: your-email@domain.com
   ```
   - Click **"Save and Continue"**

4. **Add Scopes:**
   - Click **"Add or Remove Scopes"**
   - Add these scopes:
     ```
     https://www.googleapis.com/auth/calendar.readonly
     https://www.googleapis.com/auth/drive.readonly
     https://www.googleapis.com/auth/meetings.space.readonly
     ```
   - Click **"Update"** and **"Save and Continue"**

5. **Add Test Users (if External):**
   - Add email addresses of users who will use the bot
   - Click **"Save and Continue"**

#### Create OAuth Credentials:

1. **Create OAuth Client:**
   - Go to **"Credentials"**
   - Click **"+ Create Credentials" → "OAuth client ID"**
   - Select **"Desktop application"**
   - Name: `PM Bot Desktop Client`
   - Click **"Create"**

2. **Download Credentials:**
   - Click **"Download JSON"** for the OAuth client
   - Save as `credentials.json` in your project directory

## Step 4: Configure Environment Variables

Add these variables to your `.env` file:

```env
# Google Meet/Calendar Configuration
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
GOOGLE_MEETING_LOOKBACK_DAYS=7
```

## Step 5: Test Your Credentials

1. **Install Required Packages:**
   ```bash
   # Using uv (recommended - much faster)
   uv pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   
   # Or using pip
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. **Run the Test Script:**
   ```bash
   python test_google_auth.py
   ```

3. **Follow OAuth Flow (if using OAuth):**
   - A browser window will open for authentication
   - Sign in with your Google account
   - Grant the requested permissions
   - The token will be saved automatically

## Required Scopes 🔐

| Scope | Purpose | Permission Level |
|-------|---------|------------------|
| `https://www.googleapis.com/auth/calendar.readonly` | Read calendar events and meeting information | Read-only |
| `https://www.googleapis.com/auth/drive.readonly` | Access meeting recordings and transcripts | Read-only |
| `https://www.googleapis.com/auth/meetings.space.readonly` | Access Google Meet data | Read-only |

## Authentication Methods Comparison 📊

| Method | Best For | Setup Complexity | User Experience | Security |
|--------|----------|------------------|-----------------|----------|
| **Service Account** | Server apps, automated access | Medium | No user interaction | High |
| **OAuth 2.0** | User-specific access | High | Users must authenticate | Medium |

## Step 6: Verify Setup

Your project directory should have:

```
pm-bot/
├── credentials.json          # Google API credentials
├── token.json               # OAuth token (if using OAuth)
├── test_google_auth.py      # Test script
└── .env                     # Environment configuration
```

## Step 7: Set File Permissions

```bash
# Set proper permissions for security
chmod 600 credentials.json
chmod 600 token.json
```

## Testing Your Setup 🧪

### Expected Test Output:

```
🔍 Testing Google API credentials...

🔐 Testing OAuth authentication...
✅ OAuth authentication successful!
💾 Token saved to token.json

📅 Testing Calendar API access...
✅ Found 3 calendars
   📅 Primary Calendar (your-email@gmail.com)
   📅 Work Calendar (work@company.com)
   📅 Team Calendar (team@company.com)
✅ Found 5 recent events
   🗓️  Sprint Planning (2024-01-15T10:00:00-08:00)
   🗓️  Daily Standup (2024-01-16T09:00:00-08:00)

💾 Testing Drive API access...
✅ Found 5 recent files
   📄 Meeting Recording.mp4 (video/mp4)
   📄 Sprint Notes.docx (application/vnd.openxmlformats)

==================================================
📊 Test Results Summary:
🔐 Authentication: ✅ Success
📅 Calendar API: ✅ Success
💾 Drive API: ✅ Success

🎉 All tests passed! Your Google credentials are working correctly.
```

## Advanced Configuration ⚙️

### For Google Workspace Organizations:

1. **Admin Console Settings:**
   - Navigate to Google Admin Console
   - Go to **Security → API Controls**
   - Ensure APIs are not restricted

2. **Organizational Units:**
   - Configure access for specific OUs
   - Set policies for API access

### Rate Limiting:

Google APIs have usage limits:
- **Calendar API**: 1,000,000 queries/day
- **Drive API**: 1,000,000,000 queries/day
- **Per-user rate limit**: 250 requests/100 seconds/user

## Troubleshooting 🔧

### Common Issues:

1. **"Credentials not found" error:**
   ```bash
   # Ensure credentials.json exists
   ls -la credentials.json
   
   # Check file permissions
   chmod 600 credentials.json
   ```

2. **"API not enabled" error:**
   - Go to Google Cloud Console
   - Enable Calendar API and Drive API
   - Wait a few minutes for changes to propagate

3. **"Insufficient permissions" error:**
   - Check OAuth scopes
   - For service accounts, verify domain-wide delegation
   - Ensure the user has access to the calendars

4. **"Invalid grant" error:**
   ```bash
   # Delete and regenerate token
   rm token.json
   python test_google_auth.py
   ```

5. **"Access blocked" error:**
   - Verify OAuth consent screen is configured
   - Add users to test users list
   - Check organization policies

### Debug Commands:

```bash
# Test credentials file
python -c "import json; print(json.load(open('credentials.json'))['type'])"

# Check token validity
python -c "
import json
from google.oauth2.credentials import Credentials
creds = Credentials.from_authorized_user_file('token.json')
print(f'Valid: {creds.valid}')
print(f'Expired: {creds.expired}')
"
```

## Security Best Practices 🔒

1. **Protect Credentials:**
   ```bash
   # Set restrictive permissions
   chmod 600 credentials.json token.json
   
   # Add to .gitignore
   echo "credentials.json" >> .gitignore
   echo "token.json" >> .gitignore
   ```

2. **Use Least Privilege:**
   - Only request necessary scopes
   - Use readonly scopes when possible
   - Regularly review and rotate credentials

3. **Monitor Usage:**
   - Check Google Cloud Console for API usage
   - Set up quotas and alerts
   - Monitor for unusual activity

4. **For Production:**
   - Use service accounts when possible
   - Store credentials securely (e.g., using secrets management)
   - Implement proper error handling and logging

## Integration with PM Bot 🤖

Once configured, the PM Bot can:

1. **📅 Process Calendar Events:**
   - Find meetings by keyword
   - Extract meeting participants
   - Identify meeting types (standup, sprint planning, etc.)

2. **💾 Access Meeting Files:**
   - Download meeting recordings
   - Read transcripts from Google Drive
   - Extract meeting notes and documents

3. **🔄 Automated Processing:**
   - Convert raw meeting data to structured format
   - Generate professional documentation
   - Create Confluence pages with action items

## API Quotas and Limits 📊

### Calendar API Limits:
- **Queries per day**: 1,000,000
- **Queries per 100 seconds per user**: 250
- **Queries per 100 seconds**: 10,000

### Drive API Limits:
- **Queries per day**: 1,000,000,000
- **Queries per 100 seconds per user**: 1,000
- **Queries per 100 seconds**: 10,000

### Best Practices:
- Implement exponential backoff
- Cache results when possible
- Batch requests where supported
- Monitor usage in Google Cloud Console

## Support Resources 📚

- **Google Calendar API Documentation**: https://developers.google.com/calendar
- **Google Drive API Documentation**: https://developers.google.com/drive
- **Google Cloud Console**: https://console.cloud.google.com/
- **API Explorer**: https://developers.google.com/apis-explorer/
- **Stack Overflow**: Tag questions with `google-api` and `google-calendar-api`

## Next Steps ➡️

1. **Test Integration:**
   ```bash
   # Start the PM Bot
   docker-compose up -d
   
   # Test meeting processing
   # In Slack: /process-meetings space=PROJ
   ```

2. **Monitor Logs:**
   ```bash
   ./docker-run.sh logs
   ```

3. **Optimize Configuration:**
   - Adjust `GOOGLE_MEETING_LOOKBACK_DAYS`
   - Configure additional scopes if needed
   - Set up monitoring and alerts

Your Google credentials are now configured! The PM Bot can access your Google Calendar and Drive to process meeting notes and create comprehensive documentation. 🎉 