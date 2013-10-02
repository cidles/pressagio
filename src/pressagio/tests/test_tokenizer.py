# -*- coding: utf-8 -*-
#
# Poio Tools for Linguists
#
# Copyright (C) 2009-2013 Poio Project
# Author: Peter Bouda <pbouda@cidles.eu>
# URL: <http://media.cidles.eu/poio/>
# For license information, see LICENSE

import os
import codecs

import pressagio.tokenizer


class TestForwardTokenizer():

    def setup(self):
        filename = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
            'test_data', 'der_linksdenker.txt'))
        self.tokenizer = pressagio.tokenizer.ForwardTokenizer(filename)

    def test_reset_stream(self):
        self.tokenizer.next_token()
        assert self.tokenizer.stream.tell() != 0
        self.tokenizer.reset_stream()
        assert self.tokenizer.stream.tell() == 0

    def test_count_characters(self):
        #print(self.tokenizer.count_characters())
        assert self.tokenizer.count_characters() == 7927

    def test_count_tokens(self):
        assert self.tokenizer.count_tokens() == 1251

    def test_has_more_tokens(self):
        assert self.tokenizer.has_more_tokens() == True

    def test_next_token(self):
        assert self.tokenizer.next_token() == "Der"
        self.tokenizer.reset_stream()

    def test_is_blankspace(self):
        assert self.tokenizer.is_blankspace('\n') == True
        assert self.tokenizer.is_blankspace('a') == False

    def test_is_separator(self):
        assert self.tokenizer.is_separator('"') == True
        assert self.tokenizer.is_separator('b') == False


class TestReverseTokenizer():

    def setup(self):
        filename = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
            'test_data', 'der_linksdenker.txt'))
        self.tokenizer = pressagio.tokenizer.ReverseTokenizer(filename)

    def test_reset_stream(self):
        self.tokenizer.next_token()
        assert self.tokenizer.stream.tell() != self.tokenizer.offend
        self.tokenizer.reset_stream()
        assert self.tokenizer.stream.tell() == self.tokenizer.offend

    def test_count_tokens(self):
        assert self.tokenizer.count_tokens() == 1251

    def test_has_more_tokens(self):
        assert self.tokenizer.has_more_tokens() == True

    def test_next_token(self):
        assert self.tokenizer.next_token() == "Linksdenker"
        self.tokenizer.reset_stream()


def test_tokenizers_are_equal():
        filename = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
            'test_data', 'der_linksdenker.txt'))
        reverse_tokenizer = pressagio.tokenizer.ReverseTokenizer(filename)
        forward_tokenizer = pressagio.tokenizer.ForwardTokenizer(filename)
        forward_tokens = []
        reverse_tokens = []
        while forward_tokenizer.has_more_tokens():
            forward_tokens.append(forward_tokenizer.next_token())
        while reverse_tokenizer.has_more_tokens():
            reverse_tokens.append(reverse_tokenizer.next_token())
        diff = set(forward_tokens) ^ set(reverse_tokens)
        assert forward_tokens == reverse_tokens[::-1]
        assert len(diff) == 0
