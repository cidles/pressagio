# -*- coding: utf-8 -*-
#
# Poio Tools for Linguists
#
# Copyright (C) 2009-2013 Poio Project
# Author: Peter Bouda <pbouda@cidles.eu>
# URL: <http://media.cidles.eu/poio/>
# For license information, see LICENSE

"""
Classes for predictors and to handle suggestions and predictions.

"""

import os
import configparser

import pressagio.dbconnector

#import pressagio.observer

MIN_PROBABILITY = 0.0
MAX_PROBABILITY = 1.0

class SuggestionException(Exception): pass
class UnknownCombinerException(Exception): pass
class PredictorRegistryException(Exception): pass

class Suggestion:
    """
    Class for a simple suggestion, consists of a string and a probility for that
    string.

    """

    def __init__(self, word, probability):
        self.word = word
        self._probability = probability

    def __eq__(self, other):
        if self.word == other.word and self.probability == other.probability:
            return True
        return False

    def __lt__(self, other):
        if self.probability < other.probability:
            return True
        if self.probability == other.probability:
            return self.word < other.word
        return False

    def __repr__(self):
        return "Word: {0} - Probability: {1}".format(
            self.word, self.probability)


    def probability():
        doc = "The probability property."
        def fget(self):
            return self._probability
        def fset(self, value):
            if value < MIN_PROBABILITY or value > MAX_PROBABILITY:
                raise SuggestionException("Probability is too high or too low.")
            self._probability = value
        def fdel(self):
            del self._probability
        return locals()
    probability = property(**probability())


class Prediction(list):
    """
    Class for predictions from predictors.

    """

    def __init__(self):
        pass

    def __eq__(self, other):
        if self is other:
            return True
        if len(self) != len(other):
            return False
        for i, s in enumerate(other):
            if s != self[i]:
                return False
        return True

    def suggestion_for_token(self, token):
        for s in self:
            if s.word == token:
                return s

    def add_suggestion(self, suggestion):
        if len(self) == 0:
            self.append(suggestion)
        else:
            i = 0
            while i < len(self) and suggestion < self[i]:
                i += 1

            self.insert(i, suggestion)


class PredictorActivator(): #pressagio.observer.Observer
    """
    PredictorActivator starts the execution of the active predictors,
    monitors their execution and collects the predictions returned, or
    terminates a predictor's execution if it execedes its maximum
    prediction time.

    The predictions returned by the individual predictors are combined
    into a single prediction by the active Combiner.

    """

    def __init__(self, config, registry, context_tracker):
        self.config = config
        self.registry = registry
        self.context_tracker = context_tracker
        #self.dispatcher = pressagio.observer.Dispatcher(self)
        self.predictions = []

        self.combiner = None
        self.max_partial_prediction_size = None
        self.predict_time = None
        self._combination_policy = None

    def combination_policy():
        doc = "The combination_policy property."
        def fget(self):
            return self._combination_policy
        def fset(self, value):
            self._combination_policy = value
            if value.lower() == "meritocracy":
                self.combiner = pressagio.combiner.MeritocracyCombiner()
            else:
                raise UnknownCombinerException()
        def fdel(self):
            del self._combination_policy
        return locals()
    combination_policy = property(**combination_policy())

    def predict(self, multiplier, prediction_filter):
        self.predictions.clear()
        for predictor in self.registry:
            predictions.append(predictor.predict(
                self.max_partial_prediction_size * multiplier,
                prediction_filter))
        result = self.combiner.combine(predictions)
        return result

#    def update(self, variable):
#        self.dispatcher.dispatch(variable)


class PredictorRegistry(list): #pressagio.observer.Observer,
    """
    Manages instantiation and iteration through predictors and aids in
    generating predictions and learning.
 
    PredictorRegitry class holds the active predictors and provides the
    interface required to obtain an iterator to the predictors.
 
    The standard use case is: Predictor obtains an iterator from
    PredictorRegistry and invokes the predict() or learn() method on each
    Predictor pointed to by the iterator.
 
    Predictor registry should eventually just be a simple wrapper around
    plump.

    """

    def __init__(self, config):
        self.config = config
 #       self.dispatcher = pressagio.observer.Dispatcher(self)
        self._context_tracker = None
        self.set_predictors()

    def context_tracker():
        doc = "The context_tracker property."
        def fget(self):
            return self._context_tracker
        def fset(self, value):
            if self._context_tracker is not value:                
                self._context_tracker = value
                self.clear()
                self.set_predictors()
        def fdel(self):
            del self._context_tracker
        return locals()
    context_tracker = property(**context_tracker())

    def set_predictors(self):
        if (self.context_tracker):
            self.clear()
            for predictor in self.config["PredictorRegistry"]["predictors"]\
                    .split():
                self.add_predictor(predictor)

    def add_predictor(self, predictor_name):
        predictor_config = self.config[predictor_name]
        predictor = None
        if predictor_config["predictor_class"] == "SmoothedNgramPredictor":
            predictor = SmoothedNgramPredictor(self.config,
                self.context_tracker, predictor_name)

        if predictor:
            self.append(predictor)

#    def update(self, variable):
#        self.dispatcher.dispatch(variable)


class Predictor:
    """
    Base class for predictors.

    """

    def __init__(self, config, context_tracker, predictor_name,
            short_desc = None, long_desc = None):
        self.short_description = short_desc
        self.long_description = long_desc
        self.context_tracker = context_tracker
        self.name = predictor_name
        self.config = config

    def token_satifies_filter(token, prefix, token_filter):
        if token_filter:
            for char in token_filter:
                candidate = prefix + char
                if token.startswith(candidate):
                    return True
        return False

class SmoothedNgramPredictor(Predictor): #, pressagio.observer.Observer
    """
    Calculates prediction from n-gram model in sqlite database. You have to
    create a database with the script `text2ngram` first.

    """

    def __init__(self, config, context_tracker, predictor_name,
            short_desc = None, long_desc = None):
        Predictor.__init__(config, context_tracker, predictor_name,
            short_desc, long_desc)
        self.db = None
        self.cardinality = None
        self.learn_mode_set = False
        self._dbfilename = None
        self._deltas = None
        self._learn_mode = None
        self.config = config
        self.name = predictor_name
        self.context_tracker = context_tracker
        self._read_config()

    def _read_config(self):
        self.dbfilename = self.config[self.name]["dbfilename"]
        self.deltas = self.config[self.name]["deltas"].split()
        self.learn_mode = self.config[self.name]["learn"]

    def dbfilename():
        doc = "The dbfilename property."
        def fget(self):
            return self._dbfilename
        def fset(self, value):
            self._dbfilename = value
            self.init_database_connector_if_ready()
        def fdel(self):
            del self._dbfilename
        return locals()
    dbfilename = property(**dbfilename())

    def deltas():
        doc = "The deltas property."
        def fget(self):
            return self._deltas
        def fset(self, value):
            self._deltas = []
            # make sure that values are floats
            for i, d in enumerate(value):
                self._deltas.append(float(d))
            self.cardinality = len(value)
            self.init_database_connector_if_ready()
        def fdel(self):
            del self._deltas
        return locals()
    deltas = property(**deltas())

    def learn_mode():
        doc = "The learn_mode property."
        def fget(self):
            return self._learn_mode
        def fset(self, value):
            self._learn_mode = value
            self.learn_mode_set = True
            self.init_database_connector_if_ready()
        def fdel(self):
            del self._learn_mode
        return locals()
    learn_mode = property(**learn_mode())

    def init_database_connector_if_ready(self):
        if self.dbfilename and len(self.dbfilename) > 0 and \
                self.cardinality and self.cardinality > 0 and \
                self.learn_mode_set:
            self.db = pressagio.dbconnector.SqliteDatabaseConnector(
                self.dbfilename, self.cardinality) #, self.learn_mode

    def ngram_to_string(self, ngram):
        "|".join(ngram)

    def predict(self, max_partial_prediction_size, filter):
        tokens = [""] * self.cardinality
        prediction = Prediction()

        for i in range(self.cardinality):
            tokens[self.cardinality - 1 - i] = self.context_tracker.token(i)

        prefix_completion_candidates = []
        for k in reversed(range(self.cardinality)):
            if len(prefix_completion_candidates) >= max_partial_prediction_size:
                break
            prefix_ngram = tokens[(len(tokens) - k - 1):]
            partial = None
            if not filter:
                partial = self.db.ngram_like_table(prefix_ngram,
                    max_partial_prediction_size - \
                    len(prefix_completion_candidates))
            else:
                partial = db.ngram_like_table_filtered(prefix_ngram, filter,
                    max_partial_prediction_size - \
                    len(prefix_completion_candidates))

            for p in partial:
                if len(prefix_completion_candidates) > \
                        max_partial_prediction_size:
                    break
                candidate = p[-2] # ???
                if candidate not in prefix_completion_candidates:
                    prefix_completion_candidates.append(candidate)

        # smoothing
        unigram_counts_sum = self.db.unigram_counts_sum()
        for j, candidate in enumerate(prefix_completion_candidates):
            #if j >= max_partial_prediction_size:
            #    break
            tokens[self.cardinality - 1] = candidate

            probability = 0
            for k in range(self.cardinality):
                numerator = self._count(tokens, 0, k + 1)
                denominator = unigram_counts_sum
                if numerator > 0:
                    denominator = self._count(tokens, -1, k)
                frequency = 0
                if denominator > 0:
                    frequency = numerator / denominator
                probability += self.deltas[k] * frequency

            if probability > 0:
                prediction.add_suggestion(Suggestion(tokens[self.cardinality - 1],
                    probability))
        return(prediction)

    def _count(self, tokens, offset, ngram_size):
        result = 0
        if (ngram_size > 0):
            ngram = \
                tokens[len(tokens) - ngram_size + offset:\
                len(tokens) + offset]
            result = self.db.ngram_count(ngram)
        else:
            result = self.db.unigram_counts_sum()
        return result
