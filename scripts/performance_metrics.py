import os
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
csv_file_path = '/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/calir-bullingerproject/output_filtered_accuracy.csv'
directory_to_check = '/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/calir-bullingerproject/lb_files_auto'
mismatch_output_file = 'error-clean.csv'  # File to write mismatches
column1 = 'Label'
column2 = 'My Tagger Entity'
filename_column = 'Filename'
sentence_column = 'Sentence'
tagged_sentence_column = 'Tagged Sentence'

# Initialize dictionaries and global counters
file_accuracies = {}
global_counters = {'total_checked': 0, 'matches': 0, 'false_positives': 0, 'false_negatives': 0}
mismatches = []

# Function to normalize and check if sentences match
def sentences_match(sent1, sent2):
    norm1 = sent1.strip().lower()
    norm2 = sent2.strip().lower()
    return norm1 == norm2

try:
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Group DataFrame by Filename
    grouped_df = df.groupby(filename_column)

    # Iterate through each file in the DataFrame
    for filename, group in grouped_df:
        file_counters = {'total_checked': 0, 'matches': 0, 'false_positives': 0, 'false_negatives': 0}
        
        for _, row in group.iterrows():
            # Exclude rows where auto_name tags are present
            if '<persName type="auto_name">' not in row[sentence_column] and '<placeName type="auto_name">' not in row[tagged_sentence_column]:
                file_counters['total_checked'] += 1
                global_counters['total_checked'] += 1

                if row[column1] == row[column2]:
                    if sentences_match(row[sentence_column], row[tagged_sentence_column]):
                        file_counters['matches'] += 1
                        global_counters['matches'] += 1
                    else:
                        file_counters['false_positives'] += 1
                        global_counters['false_positives'] += 1
                        mismatches.append({'filename': filename, 'sentence': row[sentence_column], 'tagged_sentence': row[tagged_sentence_column], 'type': 'False Positive'})
                else:
                    file_counters['false_negatives'] += 1
                    global_counters['false_negatives'] += 1
                    mismatches.append({'filename': filename, 'sentence': row[sentence_column], 'tagged_sentence': row[tagged_sentence_column], 'type': 'False Negative'})

        # Calculate metrics for each file
        if file_counters['total_checked'] > 0:
            precision = file_counters['matches'] / (file_counters['matches'] + file_counters['false_positives'])
            recall = file_counters['matches'] / (file_counters['matches'] + file_counters['false_negatives'])
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            file_accuracies[filename] = {'accuracy': (file_counters['matches'] / file_counters['total_checked']) * 100, 'precision': precision, 'recall': recall, 'f1_score': f1_score}

    # Output mismatches to CSV
    pd.DataFrame(mismatches).to_csv(mismatch_output_file, index=False)

    # Print global metrics
    global_precision = (global_counters['matches'] / (global_counters['matches'] + global_counters['false_positives'])) * 100
    global_recall = (global_counters['matches'] / (global_counters['matches'] + global_counters['false_negatives'])) * 100
    global_f1_score = (2 * (global_precision * global_recall) / (global_precision + global_recall)) if (global_precision + global_recall) > 0 else 0
    global_accuracy = (global_counters['matches'] / global_counters['total_checked']) * 100

    print(f"Global Precision: {global_precision:.3f}, Global Recall: {global_recall:.3f}, Global F1-Score: {global_f1_score:.3f}, Global Accuracy: {global_accuracy:.3f}%")

except Exception as e:
    print(f"An error occurred: {e}")