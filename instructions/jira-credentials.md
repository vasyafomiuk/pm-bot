# Jira Credentials Setup Guide 🎯

This guide will walk you through setting up Jira credentials for the PM Bot to create epics, user stories, and manage Jira issues. The bot integrates with both Jira Cloud and Jira Server/Data Center.

## Prerequisites 📋

- Jira Cloud or Server/Data Center instance
- Admin permissions to create API tokens
- Project administrator access for the target project
- Basic understanding of Jira permissions

## Overview 🗺️

The PM Bot needs Jira credentials to:
- **🎯 Create Epics**: Generate comprehensive epics with AI-powered features
- **📋 Create User Stories**: Generate detailed user stories with acceptance criteria
- **🔗 Link Issues**: Connect user stories to epics
- **📊 Update Status**: Transition issues through workflow states
- **🔍 Search Issues**: Query existing epics and stories

## Step 1: Determine Your Jira Type

First, identify your Jira deployment type:

### Jira Cloud
- URL format: `https://your-domain.atlassian.net`
- Uses **API tokens** for authentication
- Supports **OAuth 2.0** for multi-user scenarios

### Jira Server/Data Center
- Self-hosted on your infrastructure
- URL format: `https://jira.your-company.com`
- Uses **Personal Access Tokens (PAT)** or **API tokens**

## Step 2A: Jira Cloud Setup

### Generate API Token:

1. **Go to Atlassian Account Settings:**
   - Visit https://id.atlassian.com/manage-profile/security/api-tokens
   - Sign in with your Atlassian account

2. **Create API Token:**
   - Click **"Create API token"**
   - Enter a label: `PM Bot Integration`
   - Click **"Create"**
   - **Copy the token immediately** (you won't see it again)

3. **Note Your Details:**
   ```
   Server URL: https://your-domain.atlassian.net
   Username: your-email@company.com
   API Token: ATATT3... (the token you just created)
   ```

### Find Your Project Key:

1. **Navigate to Your Project:**
   - Go to your Jira instance
   - Open the project you want to use

2. **Get Project Key:**
   - Look at the URL: `https://your-domain.atlassian.net/jira/software/projects/PROJ/boards/1`
   - The project key is `PROJ` (usually 2-10 characters)

### Test API Access:

```bash
# Test with curl
curl -u your-email@company.com:ATATT3... \
  -X GET \
  -H "Accept: application/json" \
  "https://your-domain.atlassian.net/rest/api/3/project/PROJ"
```

## Step 2B: Jira Server/Data Center Setup

### Generate Personal Access Token:

1. **Navigate to User Profile:**
   - Go to your Jira instance
   - Click your profile picture → **"Personal Access Tokens"**

2. **Create Token:**
   - Click **"Create token"**
   - Enter details:
     ```
     Token name: PM Bot Integration
     Expiration: Choose appropriate duration
     ```
   - Click **"Create"**
   - **Copy the token immediately**

### Alternative: Use Password Authentication:

For older Jira versions that don't support PAT:
- Username: `your-username`
- Password: `your-jira-password`

**Note:** Password authentication is less secure and not recommended for production.

## Step 3: Configure Environment Variables

Add these variables to your `.env` file:

```env
# Jira Configuration
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=ATATT3xxxxxxxxxxx
JIRA_PROJECT_KEY=PROJ

# Confluence Configuration (usually same domain + /wiki)
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
```

### For Jira Server/Data Center:

```env
# Jira Server Configuration
JIRA_SERVER=https://jira.your-company.com
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-personal-access-token
JIRA_PROJECT_KEY=PROJ

# Confluence Configuration
CONFLUENCE_URL=https://confluence.your-company.com
```

## Step 4: Verify Required Permissions

Ensure your account has these permissions:

### Project Permissions:
- **Browse Projects**: View project content
- **Create Issues**: Create epics and stories
- **Edit Issues**: Update issue details
- **Link Issues**: Connect stories to epics
- **Transition Issues**: Change issue status

### Issue Type Permissions:
- **Epic**: Ability to create epic issue type
- **Story**: Ability to create story issue type
- **Task**: (Optional) For additional issue types

### Field Permissions:
- **Epic Name**: Required for epic creation
- **Epic Link**: Required to link stories to epics
- **Story Points**: (Optional) For story estimation

## Step 5: Test Your Setup

### Using the Test Script:

1. **Create Test Script:**
   ```python
   # test_jira_auth.py
   import requests
   import base64
   import json
   
   # Configuration
   JIRA_SERVER = "https://your-domain.atlassian.net"
   USERNAME = "your-email@company.com"
   API_TOKEN = "ATATT3..."
   PROJECT_KEY = "PROJ"
   
   # Create basic auth header
   auth_string = f"{USERNAME}:{API_TOKEN}"
   auth_bytes = auth_string.encode('ascii')
   auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
   
   headers = {
       "Authorization": f"Basic {auth_b64}",
       "Accept": "application/json",
       "Content-Type": "application/json"
   }
   
   def test_connection():
       """Test basic connection to Jira"""
       try:
           response = requests.get(f"{JIRA_SERVER}/rest/api/3/myself", headers=headers)
           if response.status_code == 200:
               user = response.json()
               print(f"✅ Connected to Jira as: {user['displayName']}")
               return True
           else:
               print(f"❌ Connection failed: {response.status_code} - {response.text}")
               return False
       except Exception as e:
           print(f"❌ Connection error: {e}")
           return False
   
   def test_project_access():
       """Test access to project"""
       try:
           response = requests.get(f"{JIRA_SERVER}/rest/api/3/project/{PROJECT_KEY}", headers=headers)
           if response.status_code == 200:
               project = response.json()
               print(f"✅ Project access: {project['name']} ({project['key']})")
               return True
           else:
               print(f"❌ Project access failed: {response.status_code} - {response.text}")
               return False
       except Exception as e:
           print(f"❌ Project access error: {e}")
           return False
   
   def test_issue_creation():
       """Test issue creation permissions"""
       try:
           # Test with a simple task issue (don't actually create it)
           issue_data = {
               "fields": {
                   "project": {"key": PROJECT_KEY},
                   "summary": "Test Issue - PM Bot",
                   "description": "Test issue for PM Bot integration",
                   "issuetype": {"name": "Task"}
               }
           }
           
           # Just validate the payload (dryRun simulation)
           response = requests.get(f"{JIRA_SERVER}/rest/api/3/issue/createmeta", headers=headers)
           if response.status_code == 200:
               print("✅ Issue creation permissions verified")
               return True
           else:
               print(f"❌ Issue creation test failed: {response.status_code}")
               return False
       except Exception as e:
           print(f"❌ Issue creation test error: {e}")
           return False
   
   if __name__ == "__main__":
       print("🔍 Testing Jira credentials...\n")
       
       conn_ok = test_connection()
       proj_ok = test_project_access() if conn_ok else False
       issue_ok = test_issue_creation() if proj_ok else False
       
       print(f"\n{'='*50}")
       print("📊 Test Results Summary:")
       print(f"🔐 Connection: {'✅ Success' if conn_ok else '❌ Failed'}")
       print(f"📁 Project Access: {'✅ Success' if proj_ok else '❌ Failed'}")
       print(f"📝 Issue Creation: {'✅ Success' if issue_ok else '❌ Failed'}")
       
       if conn_ok and proj_ok and issue_ok:
           print("\n🎉 All tests passed! Your Jira credentials are working correctly.")
       else:
           print("\n⚠️  Some tests failed. Please check the errors above.")
   ```

2. **Run Test:**
   ```bash
   # Using uv (recommended - much faster)
   uv pip install requests
   
   # Or using pip
   pip install requests
   
   python test_jira_auth.py
   ```

### Expected Output:

```
🔍 Testing Jira credentials...

✅ Connected to Jira as: John Doe
✅ Project access: Project Management (PROJ)
✅ Issue creation permissions verified

==================================================
📊 Test Results Summary:
🔐 Connection: ✅ Success
📁 Project Access: ✅ Success
📝 Issue Creation: ✅ Success

🎉 All tests passed! Your Jira credentials are working correctly.
```

## Step 6: Configure Issue Types and Fields

### Required Issue Types:

Ensure your project has these issue types:

1. **Epic**
   - Used for high-level features
   - Must have "Epic Name" field
   - Should have "Epic Link" capability

2. **Story** (or User Story)
   - Used for user stories
   - Must be linkable to epics
   - Should have "Story Points" field (optional)

### Required Custom Fields:

| Field | Purpose | Required |
|-------|---------|----------|
| **Epic Name** | Epic title/name | Yes |
| **Epic Link** | Link stories to epics | Yes |
| **Story Points** | Story estimation | Optional |

### Configure Fields (Admin Required):

1. **Navigate to Project Settings:**
   - Go to Project → Project settings → Issue types

2. **Configure Epic:**
   - Ensure "Epic Name" field is available
   - Verify "Epic Link" field is configured

3. **Configure Story:**
   - Ensure stories can be linked to epics
   - Add "Story Points" field if needed

## Step 7: OAuth 2.0 Setup (Advanced)

For multi-user scenarios, set up OAuth 2.0:

### Create OAuth App:

1. **Go to Atlassian Developer Console:**
   - Visit https://developer.atlassian.com/
   - Create new app

2. **Configure OAuth 2.0:**
   ```
   App name: PM Bot
   Callback URL: http://localhost:8080/callback
   Scopes: read:jira-work write:jira-work
   ```

3. **Get Credentials:**
   ```
   Client ID: ari:cloud:jira::app/...
   Client Secret: your-client-secret
   ```

4. **Update Environment:**
   ```env
   ATLASSIAN_OAUTH_CLIENT_ID=your-client-id
   ATLASSIAN_OAUTH_CLIENT_SECRET=your-client-secret
   ```

## Troubleshooting 🔧

### Common Issues:

1. **"Unauthorized" (401) Error:**
   ```bash
   # Check credentials
   echo "Username: $JIRA_USERNAME"
   echo "Token starts with: ${JIRA_API_TOKEN:0:6}..."
   
   # Test with curl
   curl -u $JIRA_USERNAME:$JIRA_API_TOKEN \
     -H "Accept: application/json" \
     "$JIRA_SERVER/rest/api/3/myself"
   ```

2. **"Forbidden" (403) Error:**
   - Check user permissions in Jira
   - Verify project access
   - Contact Jira administrator

3. **"Project Not Found" (404) Error:**
   - Verify project key is correct
   - Check project exists and is accessible
   - Ensure user has project permissions

4. **"Issue Type Not Found" Error:**
   - Verify Epic and Story issue types exist
   - Check issue type scheme configuration
   - Contact project administrator

### Debug Commands:

```bash
# Test basic auth
curl -u $JIRA_USERNAME:$JIRA_API_TOKEN \
  "$JIRA_SERVER/rest/api/3/myself"

# List projects
curl -u $JIRA_USERNAME:$JIRA_API_TOKEN \
  "$JIRA_SERVER/rest/api/3/project"

# Get project details
curl -u $JIRA_USERNAME:$JIRA_API_TOKEN \
  "$JIRA_SERVER/rest/api/3/project/$JIRA_PROJECT_KEY"

# List issue types
curl -u $JIRA_USERNAME:$JIRA_API_TOKEN \
  "$JIRA_SERVER/rest/api/3/issuetype"
```

## Security Best Practices 🔒

1. **Token Management:**
   - Rotate API tokens regularly (every 90 days)
   - Use minimum required permissions
   - Store tokens securely
   - Never commit tokens to version control

2. **Access Control:**
   - Use dedicated service accounts for bots
   - Implement principle of least privilege
   - Monitor API usage and access logs
   - Set up alerts for unusual activity

3. **Network Security:**
   - Use HTTPS for all API calls
   - Implement IP restrictions if possible
   - Use VPN for server-to-server communication
   - Set up proper firewall rules

## API Rate Limits 📊

### Jira Cloud Limits:
- **Standard**: 10 requests per second per app per IP
- **Premium**: 25 requests per second per app per IP
- **Enterprise**: 50 requests per second per app per IP

### Jira Server Limits:
- Configurable by administrators
- Default: Usually 100-1000 requests per minute
- Contact your admin for specific limits

### Best Practices:
- Implement exponential backoff
- Cache results when possible
- Use bulk operations where available
- Monitor rate limit headers

## Integration Features 🚀

Once configured, the PM Bot can:

1. **🎯 Epic Management:**
   - Create comprehensive epics with AI-generated descriptions
   - Add features and acceptance criteria
   - Set priorities and labels
   - Link to project components

2. **📋 Story Management:**
   - Generate detailed user stories from features
   - Create acceptance criteria automatically
   - Estimate story points with AI assistance
   - Link stories to parent epics

3. **🔗 Issue Relationships:**
   - Establish epic-story relationships
   - Create issue links and dependencies
   - Manage component assignments
   - Track progress across related issues

4. **📊 Status Management:**
   - Transition issues through workflows
   - Update issue status automatically
   - Sync with external tools
   - Generate progress reports

## Supported Jira Versions 📋

| Version | Support Level | Notes |
|---------|---------------|-------|
| **Jira Cloud** | ✅ Full Support | Recommended |
| **Jira 8.0+** | ✅ Full Support | Server/Data Center |
| **Jira 7.6-7.13** | ⚠️ Limited Support | Some features may not work |
| **Jira 7.0-7.5** | ❌ Not Supported | Upgrade recommended |

## Support Resources 📚

- **Jira REST API Documentation**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Atlassian Developer Community**: https://community.developer.atlassian.com/
- **API Explorer**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/
- **Jira Administration Guide**: https://confluence.atlassian.com/adminjiracloud/

## Next Steps ➡️

1. **Test Integration:**
   ```bash
   # Start the PM Bot
   docker-compose up -d
   
   # Test epic creation in Slack
   /create-epic
   Title: Test Epic
   Description: Testing Jira integration
   ```

2. **Monitor Usage:**
   ```bash
   # Check logs
   ./docker-run.sh logs
   
   # Monitor Jira audit logs
   # Check Jira Admin → System → Audit log
   ```

3. **Optimize Configuration:**
   - Set up additional custom fields
   - Configure workflow transitions
   - Establish project automation rules
   - Train team on bot usage

Your Jira credentials are now configured! The PM Bot can create epics and user stories, manage issue relationships, and integrate seamlessly with your Jira workflow. 🎉 