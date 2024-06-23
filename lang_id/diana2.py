import os
import re
from lxml import etree
from nltk.tokenize import PunktSentenceTokenizer
from identifier import LanguageIdentifier, CharLM

def load_and_sort_names(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        names = [line.strip() for line in file.read().splitlines() if line.strip()]
    names.sort(key=len, reverse=True)
    return names


def mark_names_in_text(text, names, tag):
    def replacer(match):
        matched_text = match.group(0)
        start_pos, end_pos = match.span(0)

        prefix = text[max(0, start_pos - 1):start_pos]
        suffix = text[end_pos:min(len(text), end_pos + 1)]

        if prefix.isalnum() or suffix.isalnum():
            return matched_text

        pre_tag = text[max(0, start_pos - len(f"<{tag}>")):start_pos]
        post_tag = text[end_pos:end_pos + len(f"</{tag}>")]

        if pre_tag == f"<{tag}>" and post_tag == f"</{tag}>":
            return matched_text

        return f"<{tag}>{matched_text}</{tag}>"

    for name in names:
        if name:
            # check if the first character of the name is uppercase
            if name[0].isupper():
                escaped_name = re.escape(name)  # escape regex special characters in the name
                # construct pattern to match this name with an uppercase start
                pattern = re.compile(rf'\b{escaped_name}(?=\b|[A-Z][a-z])', flags=0)

                text = pattern.sub(replacer, text)

    return text

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

def train_language_models(datadir='/path/to/your/language/model/data', ngram_order=3, smoothing=0.1):
    identifier = LanguageIdentifier()
    for language_code in ['DE', 'LA']:
        filename = f'{language_code}.txt'
        training_data = os.path.join(datadir, filename)
        model = CharLM(ngram_order, smoothing)
        model.train(training_data)
        identifier.add_model(language_code, model)
    return identifier

global_language_identifier = train_language_models('/Users/diana/Documents/UZH /FS24/Annotation/calir-bullingerproject/lang_id/data')

def language_detection(text):
    if not text:
        return 'unk'
    return global_language_identifier.identify(text).lower()

def tokenize_and_preserve_structure(text_chunks, persons, places):
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
                current_sentence += part + "\t\t\t\t"
            else:
                sentences = tokenizer.tokenize(part)
                for i, sentence in enumerate(sentences):
                    detected_language = language_detection(sentence)
                    sentence = mark_names_in_text(sentence, persons, 'persName')
                    sentence = mark_names_in_text(sentence, places, 'placeName')
                    if i == 0:
                        current_sentence += sentence
                    else:
                        if current_sentence:
                            sent_tagged.append(f'<s n="{sentence_num}" xml:lang="{detected_language}">{current_sentence}</s>')
                            sentence_num += 1
                        current_sentence = sentence

    if current_sentence:
        detected_language = language_detection(current_sentence)
        current_sentence = mark_names_in_text(current_sentence, persons, 'persName')
        current_sentence = mark_names_in_text(current_sentence, places, 'placeName')
        sent_tagged.append(f'<s n="{sentence_num}" xml:lang="{detected_language}">{current_sentence}</s>')
    return ''.join(sent_tagged)


def process_paragraphs(doc, persons, places):
    for paragraph in doc.xpath('//div/p'):
        text_chunks = preserve_lb_tags(paragraph)
        sentences_str = tokenize_and_preserve_structure(text_chunks, persons, places)
        reconstruct_paragraph(sentences_str, paragraph)

def reconstruct_paragraph(sentences_str, original_paragraph):
    original_paragraph.clear()
    new_content = etree.fromstring(f'<p>{sentences_str}</p>', etree.XMLParser(recover=True))
    for child in new_content:
        original_paragraph.append(child)

def process_directory(input_dir, output_dir, persons, places):
    for filename in os.listdir(input_dir):
        if filename.endswith('.xml'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            doc = etree.parse(input_file)
            process_paragraphs(doc, persons, places)
            doc.write(output_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            print(f'Processed and saved {filename}')

# Load names
persons = load_and_sort_names('/Users/diana/Documents/UZH /FS24/Annotation/calir-bullingerproject/scripts/extracted_persons.txt')
places = load_and_sort_names('/Users/diana/Documents/UZH /FS24/Annotation/calir-bullingerproject/scripts/extracted_places.txt')


# Example usage: adjust 'input_dir' and 'output_dir' as needed
input_dir = '/Users/diana/Documents/UZH /FS24/Annotation/calir-bullingerproject/TEST'
output_dir = '/Users/diana/Documents/UZH /FS24/Annotation/calir-bullingerproject/TEST/OUTPUT'
process_directory(input_dir, output_dir, persons, places)