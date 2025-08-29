# Automatic Spam Detector Guide

## Overview
The `auto_spam_detector.py` script automatically detects and labels spam messages in raw message CSV files based on patterns learned from existing spam data.

## Features
- **Pattern-based detection**: Uses regex patterns to identify common spam indicators
- **Keyword density analysis**: Analyzes the frequency of spam-related words
- **Contact information detection**: Identifies phone numbers and email addresses
- **Scoring system**: Uses a weighted scoring system to determine if a message is spam
- **Batch processing**: Can process multiple CSV files at once

## Usage

### Basic Usage
```bash
python auto_spam_detector.py
```
This will process all CSV files in the `data/raw_messages/` directory.

### Processing a Single File
```python
from auto_spam_detector import SpamDetector

detector = SpamDetector()
detector.detect_spam_in_file("path/to/your/file.csv")
```

### Processing a Directory
```python
detector = SpamDetector()
detector.detect_spam_in_directory("path/to/directory/")
```

## Spam Detection Patterns

The detector looks for the following patterns:

### Ticket Sales
- "selling concert ticket"
- "looking to sell game ticket"
- "giving away concert ticket"
- "passing concert ticket"

### Parking Permits
- "selling parking permit text"
- "buy permit text interested"
- "parking permit text interested"

### Electronics & Items
- "selling macbook free"
- "giving away ps5 free"
- "selling car perfect condition"

### Contact Patterns
- "text if interested" + phone number
- "dm interested" + phone number
- "contact if interested" + phone number

### Suspicious Offers
- "giving away free macbook"
- "free ps5 perfect condition"
- "free ticket"

### Urgency Indicators
- "first come first serve dm"
- "dm now interested"
- "text now interested"

## Scoring System

The detector uses a weighted scoring system:

- **Pattern matches**: 3 points each
- **High keyword density (>30%)**: 10 points
- **Phone number presence**: 5 points
- **Email presence**: 3 points

**Threshold**: Messages with a score of 8 or higher are labeled as spam.

## Output

The script will:
1. Process each CSV file
2. Label detected spam messages
3. Save updated files
4. Display summary statistics

## Example Output
```
Processing: data/raw_messages/example.csv
  Detected spam: Selling my concert tickets text if interested...
✅ Relabeled 3 messages as spam in data/raw_messages/example.csv
📊 Label distribution:
  ham: 150 messages
  spam: 3 messages
```

## Customization

You can customize the detection by:
1. Modifying the `spam_patterns` list in the `load_spam_patterns` method
2. Adjusting the scoring weights in the `is_spam` method
3. Changing the threshold score (currently 8)

## Files Created

- **`data/consolidated_spam_simplified.csv`**: Simplified spam reference file with only text and label columns
- **Updated CSV files**: Original files with spam labels added

## Notes

- The script skips files that already have spam labels
- It uses the consolidated spam data as a reference for patterns
- The detection is conservative to avoid false positives
- You can review and manually adjust labels after automatic detection
