# 🚀 Quick Start - Minimal Configuration

**Get your PM Bot running in 2 minutes with just the essential credentials!**

## ✅ Prerequisites Complete
- ✅ UV package manager installed and working
- ✅ All dependencies installed (88 packages)
- ✅ SSL certificates fixed
- ✅ Core AI agents initialized

## 🔑 Minimal Required Credentials

To get the bot running, you only need these **2 essential credentials**:

### 1. Slack Bot Credentials
```bash
# Copy the template
cp environment.template.txt .env

# Edit .env and add these required fields:
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token  # For socket mode
```

### 2. OpenAI API Key
```bash
# Add to your .env file:
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for cheaper usage
```

## 🚀 Run the Bot

```bash
# Activate the environment
source .venv/bin/activate

# Run with minimal validation (skips optional services)
python3 main.py --skip-validation
```

## 🎯 What Works With Minimal Setup

With just Slack + OpenAI credentials, your bot can:
- ✅ **Respond to Slack messages**
- ✅ **Generate epic features** using AI agents
- ✅ **Create user stories** with acceptance criteria
- ✅ **Process meeting notes** into structured documents
- ✅ **Conversational Q&A flow** ("What can I do for you?")

## 📋 Optional Services (Can Configure Later)

These are **optional** and the bot works fine without them:

| Service | Purpose | Required For |
|---------|---------|--------------|
| **Jira/Atlassian** | Create actual Jira tickets | Epic/story creation in Jira |
| **Google Meet** | Meeting transcript processing | Meeting notes from Google Meet |
| **Confluence** | Document creation | Publishing meeting notes |

## 🛠️ Troubleshooting

### Issue: "Service validation failed"
```bash
# Run with validation disabled
python3 main.py --skip-validation
```

### Issue: Still getting SSL errors
```bash
# Re-run certificate installer
/Applications/Python\ 3.10/Install\ Certificates.command
```

### Issue: Missing .env file
```bash
# Create from template
cp environment.template.txt .env
# Then edit .env with your credentials
```

## 🎉 Success Indicators

When running successfully, you should see:
```
INFO - 🤖 Project Management Bot Starting Up
INFO - Initialized OpenAI client
INFO - Successfully initialized AI agents
INFO - Bot is ready and listening for messages
```

## 🔗 Next Steps

1. **Test basic functionality** - Send a message to your bot
2. **Configure Jira** - See [instructions/jira_credentials.md](instructions/jira_credentials.md)
3. **Add Google integration** - See [instructions/google_credentials.md](instructions/google_credentials.md)
4. **Explore advanced features** - Epic creation, meeting notes processing

---

**Your PM Bot is ready to help with project management tasks!** 🤖⚡ 