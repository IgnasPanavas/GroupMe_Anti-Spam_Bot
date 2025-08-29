# Data Collection Guide

This guide explains how to collect and prepare training data for the GroupMe Anti-Spam Bot.

## 🎯 **Workflow Overview**

1. **Collect messages** from multiple groups
2. **Label the messages** as spam/regular
3. **Combine labeled data** into training dataset
4. **Create training splits** for model training
5. **Train the model** with your custom data

## 📊 **Step 1: Collect Messages**

### List Available Groups
```bash
python -m groupme_bot.cli data --list-groups
```

### Collect from Single Group
```bash
python -m groupme_bot.cli data --collect-from 109638241 --limit 500
```

### Collect from Multiple Groups
```bash
python -m groupme_bot.cli data --collect-from 109638241 35563498 24832372 --limit 1000
```

**Output:** CSV files in `data/raw_messages/` with names like:
- `Anti-spam-bot-test-group_20250828_181645.csv`
- `Student_Financial_Planning_Association_20250828_181650.csv`

## 🏷️ **Step 2: Label Messages**

### Option A: Manual Labeling (Recommended)

1. **Open the CSV file** in Excel, Google Sheets, or any spreadsheet editor
2. **Change labels** in the `label` column:
   - Messages are pre-labeled as `ham` (non-spam)
   - Change to `spam` for unwanted, promotional, or inappropriate messages
   - Keep as `ham` for normal conversation messages
   - Use `questionable` for messages you're unsure about (optional)

### Option B: Create Labeling Template
```bash
python -m groupme_bot.cli data --create-template data/raw_messages/your_file.csv
```

### Labeling Guidelines

**Examples of SPAM:**
- "Selling tickets", "Buy now", "Click here"
- "Free money", "Make money fast"
- Promotional messages, scams
- Unwanted solicitations

**Examples of REGULAR:**
- "Hey everyone", "What time is the meeting?"
- "Thanks!", "Great idea"
- Normal conversation, questions, responses

## 🔄 **Step 3: Combine and Prepare Data**

### Combine All Labeled Files
```bash
python -m groupme_bot.cli data --combine
```

This will:
- Find all CSV files with labels
- Combine them into `data/training/combined_labeled_data.csv`
- Clean and standardize the data
- Show a summary of the dataset

### Create Training Splits
```bash
python -m groupme_bot.cli data --combine --create-splits
```

This creates:
- `data/training/train_data.csv` (80% of data)
- `data/training/test_data.csv` (20% of data)

## 🤖 **Step 4: Train Model**

```bash
python -m groupme_bot.cli train
```

The model will now use your custom labeled data!

## 📋 **File Structure**

```
data/
├── raw_messages/                    # Raw collected messages
│   ├── Group1_20250828_181645.csv
│   ├── Group2_20250828_181650.csv
│   └── ...
└── training/                       # Prepared training data
    ├── combined_labeled_data.csv   # All labeled messages combined
    ├── train_data.csv             # Training split
    ├── test_data.csv              # Testing split
    └── spam_detection_model.pkl   # Trained model
```

## 🔧 **Advanced Commands**

### Validate Labels
```bash
python -m groupme_bot.cli data --validate data/raw_messages/your_file.csv
```

### Collect with Attachments Info
```bash
python -m groupme_bot.cli data --collect-from 109638241 --limit 500 --save-attachments
```

### Custom Output Directory
```bash
python -m groupme_bot.cli data --collect-from 109638241 --output-dir my_data
```

## 💡 **Tips for Better Data**

1. **Diverse Sources**: Collect from different types of groups
2. **Balanced Labels**: Try to have similar numbers of spam and regular messages
3. **Quality Over Quantity**: 100 well-labeled messages > 1000 poorly-labeled ones
4. **Regular Updates**: Collect new data periodically to improve the model
5. **Edge Cases**: Include borderline cases to improve model robustness

## 🚨 **Important Notes**

- **No separate spam CSV needed**: All messages go in one file with a `label` column
- **Safe filenames**: Group names are automatically converted to safe filenames
- **No duplicates**: The system automatically removes duplicate messages
- **API limits**: Be respectful of GroupMe's API limits (built-in delays)
- **Backup your data**: Keep copies of your labeled CSV files

## 🔄 **Iterative Improvement**

1. Train model with initial data
2. Test on real groups
3. Collect more data from edge cases
4. Re-label and retrain
5. Repeat!

This iterative process will continuously improve your spam detection accuracy.
