import os
from collections import defaultdict
import string
import Levenshtein as lev
import re

class EntityTagger:
    def __init__(self, entity_directory):
        self.entity_directory = entity_directory
        self.entity_dicts = self.build_entity_dictionaries()  # No need to pass self.entity_directory

    def build_entity_dictionaries(self):
        entity_counts = defaultdict(lambda: {'persons': 0, 'places': 0})  # Track counts of entities in each category
        entity_dicts = defaultdict(lambda: defaultdict(dict))

        for entity_type in ['persons', 'places']:
            try:
                with open(os.path.join(self.entity_directory, f'extracted_{entity_type}.txt'), 'r', encoding='utf-8') as file:
                    for line in file:
                        parts = line.strip().rsplit(', ', 1)
                        entity = parts[0].strip(string.punctuation + string.whitespace)  # Normalize the entity
                        entity_id = parts[1] if len(parts) == 2 else ""
                        ngram_length = len(entity.split())
                        
                        # Ensure that single-word entities are stored under key '1'
                        if ngram_length == 1:
                            entity_dicts[entity_type][1][entity] = entity_id
                        else:
                            entity_dicts[entity_type][ngram_length][entity] = entity_id
                        
                        # Update the entity counts
                        entity_counts[entity][entity_type] += 1
            except FileNotFoundError:
                print(f"File for {entity_type} not found in {self.entity_directory}.")

        # Resolve conflicts where the same entity is categorized under both persons and places
        for entity, counts in entity_counts.items():
            # Determine if entity exists in both categories
            if counts['persons'] > 0 and counts['places'] > 0:
                # Choose the category where the entity appears most frequently
                dominant_category = 'persons' if counts['persons'] > counts['places'] else 'places'
                other_category = 'places' if dominant_category == 'persons' else 'persons'
                
                # Iterate through all n-gram lengths for the non-dominant category and remove the entity
                for ngram_length in entity_dicts[other_category]:
                    if entity in entity_dicts[other_category][ngram_length]:
                        del entity_dicts[other_category][ngram_length][entity]

        # Convert defaultdicts to regular dictionaries for output
        return {entity_type: {n: dict(v) for n, v in length_dicts.items()} for entity_type, length_dicts in entity_dicts.items()}

    def clean_text(self, text):
        # Remove standard XML-like tags.
        text_no_tags = re.sub(r'<[^>]+>', '', text)
        
        # Remove malformed tags and their remnants. This assumes 'xmlidp' followed by digits and/or letters
        # is always an artifact you want to remove.
        text_no_tags = re.sub(r'xmlidp[\d\w]+', '', text_no_tags)
        
        # Remove sequences that could be remnants of tags or other unwanted artifacts. Adjust this pattern
        # to fit the kinds of remnants you observe in your data.
        text_no_tags = re.sub(r'\b[a-zA-Z]{2,10}\d+\b', '', text_no_tags)
        
        # Optionally, remove punctuation from the cleaned text. Be careful if entities might include punctuation.
        text_no_tags_and_punct = ''.join(ch for ch in text_no_tags if ch not in string.punctuation)
        
        return text_no_tags_and_punct



    def is_proper_noun(self, word):
        return word[0].isupper() if word else False

    def bio_tag(self, text):
        text_list = text.split()
        out_string = ''
        skip_until = -1
        is_first_word = True  # Flag for the first word in the text.

        for pos in range(len(text_list)):
            if pos < skip_until:
                continue

            found = False
            n_ranges = range(max(max(self.entity_dicts['persons'].keys(), default=0), 
                                max(self.entity_dicts['places'].keys(), default=0)), 0, -1)
            for n in n_ranges:
                if pos + n > len(text_list):
                    continue

                ngram_original = ' '.join(text_list[pos:pos + n])  # Original text segment
                ngram_temp = ngram_original  # Temporary ngram_original for processing
                # Extract <lb> tags and replace them with placeholders for processing.  # Replace <lb> tags with space
                cleaned_ngram = self.clean_text(ngram_temp)  # Clean the temporary ngram_original for entity recognition.

                if is_first_word:
                    is_first_word = False  # Update flag after processing the first word
                    continue

                if not self.is_proper_noun(cleaned_ngram):
                    continue  

                persons_unigram = self.entity_dicts['persons'].get(1, {}).get(cleaned_ngram)
                places_unigram = self.entity_dicts['places'].get(1, {}).get(cleaned_ngram)
                if persons_unigram:
                    out_string += f'<personName ref="{persons_unigram}">{ngram_original}</personName> '
                    skip_until = pos + n
                    found = True
                    break
                elif places_unigram:
                    out_string += f'<placeName ref="{places_unigram}">{ngram_original}</placeName> '
                    skip_until = pos + n
                    found = True
                    break
                
                
                if n == 1:  # Skip Levenshtein distance for unigrams
                    # If no exact match is found, try to find a close match using Levenshtein distance
                    exact_match = persons_unigram or places_unigram  # Check for an exact match
                    if not exact_match:
                        # First look for an exact match in the other category
                        other_category = 'persons' if persons_unigram else 'places'
                        other_unigram = self.entity_dicts[other_category].get(1, {}).get(cleaned_ngram)
                        if other_unigram:
                            tag_name = 'personName' if other_category == 'persons' else 'placeName'
                            punctuation = ngram_temp[-1] if ngram_temp[-1] in string.punctuation else ''
                            if ngram_temp[-1] in string.punctuation:
                                out_string += f'<{tag_name} ref="{other_unigram}">{ngram_original[:-1]}</{tag_name}>{punctuation} '
                            else:   
                                out_string += f'<{tag_name} ref="{other_unigram}">{ngram_original}</{tag_name}> '
                            skip_until = pos + n
                            found = True
                            break
                        else:
                            # If no exact match is found in either category, try Levenshtein distance
                            closest_entity = None
                            closest_distance = float('inf')
                            closest_category = None  # Track the category of the closest entity
                            for category in ['persons', 'places']:
                                for entity, entity_id in self.entity_dicts[category].get(n, {}).items():
                                    distance = lev.distance(cleaned_ngram.lower(), entity.lower())  # Convert to lowercase for case insensitivity
                                    if distance <= 2 and distance < closest_distance and len(cleaned_ngram) >= 4:
                                        closest_entity = (entity, entity_id, category)
                                        print(closest_entity)
                                        closest_distance = distance
                                        closest_category = category

                            if closest_entity:
                                entity, entity_id, category = closest_entity
                                tag_name = 'personName' if category == 'persons' else 'placeName'
                                punctuation = ngram_temp[-1] if ngram_temp[-1] in string.punctuation else ''
                                if ngram_temp[-1] in string.punctuation:
                                    out_string += f'<{tag_name} ref="{entity_id}">{ngram_original[:-1]}</{tag_name}>{punctuation} ' if entity_id else f'<{tag_name}>{ngram_original[:-1]}</{tag_name}>{punctuation} '
                                else:
                                    out_string += f'<{tag_name} ref="{entity_id}">{ngram_original}</{tag_name}> ' if entity_id else f'<{tag_name}>{ngram_original}</{tag_name}> '
                                skip_until = pos + n
                                found = True
                                break


                closest_entity = None
                closest_distance = float('inf')
                closest_category = None  # Track the category of the closest entity
                for category in ['persons', 'places']:
                    for entity, entity_id in self.entity_dicts[category].get(n, {}).items():
                        distance = lev.distance(cleaned_ngram.lower(), entity)
                        if distance <= 2 and distance < closest_distance:
                            closest_entity = (entity, entity_id, category)
                            closest_distance = distance
                            closest_category = category

                if closest_entity:
                    entity, entity_id, category = closest_entity
                    tag_name = 'personName' if category == 'persons' else 'placeName'
                    punctuation = ngram_temp[-1] if ngram_temp[-1] in string.punctuation else ''
                    if ngram_temp[-1] in string.punctuation:
                        out_string += f'<{tag_name} ref="{entity_id}">{ngram_original[:-1]}</{tag_name}>{punctuation} ' if entity_id else f'<{tag_name}>{ngram_original[:-1]}</{tag_name}>{punctuation} '
                    else:
                        out_string += f'<{tag_name} ref="{entity_id}">{ngram_original}</{tag_name}> ' if entity_id else f'<{tag_name}>{ngram_original}</{tag_name}> '
                    skip_until = pos + n
                    found = True
                    break  

            if not found and pos >= skip_until:
                out_string += ngram_original + ' '  # Use ngram_original to keep <lb> tags

        return out_string.strip() 


def main():
    entity_tagger = EntityTagger('entities')  
    texts = [
        'This letter was sent by Joannes Piscatorius last week.',
        'This letter was sent by Piscatorius last week.',
        'This letter was sent by Joannes Piscatorius, who came last week.',
        'This letter was sent by Johannes Piscatorio last week.',
        'This letter was sent by Ioannes Piscatorius last week.',
        'This letter was sent by Ioanne Pistorio from Rome last week.',
        'This letter was sent by Heinrich Bullinger from Rome last week.',
        'This letter was sent by Heinrich Bullinger from Zürich last week.',
        'This letter was sent by Heinrich Bullinger from Frankfurt last week.',
        'This letter was sent by Heinrycho Bullingero from Zurich last week, and he mentioned Joannes Piscatorius.',
        'Ioannes Piscatorius was mentioned in a letter sent by Heinrich Bullinger from Zurich last week.',
        'Ioannis was in Rome last week',
        'Excellentissimo viro d. Heinrycho <lb xml:id="p2z2"/> Bullingero, Tigurinae <lb xml:id="p2z3"/>ecclesiae antistiti fidelissimo, domino<lb xml:id="p2z4"/>ecclesiae Baptistori suo fidelissimum domino<lb xml:id="p2z5"/>zuͦ Heinrych Byl zuͦ<lb xml:id="p2z6"/>zuͦ Zürich in yl zuͦ<lb xml:id="p2z7"/>per zu hinrych<lb xml:id="p2z8"/>',
        'Excellentissimo viro d. Heinrycho Bullingero, Tigurinae ecclesiae antistiti fidelissimo, domino ecclesiae Baptistori suo fidelissimum domino zuͦ Heinrych Byl zuͦ zuͦ Zürich in yl zuͦ per zu hinrych'
        ]

    for text in texts:
        print('Input:', text)
        output = entity_tagger.bio_tag(text)
        print('Output:', output, '\n')

if __name__ == "__main__":
    main()
