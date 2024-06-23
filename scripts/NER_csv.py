import os
import csv
import re
from lxml import etree
from NERTagger import EntityTagger  # Make sure this import is correct based on your environment

class SentenceExtractor:
    def __init__(self, entity_directory, input_directory, exclude_directory):
        self.entity_tagger = EntityTagger(entity_directory)
        self.input_directory = input_directory
        self.exclude_directory = exclude_directory
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def extract_sentences(self, output_file):
        excluded_files = set(os.listdir(self.exclude_directory))

        with open(output_file, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Sentence', 'Label', 'Sentence Number', 'Filename'])

            for filename in os.listdir(self.input_directory):
                if filename.endswith('.xml') and filename not in excluded_files:
                    file_path = os.path.join(self.input_directory, filename)
                    tree = etree.parse(file_path)

                    for sentence in tree.xpath('//tei:s[not(ancestor::tei:note) and not(child::tei:note)]', namespaces=self.namespaces):
                        sentence_num = sentence.get('n')
                        sentence_str = etree.tostring(sentence, encoding='unicode', method='xml')
                        cleaned_sentence_str = re.sub(r'<\/?s[^>]*>', '', sentence_str).strip()
                        cleaned_sentence_str = re.sub(r'<lb[^>]*\/>', '', cleaned_sentence_str).strip()

                        if not ('<persName type="auto_name"' in cleaned_sentence_str or '<placeName type="auto_name"' in cleaned_sentence_str):
                            if '<persName' in cleaned_sentence_str:
                                label = 'contains_person'
                            elif '<placeName' in cleaned_sentence_str:
                                label = 'contains_place'
                            else:
                                label = 'no_entity'

                            writer.writerow([cleaned_sentence_str, label, sentence_num, filename])

    def add_tagged_sentences_to_csv(self, input_csv, output_csv):
        data_rows = []
        with open(input_csv, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                # Excluding sentences containing auto_name types in original Sentence
                if '<personName type="auto_name"' not in row['Sentence'] and '<placeName type="auto_name"' not in row['Sentence']:
                    data_rows.append(row)

        with open(output_csv, mode='w', encoding='utf-8', newline='') as outfile:
            fieldnames = reader.fieldnames + ['Tagged Sentence', 'My Tagger Entity']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data_rows:
                original_sentence = row['Sentence']
                # Assuming bio_tag correctly tags the sentence, it should be:
                tagged_sentence = self.entity_tagger.bio_tag(original_sentence)
                row['Tagged Sentence'] = tagged_sentence  # Store the tagged sentence
                
                # Checking if the tagged sentence contains person or place names.
                # Ensure these checks correctly identify whether tags are present.
                if '<persName' in tagged_sentence:
                    row['My Tagger Entity'] = 'contains_person'
                elif '<placeName' in tagged_sentence:
                    row['My Tagger Entity'] = 'contains_place'
                else:
                    row['My Tagger Entity'] = 'no_entity'

                writer.writerow(row)  # Write the modified row to the CSV


entity_directory = 'entities'

 # this to get all the previously annotated letters to be reprocessed with the new tagger
input_directory = '/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/calir-bullingerproject/gold_standard'
extractor = SentenceExtractor(entity_directory, input_directory, exclude_directory="/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/calir-bullingerproject/<lb_files_corrected")
output_file = 'extracted_sentences-ACCURACY.csv'  # Change as needed
extractor.extract_sentences(output_file)
input_csv = 'extracted_sentences-ACCURACY.csv'  # Change as needed
output_csv = 'extracted_sentences-ACCURACY.csv'  # Change as needed
extractor.add_tagged_sentences_to_csv(input_csv, output_csv)
