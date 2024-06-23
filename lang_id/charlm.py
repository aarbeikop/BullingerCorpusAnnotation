#!/usr/bin/env python3
# coding: utf8
#
# PCL 2, FS 2018


"""
Language modeling with character-level n-grams.
"""


import math
from collections import defaultdict
from collections import Counter


class CharLM:
	"""A character-level n-gram language model."""

	BOS_SYMBOL = object()
	EOS_SYMBOL = object()

	def __init__(self, n=3, smoothing=1):
		"""Initialise a language model of order @param n."""
		self._order = n
		self._logprobs = defaultdict(lambda: defaultdict(float))
		self._smoothing = smoothing

	@staticmethod
	def log(probability):
		"""Transform @param probability into log space."""
		return math.log2(probability)

	@staticmethod
	def perplexity(log_probability, n_items):
		"""
		Compute the perplexity of a sequence with
		@param n_items and @param log_probability.
		"""
		# Entropy is average negative log2 likelihood per word.
		entropy = -log_probability / n_items
		# Perplexity is 2^entropy.
		perplexity = math.pow(2, entropy)
		return perplexity

	def _extract_ngrams(self, sentence):
		"""Produce all n-grams contained in @param sentence."""
		# Beginning of sentence with padding.
		symbols = [self.BOS_SYMBOL] * (self._order-1)
		# Actual characters; unknowns are not replaced (see exercise sheet).
		symbols += [char for char in sentence]
		# End of sentence.
		symbols += [self.EOS_SYMBOL]
		# n-gram extraction, as in https://goo.gl/91x6P6
		return list(zip(*[symbols[i:] for i in range(self._order)]))

	def _add_ngram(self, head, history, log_probability):
		"""
		Add an n-gram to this language model, such that
		P(@param symbol|@param history) = @param log_probability.
		"""
		self._logprobs[history][head] = log_probability

	def _set_unk_given_unknown_history(self, log_probability):
		"""
		Set the log probability used for n-grams with a history we
		have not seen in training.
		"""
		self._logprobs.default_factory = lambda: defaultdict(lambda: log_probability)

	def _set_unk_given_known_history(self, history, log_probability):
		"""
		Set the log probability used for n-grams with a history we
		have seen in training, but not in combination with the current
		head.
		"""
		self._logprobs[history].default_factory = lambda: log_probability

	def train(self, training_data):
		"""
		Train this language model on the sentences contained in
		file @param training_data (one sentence per line).
		"""
		
		with open(training_data, 'r') as infile:
			ngrams = Counter([ngram for line in infile for ngram in self._extract_ngrams(line)])
		histories = Counter([elem[:-1] for elem in ngrams])
		v = len(histories)

		for ngram in ngrams:
			head, history = ngram[-1], ngram[:-1]
			log_probability = self.log((ngrams[ngram]+self._smoothing)/(histories[history]+self._smoothing*v))
			self._add_ngram(head, history, log_probability)

		for history in histories:
			self._set_unk_given_known_history(history, self.log(self._smoothing/(histories[history]+self._smoothing*v)))
			
		self._set_unk_given_unknown_history(self.log(self._smoothing/(self._smoothing*v)))

	def get_perplexity(self, sentence):
		"""Compute the perplexity of @param sentence."""
		log_probability = 0.0
		for ngram in self._extract_ngrams(sentence):
			head, history = ngram[-1], ngram[:-1]
			log_probability += self._logprobs[history][head]
		# +1 in length for EOS_SYMBOL (see PCL2 Session 10, slide 48)
		return self.perplexity(log_probability, len(sentence)+1)
