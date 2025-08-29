# Local Setup Guide

## Prerequisites
- Python 3.8+
- pip
- GroupMe API key

## Step 1: Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd GroupMe_Anti-Spam_Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Step 2: Configure Environment
```bash
# Copy example environment file
cp env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Required values in .env:**
- `API_KEY`: Your GroupMe API key from https://dev.groupme.com/
- `BOT_USER_ID`: Your bot's user ID (optional, but recommended)

## Step 3: Get Your GroupMe API Key
1. Go to https://dev.groupme.com/
2. Sign in with your GroupMe account
3. Click "Create Application"
4. Fill in the form (any name/description works)
5. Copy the "Access Token" - this is your API_KEY

## Step 4: Find Your Group ID
```bash
# List all your groups
python -m groupme_bot.cli groups
```

## Step 5: Test the Setup
```bash
# Train the model first
python -m groupme_bot.cli train

# Test data collection (optional)
python -m groupme_bot.cli collect --group-id YOUR_GROUP_ID --limit 10

# Start the bot
python -m groupme_bot.cli start --group-id YOUR_GROUP_ID
```

## Step 6: Run in Background (Optional)
```bash
# Using nohup (Linux/Mac)
nohup python -m groupme_bot.cli start --group-id YOUR_GROUP_ID > bot.log 2>&1 &

# Using screen (Linux/Mac)
screen -S bot
python -m groupme_bot.cli start --group-id YOUR_GROUP_ID
# Press Ctrl+A, then D to detach

# Using tmux (Linux/Mac)
tmux new-session -d -s bot 'python -m groupme_bot.cli start --group-id YOUR_GROUP_ID'
```

## Troubleshooting
- **Import errors**: Make sure you ran `pip install -e .`
- **API errors**: Check your API_KEY in .env
- **Permission errors**: Make sure you have admin rights in the GroupMe group
