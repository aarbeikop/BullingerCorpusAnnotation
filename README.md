# CALiR-BullingerProject

## Description

The Bullinger Project is a collaborative research platform dedicated to the annotation of historical document transcriptions, specificaally letters written to and from Heinrich Bullinger, a key figure in the Protestant Reformation. This project was completed in the context of a semester project for the FS24 semester course "Creation and Annotation of Linguistic Ressources".
## Methodology

The project employs methodology to annotate historical documents, consisting of the following steps:

### Sentence Boundary Marking

We employ the PunktSentenceTokenizer from the NLTK library to identify sentence boundaries accurately. The tokenizer is sophisticated enough to handle various punctuation marks and text formats, making it particularly effective for the structured text from our transcriptions. This approach ensures that each sentence is correctly segmented, paving the way for more detailed analysis. The methodology applied here also allows for the conservation of the original line breaks within the sentence. These are important as they hold information about the original format of the letters of the Bullinger Corpus.

### Language Tagging

Acknowledging the multilingual aspect of the Bullinger corpus, we implement a custom language detection system, which was provided to us. This system, built on character-level language models, distinguishes between languages (German and Latin). The models are trained with specific language data and integrated into our workflow to automate the language identification process, thereby enhancing the accuracy of our annotations. The language tagging is applied on a sentence level, which allows for high precision. However it much be noted that there is also inter-sentence code switching at times, and out experimental setup doesn't allow for this identification. 

### Named Entity Recognition and Linking

Our process extends to the identification and tagging of named entities within the texts. Utilizing a custom EntityTagger class, we extract and categorize entities into predefined groups (persons and places) by running the `NER_storage.py` on our annotated corpus. The tagger then leverages dictionaries compiled from the already annotated texts and utilizes the Levenshtein distance algorithm to identify and tag entities with high accuracy, even accounting for variances in spelling or phrasing. We use true-casing to minimise false positives at the beginning of sentences. 

## Implementation Details

The core of our project relies on Python scripts to process XML files containing the transcribed documents. These scripts perform tasks such as preserving line break tags, training language models, detecting languages, tokenizing texts while preserving their structure, and tagging entities accurately. The process respects the original document structure, ensuring that the annotations maintain textual integrity.

### Process Flow

1. **Preserve Line Breaks:** We convert line breaks in the documents into recognizable tags to maintain original formatting.
2. **Train Language Models:** Custom language models are trained using historical data to enhance the accuracy of language detection.
3. **Language Detection:** Texts are automatically scanned to determine the predominant language used in each segment.
4. **Tokenize and Preserve Structure:** Texts are segmented into sentences while retaining original structural elements like line breaks.
5. **Named Entity Recognition:** Entities are identified and tagged in the text, using a combination of rule-based and probabilistic approaches.

## How to run 

1. **To scrape and store tagged entities run the following command in your terminal**: 
```
    python NER_storage.py /path/to/input/directory extracted_persons.txt extracted_places.txt
```
2. **Optional** we also created a script to disambiguate certain entities, should they be in both entity dictionaries. To disambiguate run:
```
    python disambiguate_entities.py /path/to/directory
```
3. **Finally, to annotate, run:**
```
    python Annotator.py --input_dir [path/to/input] --output_dir [path/to/output] --lang_data_dir [path/to/language/model/data]
```


