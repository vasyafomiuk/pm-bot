# Azure OpenAI Credentials Setup Guide 🤖

This guide will walk you through setting up Azure OpenAI credentials for the PM Bot. Azure OpenAI provides enterprise-grade AI services with enhanced security, compliance, and data residency controls.

## Prerequisites 📋

- Azure subscription (with OpenAI access approved)
- Azure portal access
- Administrator permissions to create resources

## Step 1: Request Azure OpenAI Access

1. **Apply for Access:**
   - Azure OpenAI requires approval for access
   - Go to: https://aka.ms/oai/access
   - Fill out the application form
   - Wait for approval (can take several days)

2. **Check Access Status:**
   - Log into Azure portal
   - Search for "Azure OpenAI" in the search bar
   - If you see the service, you have access

## Step 2: Create Azure OpenAI Resource

1. **Navigate to Azure Portal:**
   - Go to https://portal.azure.com/
   - Sign in with your Azure account

2. **Create New Resource:**
   - Click **"+ Create a resource"**
   - Search for **"Azure OpenAI"**
   - Click **"Create"**

3. **Configure Resource:**
   ```
   Subscription: Your Azure subscription
   Resource Group: Create new or use existing (e.g., "pm-bot-rg")
   Region: Choose a region (e.g., East US, West Europe)
   Name: Your resource name (e.g., "pm-bot-openai")
   Pricing Tier: Standard S0
   ```

4. **Review and Create:**
   - Click **"Review + create"**
   - Click **"Create"**
   - Wait for deployment to complete

## Step 3: Deploy AI Models

1. **Access Azure OpenAI Studio:**
   - Go to your created resource
   - Click **"Go to Azure OpenAI Studio"**
   - Or visit: https://oai.azure.com/

2. **Navigate to Deployments:**
   - In Azure OpenAI Studio, click **"Deployments"**
   - Click **"+ Create new deployment"**

3. **Deploy GPT-4 Model:**
   ```
   Model: gpt-4 (or gpt-4-32k if available)
   Deployment name: gpt-4-deployment
   Version: Latest available
   Scale type: Standard
   Tokens per minute rate limit: 10K (adjust as needed)
   Content filter: Default
   ```

4. **Deploy Additional Models (Optional):**
   - **GPT-3.5-turbo** for faster, cheaper operations
   - **text-embedding-ada-002** for embeddings
   - Follow same process with different model names

## Step 4: Get Credentials

1. **Get Endpoint URL:**
   - In Azure OpenAI Studio, go to **"Chat"** playground
   - Click **"View code"**
   - Copy the **"Endpoint"** URL
   - Format: `https://your-resource.openai.azure.com/`

2. **Get API Key:**
   - In Azure portal, go to your OpenAI resource
   - Click **"Keys and Endpoint"** (left sidebar)
   - Copy **"KEY 1"** or **"KEY 2"**

3. **Get API Version:**
   - Latest stable version: `2024-02-15-preview`
   - Check Azure OpenAI docs for updates

4. **Get Deployment Name:**
   - Use the deployment name you created (e.g., "gpt-4-deployment")

## Step 5: Configure Environment Variables

Add these variables to your `.env` file:

```env
# Azure OpenAI Configuration
USE_AZURE_OPENAI=true
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4-deployment
```

## Step 6: Test Your Setup

1. **Create Test Script:**
   ```python
   # test_azure_openai.py
   import openai
   from openai import AzureOpenAI
   
   client = AzureOpenAI(
       api_key="your-api-key-here",
       api_version="2024-02-15-preview",
       azure_endpoint="https://your-resource.openai.azure.com/"
   )
   
   try:
       response = client.chat.completions.create(
           model="gpt-4-deployment",  # Your deployment name
           messages=[{"role": "user", "content": "Hello, Azure OpenAI!"}],
           max_tokens=50
       )
       print("✅ Azure OpenAI is working!")
       print(f"Response: {response.choices[0].message.content}")
   except Exception as e:
       print(f"❌ Error: {e}")
   ```

2. **Run Test:**
   ```bash
   # Using uv (recommended - much faster)
   uv pip install openai
   
   # Or using pip
   pip install openai
   
   python test_azure_openai.py
   ```

## Available Models 🤖

| Model | Best For | Context Window | Cost |
|-------|----------|----------------|------|
| **gpt-4** | Complex reasoning, high quality | 8K tokens | Higher |
| **gpt-4-32k** | Long documents, large context | 32K tokens | Highest |
| **gpt-35-turbo** | Fast responses, general tasks | 4K tokens | Lower |
| **gpt-35-turbo-16k** | Medium documents | 16K tokens | Medium |

## Regional Availability 🌍

Azure OpenAI is available in these regions:
- **East US** ✅ Recommended
- **South Central US** ✅ Recommended  
- **West Europe** ✅ Recommended
- **France Central**
- **UK South**
- **Australia East**
- **Canada East**
- **Japan East**

## Pricing Information 💰

### GPT-4 Pricing (per 1K tokens):
- **Input**: $0.03
- **Output**: $0.06

### GPT-3.5-turbo Pricing (per 1K tokens):
- **Input**: $0.0015
- **Output**: $0.002

### Cost Optimization Tips:
1. Use GPT-3.5-turbo for simpler tasks
2. Set appropriate token limits
3. Monitor usage in Azure portal
4. Use prompt engineering to reduce tokens

## Security Best Practices 🔒

1. **Network Security:**
   - Configure virtual networks
   - Use private endpoints
   - Set up IP restrictions

2. **Access Control:**
   - Use Azure RBAC
   - Rotate keys regularly
   - Use managed identities when possible

3. **Data Protection:**
   - Enable audit logging
   - Configure data retention policies
   - Use customer-managed keys

## Troubleshooting 🔧

### Common Issues:

1. **"Access Denied" Error:**
   - Verify Azure OpenAI access is approved
   - Check resource permissions
   - Ensure correct subscription

2. **"Model Not Found" Error:**
   - Verify deployment name matches exactly
   - Check model is deployed and active
   - Ensure model is available in your region

3. **"Rate Limit Exceeded" Error:**
   - Increase tokens per minute limit
   - Implement retry logic
   - Monitor usage patterns

4. **"Invalid API Key" Error:**
   - Regenerate API keys in Azure portal
   - Check key is copied correctly
   - Verify endpoint URL format

### Useful Azure CLI Commands:

```bash
# List Azure OpenAI resources
az cognitiveservices account list --query "[?kind=='OpenAI']"

# Get resource keys
az cognitiveservices account keys list --name your-resource-name --resource-group your-rg

# Check deployment status
az cognitiveservices account deployment list --name your-resource-name --resource-group your-rg
```

## Monitoring and Management 📊

1. **Azure Portal Monitoring:**
   - View usage metrics
   - Set up alerts
   - Monitor costs

2. **Azure OpenAI Studio:**
   - Test models in playground
   - Manage deployments
   - View quotas and limits

3. **Logging:**
   - Enable diagnostic logging
   - Monitor API calls
   - Track usage patterns

## Migration from OpenAI

If migrating from OpenAI to Azure OpenAI:

1. **Update Client Code:**
   ```python
   # Old OpenAI
   import openai
   openai.api_key = "sk-..."
   
   # New Azure OpenAI
   from openai import AzureOpenAI
   client = AzureOpenAI(...)
   ```

2. **Environment Variables:**
   ```env
   # Change from:
   USE_AZURE_OPENAI=false
   OPENAI_API_KEY=sk-...
   
   # To:
   USE_AZURE_OPENAI=true
   AZURE_OPENAI_ENDPOINT=https://...
   AZURE_OPENAI_API_KEY=...
   ```

## Support Resources 📚

- **Azure OpenAI Documentation**: https://docs.microsoft.com/azure/cognitive-services/openai/
- **Azure OpenAI Studio**: https://oai.azure.com/
- **Pricing Calculator**: https://azure.microsoft.com/pricing/calculator/
- **Status Page**: https://status.openai.com/
- **Support**: Azure portal support tickets

## Next Steps ➡️

1. **Configure PM Bot:**
   - Update your `.env` file with Azure OpenAI credentials
   - Restart the bot: `docker-compose restart pm-bot`

2. **Test Integration:**
   - Try creating an epic: `/create-epic`
   - Monitor logs for any issues

3. **Optimize Usage:**
   - Monitor token consumption
   - Adjust model selection based on needs
   - Set up usage alerts

Your Azure OpenAI integration is now ready! The PM Bot will use Azure's enterprise-grade AI services for generating epics and user stories. 🎉 