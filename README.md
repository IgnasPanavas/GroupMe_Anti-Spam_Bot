# SpamShield

An intelligent anti-spam bot for GroupMe with ML-powered detection, chat commands, and comprehensive monitoring capabilities.

## 🚀 Features

- **ML-Powered Spam Detection** - Uses trained models to identify spam messages
- **Chat Commands** - Control the bot directly through GroupMe messages
- **Admin Controls** - Secure admin-only commands for bot management
- **Multi-Group Support** - Monitor multiple groups simultaneously
- **Configurable Settings** - Customize confidence thresholds, check intervals, and notifications
- **Data Management** - Automatic deduplication and data cleanup
- **Image Handling** - Proper handling of messages with attachments

## 📁 Project Structure

```
GroupMe_Anti-Spam_Bot/
├── src/                          # Source code
│   ├── bot/                      # Core bot functionality
│   │   ├── spam_monitor.py       # Main spam monitoring logic
│   │   ├── chat_commands.py      # Chat command processing
│   │   └── start_spam_monitor.py # Bot startup script
│   ├── ml/                       # Machine learning components
│   │   └── model_trainer.py      # Model training and prediction
│   ├── utils/                    # Utilities and helpers
│   │   ├── config_manager.py     # Configuration management
│   │   ├── groupme_api.py        # GroupMe API interactions
│   │   ├── clean_training_data.py # Data cleanup utilities
│   │   └── debug_commands.py     # Debugging tools
│   └── web/                      # Web dashboard (future)
├── data/                         # Data storage
│   ├── training/                 # Training data and models
│   ├── config/                   # Configuration files
│   └── logs/                     # Log files
├── tests/                        # Test files
├── docs/                         # Documentation
├── main.py                       # Main entry point
├── train.py                      # Model training script
├── collect_data.py               # Data collection script
├── clean_data.py                 # Data cleanup script
└── requirements.txt              # Python dependencies
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- GroupMe API key from https://dev.groupme.com/

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd GroupMe_Anti-Spam_Bot

# Run automated setup
./quick-start.sh
```

### Manual Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd GroupMe_Anti-Spam_Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your API key from https://dev.groupme.com/
   ```

## 🚀 Quick Start

### Get Your GroupMe API Key
1. Go to https://dev.groupme.com/
2. Sign in with your GroupMe account
3. Click "Create Application"
4. Copy the "Access Token" - this is your API_KEY

### Find Your Group ID
```bash
python -m groupme_bot.cli groups
```

### 1. Train the Model
```bash
python -m groupme_bot.cli train
```

### 2. Start the Bot
```bash
python -m groupme_bot.cli start --group-id YOUR_GROUP_ID
```

## 🌐 Frontend (Optional)

### Prerequisites
- Node.js 16+ and npm

### Setup Frontend
```bash
# Run the setup script
./setup-frontend.sh

# Or manually:
cd spamshield-frontend
npm install
```

### Start Frontend
```bash
# Terminal 1: Start API server
python api/prediction_server.py

# Terminal 2: Start React app
cd spamshield-frontend
npm start
```

### Access the Application
- **Frontend**: http://localhost:3000
- **API**: http://localhost:5001
- **Health Check**: http://localhost:5001/api/health

### Features
- 🧪 **Live Spam Detection** - Test messages with real-time AI predictions
- 📊 **Interactive Dashboard** - Monitor bot performance and statistics
- 📱 **Mobile Responsive** - Works perfectly on all devices
- 🎨 **Professional UI** - Modern design with Tailwind CSS

### 3. Collect Training Data (Optional)
```bash
python -m groupme_bot.cli collect --group-id YOUR_GROUP_ID --limit 100
```

## 📋 Usage

### Running the Bot

**Basic usage:**
```bash
python -m groupme_bot.cli start --group-id 109638241
```

**With custom settings:**
```bash
python -m groupme_bot.cli start --group-id 109638241 --confidence 0.8 --interval 30
```

**Using Makefile:**
```bash
make start GROUP_ID=109638241
```

### Chat Commands

Once the bot is running, use these commands in your GroupMe group:

- **`/spam-bot: help`** - Show all available commands
- **`/spam-bot: activate`** - Activate bot for current group *(Admin only)*
- **`/spam-bot: deactivate`** - Deactivate bot for current group *(Admin only)*
- **`/spam-bot: status`** - Show bot status for current group
- **`/spam-bot: settings`** - Show current settings *(Admin only)*
- **`/spam-bot: config`** - Configure bot behavior *(Admin only)*

### Configuration Commands

- **`/spam-bot: config removal on/off`** - Toggle removal notifications
- **`/spam-bot: config startup on/off`** - Toggle startup messages

## 🔧 Data Management

### Collect Training Data
```bash
python -m groupme_bot.cli collect --group-id YOUR_GROUP_ID --limit 100
```

### Train Model
```bash
python -m groupme_bot.cli train
```

### List Groups
```bash
python -m groupme_bot.cli groups
```

## ⚙️ Configuration

The bot uses a JSON configuration file (`data/config/bot_config.json`) with these settings:

```json
{
  "active_groups": [],
  "settings": {
    "confidence_threshold": 0.8,
    "check_interval": 30,
    "model_file": "data/training/spam_detection_model.pkl",
    "show_removal_messages": true,
    "show_startup_message": true
  }
}
```

## 🤖 How It Works

1. **Message Monitoring** - Bot continuously monitors group messages
2. **Spam Detection** - ML model analyzes message content for spam patterns
3. **Action Taking** - Spam messages are automatically removed
4. **Notifications** - Group is notified of removed spam (configurable)
5. **Command Processing** - Chat commands are processed and responded to

## 📊 ML Model

The bot uses a machine learning ensemble with:
- **TF-IDF Vectorization** - Text feature extraction
- **Multiple Algorithms** - Naive Bayes, Logistic Regression, Random Forest
- **Automatic Selection** - Best performing model is automatically chosen
- **Regular Retraining** - Model can be retrained with new data

## 🔒 Security

- **Admin-Only Commands** - Critical operations require admin privileges
- **API Key Protection** - Secure handling of GroupMe API credentials
- **Input Validation** - All commands and inputs are validated
- **Error Handling** - Graceful handling of API errors and failures

## 📝 Logging

The bot provides comprehensive logging:
- **Console Output** - Real-time status updates
- **Log Files** - Detailed logs in `data/logs/`
- **Error Tracking** - Automatic error reporting and handling

## 🐛 Troubleshooting

### Common Issues

1. **"Model file not found"**
   - Run `python -m groupme_bot.cli train` to create the model

2. **"API key error"**
   - Check your `.env` file and API key validity
   - Get your API key from https://dev.groupme.com/

3. **"Permission denied"**
   - Ensure the bot user is an admin in the group

4. **"No messages detected"**
   - Check group ID and bot permissions

5. **"Import errors"**
   - Run `pip install -e .` to install the package

### Debug Mode

Enable debug output:
```bash
python -m groupme_bot.cli start --group-id YOUR_GROUP_ID --dry-run
```

## ☁️ Deployment

### Local Development
```bash
# Quick setup
./quick-start.sh

# Manual setup
pip install -e .
python -m groupme_bot.cli start --group-id YOUR_GROUP_ID
```

### AWS EC2 Deployment
See [deploy/aws-ec2-guide.md](deploy/aws-ec2-guide.md) for detailed instructions.

**Quick EC2 setup:**
```bash
# On your EC2 instance
curl -sSL https://raw.githubusercontent.com/yourusername/GroupMe_Anti-Spam_Bot/main/deploy/ec2-setup.sh | bash
```

### Docker Deployment
```bash
# Build image
make docker-build

# Run container
make docker-run GROUP_ID=YOUR_GROUP_ID
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `data/logs/`
3. Open an issue on GitHub

---

**Note:** This bot is designed for educational and personal use. Please respect GroupMe's terms of service and use responsibly.
