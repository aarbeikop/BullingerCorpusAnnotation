#!/usr/bin/env python3
# coding: utf8
#
# PCL 2, FS 2018

import os
import sys

from charlm import CharLM
from identifier import LanguageIdentifier

def main():
	datadir = os.path.join(os.path.dirname(__file__), 'data')
	language_identifier = train(datadir, 3, 0.1)
	predict(language_identifier, sys.argv[1])
	
def train(datadir, ngram_order=3, smoothing=1):
    """
    Train a character-level language model per language
    and add these to a language identificator.
    """
    identifier = LanguageIdentifier()
    for language_code in 'DE LA'.split():
        #print("Training {0} language model...".format(language_code))
        filename = '{}.txt'.format(language_code.lower())
        training_data = os.path.join(datadir, filename)

        model = CharLM(ngram_order, smoothing)
        model.train(training_data)
        identifier.add_model(language_code, model)
    return identifier

def predict(identifier, testfile):
	"""
	Evaluate the classifier with the test set.
	"""
	
	with open(testfile) as infile:
		for line in infile:
			label = identifier.identify(line.strip())
			print(f'{label}\t{line.strip()}')

	
if __name__ == '__main__':
	main()
