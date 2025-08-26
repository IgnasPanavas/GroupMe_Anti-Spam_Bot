# GroupMe Anti-Spam Bot

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

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd GroupMe_Anti-Spam_Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with:
   ```
   API_KEY=your_groupme_api_key
   BOT_USER_ID=your_bot_user_id
   ```

## 🚀 Quick Start

### 1. Collect Training Data
```bash
python collect_data.py
```

### 2. Train the Model
```bash
python train.py
```

### 3. Start the Bot
```bash
python main.py --group-id YOUR_GROUP_ID
```

## 📋 Usage

### Running the Bot

**Basic usage:**
```bash
python main.py --group-id 109638241
```

**With custom settings:**
```bash
python main.py --group-id 109638241 --confidence 0.8 --interval 30
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
python collect_data.py
```

### Clean Training Data
```bash
python clean_data.py
```

### Manual Data Analysis
```bash
python -m src.utils.clean_training_data --action analyze
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
   - Run `python train.py` to create the model

2. **"API key error"**
   - Check your `.env` file and API key validity

3. **"Permission denied"**
   - Ensure the bot user is an admin in the group

4. **"No messages detected"**
   - Check group ID and bot permissions

### Debug Mode

Enable debug output:
```bash
python -m src.utils.debug_commands
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
