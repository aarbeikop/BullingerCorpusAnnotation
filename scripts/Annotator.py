import os
import re
from lxml import etree
from nltk.tokenize import PunktSentenceTokenizer
from argparse import ArgumentParser

# Assuming the following are correctly implemented and imported
from lang_id.identifier import LanguageIdentifier
from lang_id.charlm import CharLM
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
    return ''.join(parts)

def train_language_models(datadir, ngram_order=3, smoothing=0.1):
    identifier = LanguageIdentifier()
    for language_code in ['DE', 'LA']:
        filename = f'{language_code.lower()}.txt'
        training_data = os.path.join(datadir, filename)
        model = CharLM(ngram_order, smoothing)
        model.train(training_data)
        identifier.add_model(language_code, model)
    return identifier

# Assuming lang_id data directory path is provided as an argument
def get_global_identifier(args):
    return train_language_models(args.lang_data_dir)

def language_detection(text, identifier):
    if not text:
        return 'unk'
    return identifier.identify(text).lower()

def tokenize_and_preserve_structure(text_chunks, entity_tagger, identifier):
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
                    detected_language = language_detection(tagged_sentence, identifier)
                    if i == 0:
                        current_sentence += tagged_sentence
                    else:
                        if current_sentence:
                            sent_tagged.append(f'<s n="{sentence_num}" xml:lang="{detected_language}">{current_sentence}</s>\n\t\t\t\t')
                            sentence_num += 1
                        current_sentence = tagged_sentence

    if current_sentence:
        detected_language = language_detection(current_sentence, identifier)
        sent_tagged.append(f'<s n="{sentence_num}" xml:lang="{detected_language}">{current_sentence}</s>\n\t\t\t\t')
    return ''.join(sent_tagged)

def process_paragraphs(doc, entity_tagger, identifier):
    for paragraph in doc.xpath('//div/p'):
        text_chunks = preserve_lb_tags(paragraph)
        sentences_str = tokenize_and_preserve_structure(text_chunks, entity_tagger, identifier)
        reconstruct_paragraph(sentences_str, paragraph)

def reconstruct_paragraph(sentences_str, original_paragraph):
    original_paragraph.clear()
    new_content = etree.fromstring(f'<p>{sentences_str}</p>', etree.XMLParser(recover=True))
    for child in new_content:
        original_paragraph.append(child)

def process_directory(input_dir, output_dir, entity_tagger, identifier):
    for filename in os.listdir(input_dir):
        if filename.endswith('.xml'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            doc = etree.parse(input_file)
            process_paragraphs(doc, entity_tagger, identifier)
            doc.write(output_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            print(f'Processed and saved {filename}')

def main():
    parser = ArgumentParser(description="Process XML files for NLP annotation.")
    parser.add_argument("--input_dir", type=str, help="Directory containing input XML files")
    parser.add_argument("--output_dir", type=str, help="Directory to save annotated XML files")
    parser.add_argument("--lang_data_dir", type=str, help="Directory containing language model data")
    args = parser.parse_args()

    identifier = get_global_identifier(args)
    entity_tagger = EntityTagger("entities")

    process_directory(args.input_dir, args.output_dir, entity_tagger, identifier)

if __name__ == "__main__":
    main()