import os
import re
import string
from collections import defaultdict
import Levenshtein as lev
import csv

class EntityTagger:
    def __init__(self, entity_directory):
        self.entity_directory = entity_directory
        self.entity_dicts = self.build_entity_dictionaries()

    def build_entity_dictionaries(self):
        entity_counts = defaultdict(lambda: {'persons': 0, 'places': 0})
        entity_dicts = defaultdict(lambda: defaultdict(dict))

        # Latin variations based on common endings
        endings_map = {
            'am': ['ae', 'arum', 'is', 'as'], 
            'ae': ['arum', 'is', 'as'], 
            'as': ['arum', 'is'],
            'os': ['i', 'orum', 'is', 'a', 'e', 'o'], 
            'um': ['i', 'orum', 'is', 'a', 'e', 'o'], 
            'is': ['ium', 'ibus', 'es'],
            'o': ['i', 'um', 'o'],
            'e': ['i', 'um', 'e'],
            'i': ['orum', 'is', 'a', 'e', 'o'],
            'orum': ['is', 'a', 'e', 'o'],
            'ibus': ['es'],
            'es': ['ium', 'ibus'],
            'ium': ['ibus', 'es'],
        }

        for entity_type in ['persons', 'places']:
            try:
                with open(os.path.join(self.entity_directory, f'extracted_{entity_type}.txt'), 'r', encoding='utf-8') as file:
                    for line in file:
                        parts = line.strip().rsplit(', ', 1)
                        entity_raw = parts[0].strip(string.punctuation + string.whitespace)
                        if not entity_raw:  # Skip empty or invalid lines
                            continue

                        entity_parts = entity_raw.split()
                        if not entity_parts:  # If entity_parts is empty, skip this iteration
                            continue
                        
                        entity_id = parts[1] if len(parts) == 2 else ""
                        ngram_length = len(entity_parts)

                        # Ensure original form is included before variations
                        entity_dicts[entity_type][ngram_length][entity_raw] = entity_id
                        entity_counts[entity_raw][entity_type] += 1

                        # Process every word for Latin variations
                        for i, part in enumerate(entity_parts):
                            for end, variations in endings_map.items():
                                if part.endswith(end):
                                    for variation in variations:
                                        new_part = part[:-len(end)] + variation
                                        new_entity_parts = entity_parts[:i] + [new_part] + entity_parts[i + 1:]
                                        new_entity = ' '.join(new_entity_parts).strip()
                                        # Add new variation to dictionary
                                        entity_dicts[entity_type][ngram_length][new_entity] = entity_id

            except FileNotFoundError:
                print(f"File for {entity_type} not found in {self.entity_directory}.")

        # Resolve conflicts between 'persons' and 'places'
        for entity, counts in entity_counts.items():
            if counts['persons'] > 0 and counts['places'] > 0:
                dominant_category = 'persons' if counts['persons'] > counts['places'] else 'places'
                other_category = 'places' if dominant_category == 'persons' else 'persons'
                for ngram_length in entity_dicts[other_category]:
                    if entity in entity_dicts[other_category][ngram_length]:
                        del entity_dicts[other_category][ngram_length][entity]

        # Convert nested defaultdicts to regular dicts for return
        return {entity_type: {n: dict(v) for n, v in length_dicts.items()} for entity_type, length_dicts in entity_dicts.items()}

    def _clean_text(self, text):
        text_list = text.split()
        #text_list[0] = text_list[0].lower()
        return ' '.join(word.strip(string.punctuation) for word in text_list)

    def _is_proper_noun(self, word):
        return word[0].isupper() if word else False

    def bio_tag(self, text):
        # Split the text into a list of words for n-gram matching
        text_list = text.split()
        out_string = ''
        # Initialize the skip_until variable to -1 to indicate that no words should be skipped
        skip_until = -1

        for pos in range(len(text_list)):
            if pos < skip_until:
                continue
            # Initialize the found variable to False to indicate that no n-gram has been found
            found = False
            n_ranges = range(max(max(self.entity_dicts['persons'].keys(), default=0), 
                                max(self.entity_dicts['places'].keys(), default=0)), 0, -1)
            for n in n_ranges:
                if pos + n > len(text_list):
                    continue
                # Create the n-gram from the current position
                ngram = ' '.join(text_list[pos:pos + n])
                cleaned_ngram = self._clean_text(ngram)

                persons_unigram = self.entity_dicts['persons'].get(1, {}).get(cleaned_ngram)
                places_unigram = self.entity_dicts['places'].get(1, {}).get(cleaned_ngram)

                # Initialize the closest_entity variable to None to indicate that no closest entity has been found and entity_id to None
                closest_entity = None
                entity_id = None
                closest_distance = float('inf')

                # If the n-gram is not a proper noun, skip it
                if not self._is_proper_noun(cleaned_ngram):
                    continue  
                
                # check unigrams for exact match, the n-gram should be at least 4 characters long
                if n == 1 and len(cleaned_ngram) >= 4:
                    exact_match = persons_unigram or places_unigram
                    if not exact_match:
                        other_category = 'persons' if persons_unigram else 'places'
                        other_unigram = self.entity_dicts[other_category].get(1, {}).get(cleaned_ngram)
                        if other_unigram:
                            tag_name = 'personName' if other_category == 'persons' else 'placeName'
                            punctuation = ngram[-1] if ngram[-1] in string.punctuation else ''
                            if ngram[-1] in string.punctuation:
                                out_string += f'<{tag_name} ref="{other_unigram}">{ngram[:-1]}</{tag_name}>{punctuation} '
                            else:   
                                out_string += f'<{tag_name} ref="{other_unigram}">{ngram}</{tag_name}> '
                            skip_until = pos + n
                            found = True
                            break
                        else:
                            for category in ['persons', 'places']:
                                for entity, entity_id in self.entity_dicts[category].get(n, {}).items():
                                    distance = lev.distance(cleaned_ngram.lower(), entity.lower())
                                    # if the n-gram is more than 5 characters, we want to match with a distance of 3 or less, this is a safe threshold
                                    if len(cleaned_ngram) > 5:
                                        if distance <= 1 and distance < closest_distance:
                                            closest_entity = (entity, entity_id, category)
                                            closest_distance = distance
                                            closest_category = category
                                    # if the n-gram is less than 5 characters, we only want to match exact strings, this avoids false positives
                                    elif len(cleaned_ngram) <= 4:
                                        if distance <= 0 and distance < closest_distance:
                                            closest_entity = (entity, entity_id, category)
                                            #print(closest_entity, "this is the closest entity for unigrams with 4 or less characters") SANITY CHECK
                                            closest_distance = distance
                                            closest_category = category

                else:
                    for category in ['persons', 'places']:
                        for entity, entity_id in self.entity_dicts[category].get(n, {}).items():
                            distance = lev.distance(cleaned_ngram.lower(), entity)
                            if len(cleaned_ngram.split()[0]) <= 3:
                                continue
                            elif distance <= 3 and distance < closest_distance:
                                closest_entity = (entity, entity_id, category)
                                closest_distance = distance
                                closest_category = category

                if closest_entity:
                    entity, entity_id, category = closest_entity
                    tag_name = 'personName' if category == 'persons' else 'placeName'
                    punctuation = ngram[-1] if ngram[-1] in string.punctuation else ''
                    if ngram[-1] in string.punctuation:
                        out_string += f'<{tag_name} ref="{entity_id}">{ngram[:-1]}</{tag_name}>{punctuation} ' if entity_id else f'<{tag_name}>{ngram[:-1]}</{tag_name}>{punctuation} '
                    else:
                        out_string += f'<{tag_name} ref="{entity_id}">{ngram}</{tag_name}> ' if entity_id else f'<{tag_name}>{ngram}</{tag_name}> '
                    skip_until = pos + n
                    found = True
                    break  

            if not found and pos >= skip_until:
                out_string += ngram + ' '

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
        #'Excellentissimo viro d. Heinrycho <lb xml:id="p2z2"/>Bullingero, Tigurinae <lb xml:id="p2z3"/>ecclesiae antistiti fidelissimo, domino<lb xml:id="p2z4"/>ecclesiae Baptistori suo fidelissimum domino<lb xml:id="p2z5"/>zuͦ Heinrych Byl zuͦ<lb xml:id="p2z6"/>zuͦ Zürich in yl zuͦ<lb xml:id="p2z7"/>per zu hinrych<lb xml:id="p2z8"/>',
        'Excellentissimo viro d. Heinrycho Bullingero, Tigurinae ecclesiae antistiti fidelissimo, domino ecclesiae Baptistori suo fidelissimum domino zuͦ Heinrych Byl zuͦ zuͦ Zürich in yl zuͦ per zu hinrych',
        'I, saw Iesu Christi last week.',
        'I, saw Iesu Christo last week in Rome.',
        'Darum er ich, Heinrich Bullinger, zuͦ Zürich in yl zuͦ per zu hinrych',
        'Argentina is a beautiful place.',
        'Deus est amor.',
        'Te dominus reges Tigurinum Zvinglio, non multum',
        'Concilii nullam audimus fieri mentionem; disiecit sine dubio dominus iterum mirabiliter multa hostium consilia per mortem regis.',
        'Amen.',
        'Nostra adhuc sunt in incertum, sed speramus meliora.',
        ]

    for text in texts:
        print('Input:', text)
        output = entity_tagger.bio_tag(text)
        print('Output:', output, '\n')
    
    input_csv = 'extracted_sentences-wTags.csv'
    output_csv = 'extracted_sentences-wTags.csv'

    #entity_tagger.add_tagged_sentences_to_csv(input_csv, output_csv)

if __name__ == "__main__":
    main()
