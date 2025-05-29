# Slack Bot Credentials Setup Guide 💬

This guide will walk you through creating a Slack bot and generating the required credentials for the PM Bot. The bot will integrate with your Slack workspace to provide conversational project management capabilities.

## Prerequisites 📋

- Slack workspace with admin permissions (or ability to install apps)
- Access to Slack API website
- Basic understanding of OAuth and app permissions

## Overview 🗺️

The PM Bot needs Slack credentials to:
- **💬 Receive Messages**: Handle direct messages and mentions
- **🤖 Send Responses**: Reply with epic creation results and status updates
- **⚡ Handle Commands**: Process slash commands like `/create-epic`
- **🔄 Enable Interactions**: Support buttons, modals, and interactive elements

## Required Tokens 🔑

You'll need to obtain three tokens:

| Token | Purpose | Format | Example |
|-------|---------|--------|---------|
| **Bot User OAuth Token** | API access for the bot | `xoxb-...` | `xoxb-1234567890-1234567890-abcdefghijklmnop` |
| **Signing Secret** | Verify requests from Slack | 32 hex chars | `1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d` |
| **App-Level Token** | Socket Mode connection | `xapp-...` | `xapp-1-A01234567-1234567890-abcdef` |

## Step 1: Create a Slack App

### 1. Navigate to Slack API:
- Go to https://api.slack.com/apps
- Sign in with your Slack account

### 2. Create New App:
- Click **"Create New App"**
- Select **"From scratch"**
- Fill in app details:
  ```
  App Name: PM Bot
  Pick a workspace: Your target workspace
  ```
- Click **"Create App"**

## Step 2: Configure Basic Information

### 1. Navigate to Basic Information:
- In the left sidebar, click **"Basic Information"**

### 2. Get Signing Secret:
- Scroll down to **"App Credentials"**
- Find **"Signing Secret"**
- Click **"Show"** and copy the value
- **This is your `SLACK_SIGNING_SECRET`** ✅

### 3. Add App Description (Optional):
```
Short Description: AI-powered project management assistant
Long Description: PM Bot helps agile teams create epics, user stories, and process meeting notes using AI. It integrates with Jira, Confluence, and Google Meet to streamline project management workflows.
```

### 4. Add App Icon (Optional):
- Upload a 512x512 icon for your bot
- Use a relevant project management or robot icon

## Step 3: Enable Socket Mode

### 1. Navigate to Socket Mode:
- In the left sidebar, click **"Socket Mode"**

### 2. Enable Socket Mode:
- Toggle **"Enable Socket Mode"** to **ON**
- You'll be prompted to create an App-Level Token

### 3. Create App-Level Token:
- Click **"Create"** when prompted
- Enter token details:
  ```
  Token Name: pm-bot-connection
  Scope: connections:write
  ```
- Click **"Generate"**
- **Copy the token (starts with `xapp-`)**
- **This is your `SLACK_APP_TOKEN`** ✅

## Step 4: Configure OAuth & Permissions

### 1. Navigate to OAuth & Permissions:
- In the left sidebar, click **"OAuth & Permissions"**

### 2. Add Bot Token Scopes:
Click **"Add an OAuth Scope"** under **"Bot Token Scopes"** and add these:

#### Required Scopes:
```
app_mentions:read     - Detect when bot is mentioned
channels:read         - Read channel information
chat:write           - Send messages to channels and DMs
commands             - Receive slash command invocations
files:read           - Read files shared in channels
im:history           - Read direct message history
im:read              - Read direct message info
im:write             - Send direct messages
users:read           - Read user information
```

#### Optional Scopes (for enhanced features):
```
channels:history     - Read channel message history
groups:read          - Read private channel info
groups:history       - Read private channel history
reactions:read       - Read message reactions
reactions:write      - Add message reactions
```

### 3. Install App to Workspace:
- Scroll up to **"OAuth Tokens for Your Workspace"**
- Click **"Install to Workspace"**
- Review permissions and click **"Allow"**

### 4. Get Bot User OAuth Token:
- After installation, copy the **"Bot User OAuth Token"**
- **This is your `SLACK_BOT_TOKEN`** ✅

## Step 5: Create Slash Commands

### 1. Navigate to Slash Commands:
- In the left sidebar, click **"Slash Commands"**

### 2. Create Commands:
Click **"Create New Command"** for each command:

#### Command 1: Create Epic
```
Command: /create-epic
Request URL: (leave blank for Socket Mode)
Short Description: Create a new epic with user stories
Usage Hint: Title: Epic title
            Description: Epic description
            Features: feature1, feature2 (optional)
            Priority: High/Medium/Low (optional)
```

#### Command 2: Process Meetings
```
Command: /process-meetings
Request URL: (leave blank for Socket Mode)
Short Description: Process meeting notes to Confluence
Usage Hint: space=SPACE_KEY
```

#### Command 3: Search Meetings
```
Command: /search-meetings
Request URL: (leave blank for Socket Mode)
Short Description: Search and process specific meetings
Usage Hint: keyword [space=SPACE_KEY] [days=30]
```

### 3. Save Commands:
- Click **"Save"** for each command

## Step 6: Configure Event Subscriptions

### 1. Navigate to Event Subscriptions:
- In the left sidebar, click **"Event Subscriptions"**

### 2. Enable Events:
- Toggle **"Enable Events"** to **ON**

### 3. Subscribe to Bot Events:
Click **"Add Bot User Event"** and add these events:

```
app_mention          - When bot is mentioned in channels
message.im           - Direct messages to the bot
```

### 4. Save Changes:
- Click **"Save Changes"**

## Step 7: Configure App Home (Optional)

### 1. Navigate to App Home:
- In the left sidebar, click **"App Home"**

### 2. Configure Home Tab:
- Enable **"Home Tab"**
- Add welcome message:
```
Welcome to PM Bot! 🤖

I can help you with:
• Creating epics and user stories
• Processing meeting notes
• Managing project documentation

Type 'help' to get started!
```

### 3. Enable Messages Tab:
- Check **"Allow users to send Slash commands and messages from the messages tab"**

## Step 8: Configure Environment Variables

Add these credentials to your `.env` file:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token-here
SLACK_SIGNING_SECRET=your-actual-signing-secret-here
SLACK_APP_TOKEN=xapp-your-actual-app-token-here
```

### Example with Real Values:
```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-1234567890-1234567890-abcdefghijklmnopqrstuvwx
SLACK_SIGNING_SECRET=1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d1e2f3a4b
SLACK_APP_TOKEN=xapp-1-A01234567-1234567890-abcdefghijklmnopqrstuvwx
```

## Step 9: Test Your Configuration

### 1. Create Test Script:
```python
# test_slack_auth.py
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Load from environment
BOT_TOKEN = "your-bot-token"
SIGNING_SECRET = "your-signing-secret"
APP_TOKEN = "your-app-token"

def test_slack_connection():
    """Test Slack bot connection"""
    try:
        # Initialize the app
        app = App(
            token=BOT_TOKEN,
            signing_secret=SIGNING_SECRET
        )
        
        # Test API connection
        response = app.client.auth_test()
        print(f"✅ Connected to Slack as: {response['user']}")
        print(f"📍 Team: {response['team']}")
        print(f"🆔 User ID: {response['user_id']}")
        
        # Test Socket Mode
        handler = SocketModeHandler(app, APP_TOKEN)
        print("✅ Socket Mode handler created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_permissions():
    """Test bot permissions"""
    try:
        app = App(token=BOT_TOKEN, signing_secret=SIGNING_SECRET)
        
        # Test getting bot info
        bot_info = app.client.auth_test()
        bot_id = bot_info['user_id']
        
        print(f"✅ Bot permissions verified")
        print(f"🤖 Bot ID: {bot_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Slack credentials...\n")
    
    conn_ok = test_slack_connection()
    perm_ok = test_permissions() if conn_ok else False
    
    print(f"\n{'='*50}")
    print("📊 Test Results Summary:")
    print(f"🔐 Connection: {'✅ Success' if conn_ok else '❌ Failed'}")
    print(f"🔑 Permissions: {'✅ Success' if perm_ok else '❌ Failed'}")
    
    if conn_ok and perm_ok:
        print("\n🎉 All tests passed! Your Slack credentials are working correctly.")
        print("You can now start the PM Bot!")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
```

### 2. Run Test:
```bash
# Using uv (recommended - much faster)
uv pip install slack-bolt

# Or using pip
pip install slack-bolt

python test_slack_auth.py
```

### Expected Output:
```
🔍 Testing Slack credentials...

✅ Connected to Slack as: pm-bot
📍 Team: Your Team Name
🆔 User ID: U01234567
✅ Socket Mode handler created successfully
✅ Bot permissions verified
🤖 Bot ID: U01234567

==================================================
📊 Test Results Summary:
🔐 Connection: ✅ Success
🔑 Permissions: ✅ Success

🎉 All tests passed! Your Slack credentials are working correctly.
You can now start the PM Bot!
```

## Step 10: Install and Test Bot

### 1. Add Bot to Channels:
- In Slack, go to a channel
- Type `/invite @PM Bot` (or your bot name)
- Or send a direct message to the bot

### 2. Test Basic Functionality:
```
# Direct message to bot
Hi PM Bot!

# Mention in channel
@PM Bot help

# Slash command
/create-epic
```

### 3. Expected Bot Response:
The bot should respond with:
```
👋 What can I do for you?

I can help you with:
1️⃣ Create Epic - Create a new epic with user stories in Jira
2️⃣ Process Meetings - Process recent meeting notes to Confluence
3️⃣ Search Meetings - Find and process specific meetings
4️⃣ Help - Get detailed information about my capabilities

Just type the number or name of what you'd like to do!
```

## Advanced Configuration ⚙️

### Multi-Workspace Installation:

1. **Enable Public Distribution:**
   - Go to **"Manage Distribution"**
   - Check **"Remove Hard Coded Information"**
   - Add privacy policy and support information

2. **Configure OAuth Redirect URLs:**
   - Add appropriate redirect URLs for OAuth flow
   - Configure for multiple workspaces

### Custom App Manifest:

You can use this app manifest for quick setup:

```yaml
display_information:
  name: PM Bot
  description: AI-powered project management assistant
  background_color: "#2c3e50"
features:
  bot_user:
    display_name: PM Bot
    always_online: true
  slash_commands:
    - command: /create-epic
      description: Create a new epic with user stories
      usage_hint: Title: Epic title, Description: Epic description
    - command: /process-meetings
      description: Process meeting notes to Confluence
      usage_hint: space=SPACE_KEY
    - command: /search-meetings
      description: Search and process specific meetings
      usage_hint: keyword [space=SPACE_KEY] [days=30]
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:read
      - chat:write
      - commands
      - files:read
      - im:history
      - im:read
      - im:write
      - users:read
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  socket_mode_enabled: true
```

## Troubleshooting 🔧

### Common Issues:

1. **"Invalid Token" Error:**
   ```bash
   # Check token format
   echo $SLACK_BOT_TOKEN | cut -c1-10
   # Should show: xoxb-12345
   
   echo $SLACK_APP_TOKEN | cut -c1-10
   # Should show: xapp-1-A01
   ```

2. **"Missing Scopes" Error:**
   - Go to **"OAuth & Permissions"**
   - Verify all required scopes are added
   - Reinstall app after adding scopes

3. **"Socket Mode Connection Failed":**
   - Verify Socket Mode is enabled
   - Check App-Level Token has `connections:write` scope
   - Ensure token starts with `xapp-`

4. **Commands Not Working:**
   - Verify slash commands are created
   - Check command names match exactly
   - Ensure Event Subscriptions are enabled

### Debug Commands:

```bash
# Test bot token
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  https://slack.com/api/auth.test

# Test app token (won't work with curl, but validates format)
echo $SLACK_APP_TOKEN | grep -E '^xapp-'

# Validate signing secret (32 hex characters)
echo $SLACK_SIGNING_SECRET | wc -c
# Should output: 33 (32 chars + newline)
```

## Security Best Practices 🔒

1. **Token Management:**
   - Store tokens in environment variables
   - Never commit tokens to version control
   - Rotate tokens regularly
   - Use workspace-specific tokens

2. **Scope Minimization:**
   - Only request necessary permissions
   - Regularly review and remove unused scopes
   - Use read-only scopes when possible

3. **Request Verification:**
   - Always verify requests using signing secret
   - Implement timestamp validation
   - Use HTTPS for all webhook endpoints

4. **Monitoring:**
   - Monitor API usage and rate limits
   - Set up alerts for unusual activity
   - Log security events

## Rate Limits 📊

### Slack API Limits:
- **Tier 1 Methods**: 1+ per minute
- **Tier 2 Methods**: 20+ per minute  
- **Tier 3 Methods**: 50+ per minute
- **Tier 4 Methods**: 100+ per minute

### Socket Mode Limits:
- **Connections**: 1 per app per workspace
- **Messages**: 30,000 per hour per workspace
- **Reconnections**: Automatic with exponential backoff

### Best Practices:
- Implement rate limit handling
- Use bulk operations where possible
- Cache responses when appropriate
- Monitor usage in app dashboard

## Bot Features 🚀

Once configured, your bot can:

1. **💬 Conversational Interface:**
   - Natural language interaction
   - Menu-driven conversations
   - Context-aware responses

2. **⚡ Slash Commands:**
   - `/create-epic` - Epic creation workflow
   - `/process-meetings` - Meeting notes processing
   - `/search-meetings` - Meeting search and analysis

3. **🤖 AI Integration:**
   - Epic generation from requirements
   - User story creation with acceptance criteria
   - Meeting notes processing and summarization

4. **🔗 External Integrations:**
   - Jira epic and story creation
   - Confluence page generation
   - Google Meet data processing

## Support Resources 📚

- **Slack API Documentation**: https://api.slack.com/
- **Slack Bolt Framework**: https://slack.dev/bolt-python/
- **Socket Mode Guide**: https://api.slack.com/apis/connections/socket
- **App Manifest Reference**: https://api.slack.com/reference/manifests
- **Slack Community**: https://slackcommunity.com/

## Next Steps ➡️

1. **Complete Setup:**
   ```bash
   # Update your .env file with the tokens
   # Start the PM Bot
   docker-compose up -d
   ```

2. **Test Integration:**
   ```bash
   # In Slack, test the bot
   @PM Bot help
   /create-epic
   ```

3. **Train Your Team:**
   - Share bot capabilities with team members
   - Create usage guidelines
   - Set up feedback channels

Your Slack bot is now ready! The PM Bot can interact with your team through natural conversations and slash commands, making project management more efficient and collaborative. 🎉 