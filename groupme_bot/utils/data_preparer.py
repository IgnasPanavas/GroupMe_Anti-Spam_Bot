"""
Data preparation utility for combining labeled CSV files into training datasets.
"""

import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataPreparer:
    """Prepares labeled data for model training."""
    
    def __init__(self, data_dir: str = "data/raw_messages"):
        self.data_dir = Path(data_dir)
    
    def find_labeled_csvs(self) -> List[Path]:
        """Find all CSV files that have been labeled (have non-empty label column)."""
        labeled_files = []
        
        for csv_file in self.data_dir.glob("*.csv"):
            if csv_file.name.endswith('.template.csv'):
                continue  # Skip template files
                
            try:
                df = pd.read_csv(csv_file)
                if 'label' in df.columns and df['label'].notna().any():
                    # Check if there are any non-empty labels
                    non_empty_labels = df[df['label'].str.strip() != '']
                    if len(non_empty_labels) > 0:
                        labeled_files.append(csv_file)
                        logger.info(f"Found labeled file: {csv_file.name} ({len(non_empty_labels)} labeled messages)")
            except Exception as e:
                logger.warning(f"Error reading {csv_file}: {e}")
        
        return labeled_files
    
    def combine_labeled_data(self, output_file: str = "data/training/combined_labeled_data.csv") -> str:
        """
        Combine all labeled CSV files into a single training dataset.
        
        Args:
            output_file: Path to save the combined dataset
            
        Returns:
            Path to the combined dataset
        """
        labeled_files = self.find_labeled_csvs()
        
        if not labeled_files:
            logger.warning("No labeled CSV files found!")
            return None
        
        # Read and combine all labeled files
        combined_data = []
        
        for csv_file in labeled_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Add source information (optional, for tracking)
                df['source_file'] = csv_file.name
                df['source_group'] = csv_file.stem.split('_')[0]  # Extract group name from filename
                
                # Filter to only labeled messages
                labeled_df = df[df['label'].str.strip() != ''].copy()
                
                if len(labeled_df) > 0:
                    combined_data.append(labeled_df)
                    logger.info(f"Added {len(labeled_df)} labeled messages from {csv_file.name}")
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
        
        if not combined_data:
            logger.error("No labeled data found in any files!")
            return None
        
        # Combine all dataframes
        combined_df = pd.concat(combined_data, ignore_index=True)
        
        # Clean up the data
        combined_df = self._clean_combined_data(combined_df)
        
        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(output_path, index=False)
        
        logger.info(f"Combined {len(combined_df)} labeled messages into {output_path}")
        
        # Print summary
        self._print_summary(combined_df)
        
        return str(output_path)
    
    def _clean_combined_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the combined dataset."""
        # Remove duplicates based on message_id
        df = df.drop_duplicates(subset=['message_id'], keep='first')
        
        # Standardize label values
        df['label'] = df['label'].str.lower().str.strip()
        
        # Replace common variations
        label_mapping = {
            'spam': 'spam',
            'ham': 'regular',
            'regular': 'regular',
            'normal': 'regular',
            'good': 'regular',
            'legitimate': 'regular',
            'questionable': 'questionable',
            'unsure': 'questionable'
        }
        
        df['label'] = df['label'].map(lambda x: label_mapping.get(x, x))
        
        # Remove rows with invalid labels
        valid_labels = ['spam', 'regular', 'ham', 'questionable']
        df = df[df['label'].isin(valid_labels)]
        
        # Ensure required columns exist
        required_columns = ['text', 'label']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return pd.DataFrame()
        
        # Remove rows with empty text
        df = df[df['text'].str.strip() != '']
        
        return df
    
    def _print_summary(self, df: pd.DataFrame):
        """Print a summary of the combined dataset."""
        print("\n" + "="*50)
        print("DATASET SUMMARY")
        print("="*50)
        print(f"Total messages: {len(df)}")
        print(f"Label distribution:")
        print(df['label'].value_counts())
        
        if 'source_group' in df.columns:
            print(f"\nMessages per group:")
            print(df['source_group'].value_counts().head(10))
        
        print(f"\nSample messages:")
        for label in df['label'].unique():
            sample = df[df['label'] == label].head(2)
            print(f"\n{label.upper()} examples:")
            for _, row in sample.iterrows():
                print(f"  - {row['text'][:100]}...")
        
        print("="*50)
    
    def create_training_splits(self, combined_file: str, test_size: float = 0.2, 
                              random_state: int = 42) -> Dict[str, str]:
        """
        Create training and testing splits from the combined dataset.
        
        Args:
            combined_file: Path to the combined labeled dataset
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with paths to training and testing files
        """
        try:
            df = pd.read_csv(combined_file)
            
            # Separate spam and regular messages for stratified split
            spam_df = df[df['label'] == 'spam']
            regular_df = df[df['label'] == 'regular']
            
            # Create splits
            from sklearn.model_selection import train_test_split
            
            spam_train, spam_test = train_test_split(
                spam_df, test_size=test_size, random_state=random_state
            )
            regular_train, regular_test = train_test_split(
                regular_df, test_size=test_size, random_state=random_state
            )
            
            # Combine splits
            train_df = pd.concat([spam_train, regular_train], ignore_index=True)
            test_df = pd.concat([spam_test, regular_test], ignore_index=True)
            
            # Save splits
            base_path = Path(combined_file).parent
            train_path = base_path / "train_data.csv"
            test_path = base_path / "test_data.csv"
            
            train_df.to_csv(train_path, index=False)
            test_df.to_csv(test_path, index=False)
            
            logger.info(f"Created training split: {train_path} ({len(train_df)} messages)")
            logger.info(f"Created testing split: {test_path} ({len(test_df)} messages)")
            
            return {
                'train': str(train_path),
                'test': str(test_path),
                'train_spam': len(spam_train),
                'train_regular': len(regular_train),
                'test_spam': len(spam_test),
                'test_regular': len(regular_test)
            }
            
        except Exception as e:
            logger.error(f"Error creating training splits: {e}")
            return {}
    
    def validate_labels(self, csv_file: str) -> Dict[str, Any]:
        """
        Validate the labels in a CSV file.
        
        Args:
            csv_file: Path to the CSV file to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            df = pd.read_csv(csv_file)
            
            results = {
                'total_messages': len(df),
                'labeled_messages': len(df[df['label'].str.strip() != '']),
                'unlabeled_messages': len(df[df['label'].str.strip() == '']),
                'label_distribution': df['label'].value_counts().to_dict(),
                'empty_text': len(df[df['text'].str.strip() == '']),
                'duplicates': len(df) - len(df.drop_duplicates(subset=['message_id']))
            }
            
            print(f"\nValidation results for {csv_file}:")
            print(f"  Total messages: {results['total_messages']}")
            print(f"  Labeled messages: {results['labeled_messages']}")
            print(f"  Unlabeled messages: {results['unlabeled_messages']}")
            print(f"  Empty text messages: {results['empty_text']}")
            print(f"  Duplicate message IDs: {results['duplicates']}")
            print(f"  Label distribution: {results['label_distribution']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating {csv_file}: {e}")
            return {}


def main():
    """Command-line interface for data preparation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GroupMe Data Preparer')
    parser.add_argument('--combine', action='store_true', help='Combine all labeled CSV files')
    parser.add_argument('--output', default='data/training/combined_labeled_data.csv', help='Output file for combined data')
    parser.add_argument('--create-splits', action='store_true', help='Create training/testing splits')
    parser.add_argument('--validate', help='Validate labels in a specific CSV file')
    parser.add_argument('--data-dir', default='data/raw_messages', help='Directory containing CSV files')
    
    args = parser.parse_args()
    
    preparer = DataPreparer(args.data_dir)
    
    if args.validate:
        preparer.validate_labels(args.validate)
    
    elif args.combine:
        output_file = preparer.combine_labeled_data(args.output)
        if output_file and args.create_splits:
            preparer.create_training_splits(output_file)
    
    elif args.create_splits:
        if os.path.exists(args.output):
            preparer.create_training_splits(args.output)
        else:
            print(f"Combined data file not found: {args.output}")
            print("Run with --combine first to create the combined dataset.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
