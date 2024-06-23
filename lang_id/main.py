#!/usr/bin/env python3


"""
Command-line script for training and applying CharLM.

Waits for console input and prints the most likely language code
for each line entered.
"""


import os

from charlm import CharLM
from identifier import LanguageIdentifier


def main():
    """Run training and wait for input."""
    datadir = os.path.join(os.path.dirname(__file__), 'data')
    language_identifier = train(datadir)
    while True:
        print("\nType in a sentence in one of the following languages: {0}\n"
              .format(", ".join(language_identifier.get_languages())))
        print(language_identifier.identify(input()))


def train(datadir, ngram_order=3):
    """
    Train a character-level language model per language
    and add these to a language identificator.
    """
    identifier = LanguageIdentifier()
    for language_code in 'DE LA'.split():
        print("Training {0} language model...".format(language_code))
        filename = '{}.txt'.format(language_code.lower())
        training_data = os.path.join(datadir, filename)

        model = CharLM(ngram_order)
        model.train(training_data)
        identifier.add_model(language_code, model)
    return identifier


if __name__ == "__main__":
    main()
