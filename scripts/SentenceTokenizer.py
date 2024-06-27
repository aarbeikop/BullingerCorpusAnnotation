import os
import re
from lxml import etree
from nltk.tokenize import PunktSentenceTokenizer
from identifier import LanguageIdentifier
from charlm import CharLM
#from lang_id.predict import LanguageIdentifier
from scripts.NERTagger import EntityTagger

def preserve_lb_tags(paragraph):
    parts = []
    for elem in paragraph.iter():
        if elem.tag == 'lb':
            parts.append(etree.tostring(elem, encoding='unicode', with_tail=False))
        elif elem.text:
            parts.append(elem.text)
        if elem.tail:
            parts.append(elem.tail)
    return parts

def train_language_models(datadir='/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/bullingerproject/lang_id/data', ngram_order=3, smoothing=0.1):
    identifier = LanguageIdentifier()
    for language_code in ['DE', 'LA']:
        filename = f'{language_code.lower()}.txt'
        training_data = os.path.join(datadir, filename)
        model = CharLM(ngram_order, smoothing)
        model.train(training_data)
        identifier.add_model(language_code, model)
    return identifier

global_language_identifier = train_language_models('/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/bullingerproject/lang_id/data')

def language_detection(text):
    if not text:
        return 'unk'
    return global_language_identifier.identify(text).lower()

def tokenize_and_preserve_structure(text_chunks, entity_tagger):
    sent_tagged = []
    sentence_num = 1
    current_sentence = ''
    tokenizer = PunktSentenceTokenizer()

    for chunk in text_chunks:
        parts = re.split(r'(\n+)', chunk)
        for part in parts:
            if part.strip() == '<lb/>':
                current_sentence += part
            elif part == '\n':
                part = ""
                current_sentence += part
            else:
                sentences = tokenizer.tokenize(part)
                for i, sentence in enumerate(sentences):
                    if r'<lb.*/>' in sentence:
                        continue
                    sentence_temp = sentence.split()
                    tagged_sentence = entity_tagger.bio_tag(sentence)
                    detected_language = language_detection(tagged_sentence)
                    if i == 0:
                        current_sentence += tagged_sentence
                    else:
                        if current_sentence:
                            sent_tagged.append(f'<s n="{sentence_num}" xml:lang="{detected_language}">{current_sentence}</s>\n\t\t\t\t')
                            sentence_num += 1
                        current_sentence = tagged_sentence

    if current_sentence:
        detected_language = language_detection(current_sentence)
        sent_tagged.append(f'<s n="{sentence_num}" xml:lang="{detected_language}">{current_sentence}</s>\n\t\t\t\t')
    return ''.join(sent_tagged)

def process_paragraphs(doc):
    for paragraph in doc.xpath('//div/p'):
        text_chunks = preserve_lb_tags(paragraph)
        tagger = EntityTagger("entities")
        sentences_str = tokenize_and_preserve_structure(text_chunks, tagger)
        reconstruct_paragraph(sentences_str, paragraph)

def reconstruct_paragraph(sentences_str, original_paragraph):
    original_paragraph.clear()
    new_content = etree.fromstring(f'<p>{sentences_str}</p>', etree.XMLParser(recover=True))
    for child in new_content:
        original_paragraph.append(child)

def process_directory(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.xml'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            doc = etree.parse(input_file)
            process_paragraphs(doc)
            doc.write(output_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            print(f'Processed and saved {filename}')

input_dir = '/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/bullingerproject/new_directory_with_lb_files'
output_dir = '/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/bullingerproject/new_directory_with_correct_files_cleaned'
process_directory(input_dir, output_dir)
