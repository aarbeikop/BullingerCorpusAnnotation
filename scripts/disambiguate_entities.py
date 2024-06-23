import os
import argparse
from collections import defaultdict
import string

def write_entities_to_file(entity_dict, file_path):
    """Writes entities back to a file, preserving the original capitalization."""
    with open(file_path, 'w', encoding='utf-8') as file:
        for ngram_length, entities in sorted(entity_dict.items()):
            for entity, details in entities.items():
                entity_original, entity_id = details  # Unpack the original name and ID
                line = f"{entity_original}, {entity_id}\n" if entity_id else f"{entity_original}\n"
                file.write(line)

def check_files_for_double_occurrences(directory):
    """
    Disambiguates entities listed in both 'persons' and 'places' by assigning them to the category where they appear most frequently.
    The original capitalization of entities is preserved.
    Args:
    - directory: The directory path where the 'extracted_persons.txt' and 'extracted_places.txt' are stored.
    """
    entity_counts = defaultdict(lambda: {'persons': 0, 'places': 0})
    entity_dicts = {'persons': defaultdict(dict), 'places': defaultdict(dict)}

    for entity_type in ['persons', 'places']:
        file_path = os.path.join(directory, f'extracted_{entity_type}.txt')
        if not os.path.exists(file_path):
            print(f"File for {entity_type} not found in {directory}.")
            continue

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().rsplit(', ', 1)
                entity_original = parts[0].strip(string.punctuation + string.whitespace)
                entity_lower = entity_original.lower()  # Use lowercase for matching and counting
                entity_id = parts[1] if len(parts) == 2 else ""
                ngram_length = len(entity_original.split())
                
                entity_dicts[entity_type][ngram_length][entity_lower] = (entity_original, entity_id)  # Store both original and ID
                entity_counts[entity_lower][entity_type] += 1

    for entity_lower, counts in entity_counts.items():
        if counts['persons'] > 0 and counts['places'] > 0:
            dominant_category = 'persons' if counts['persons'] > counts['places'] else 'places'
            subdominant_category = 'places' if dominant_category == 'persons' else 'persons'
            
            for ngram_length in entity_dicts[subdominant_category]:
                if entity_lower in entity_dicts[subdominant_category][ngram_length]:
                    del entity_dicts[subdominant_category][ngram_length][entity_lower]

    # Write the updated dictionaries back to files
    for entity_type in ['persons', 'places']:
        file_path = os.path.join(directory, f'extracted_{entity_type}.txt')
        write_entities_to_file(entity_dicts[entity_type], file_path)

    return entity_dicts

def main():
    parser = argparse.ArgumentParser(description='Disambiguate entities in persons and places files.')
    parser.add_argument('directory', type=str, help='Directory containing the entity files.')
    args = parser.parse_args()

    updated_entity_dicts = check_files_for_double_occurrences(args.directory)
    print("Entity disambiguation complete.")

if __name__ == "__main__":
    main()
