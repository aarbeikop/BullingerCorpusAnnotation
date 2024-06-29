import re
from lxml import etree
import os
import glob
from nltk.tokenize import sent_tokenize
from langdetect import detect, LangDetectException
from cltk.sentence.lat import LatinPunktSentenceTokenizer
import nltk

nltk.download('punkt')

def language_detection(text):
    try:
        return "de" if detect(text) == "de" else "la"
    except LangDetectException:
        return "unk"
    
def tokenize_sentences(text, lang):
    if lang == "de":
        return sent_tokenize(text, language="german")
    elif lang == "la":
        tokenizer = LatinPunktSentenceTokenizer()
        return tokenizer.tokenize(text)
    else:
        return sent_tokenize(text)

def process_file(input_file, output_file):
    doc = etree.parse(input_file)
    parent = doc.xpath('//div/p')[0]  # Assuming all necessary paragraphs are direct children of <div>
    
    all = '<p>' + (parent.text if parent.text else '')  # Add parent text if exists
    i = 1

    for t in parent.xpath('.//lb'):
        lb_string = etree.tostring(t, encoding='unicode').strip()  # Convert lb element to string and add it to the content
        all += lb_string  # Add line break directly to all
        was_open = False  # Reset was_open for each new line

        if t.tail:
            lang = language_detection(t.tail)
            sentences = tokenize_sentences(t.tail, lang)
            for sentence in sentences:
                sentence = sentence.strip()  # Trim whitespace
                if not sentence:  # Skip empty sentences
                    continue
                
                # Check if sentence ends with a period or similar punctuation
                if sentence[-1] in ".!?":
                    all += f'<s n="{i}">{sentence[:-1]}</s>{sentence[-1]}'  # Separate ending punctuation
                else:
                    all += f'<s n="{i}">{sentence}</s>'
                i += 1  # Increment sentence number for each new sentence

        t.tail = None  # Clear tail text after processing

    all += '</p>'  # Close paragraph tag

    try:
        xfrag = etree.fromstring(all)  # Convert string to XML
        xfrag.tail = parent.tail
        parent.getparent().replace(parent, xfrag)  # Replace original paragraph content
    except etree.XMLSyntaxError as e:
        print(f"XML Syntax Error: {e}")
        print("Faulty XML content:", all)
        with open('faulty_xml_output.xml', 'w', encoding='utf-8') as f:
            f.write(all)
        raise  # Re-throw exception after logging

    # Write to output file
    with open(output_file, 'wb') as f:
        doc.write(f, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def main():
    input_files = glob.glob('TEST/*.xml')
    for input_file in input_files:
        output_file = input_file.replace('.xml', '_processed.xml')
        process_file(input_file, output_file)

if __name__ == "__main__":
    main()
