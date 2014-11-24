#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import copy
import yaml
import getch
import random

# indentation
ind = '  '

class Color():
    b = '\033[96m' # blue
    g = '\033[90m' # gray
    e = '\033[0m'  # end

class Card(object):

    def __init__(self, sides, facts, style):
        self.sides = sides
        self.facts = facts
        self.style = style

        self.timer = 0
        self.right_timeout = 10
        self.wrong_timeout = 01

        self.last_turn = False

        # get length of longest fact key
        k = self.sides.keys()[0] # use an arbitrary ordering style
        keys = [key for side in self.sides[k] for key in side]
        self.sep_width = len((max(keys, key=len)))

    def review(self):
        CORRECT = 1
        INCORRECT = 2
        c = Color()

        # use specified ordering style
        sides = self.sides[self.style]

        for side in sides:
            facts = [(fact, self.facts[fact]) for fact in side]

            for fact in facts:
                separator = '·'
                width = self.sep_width - len(fact[0]) + 3

                print ind + str.format('{key}{sep} {fct}',
                        key = c.b + fact[0] + c.e,
                        sep = c.g + separator.rjust(width) + c.e,
                        fct = fact[1].encode('utf-8'))

            # not last side
            if side != sides[-1]: prompt_char()

        answer = prompt_char('\n' + ind + '(1: correct, 2: incorrect) ')
        try: answer = int(answer)
        except: answer = -1
        return True if answer == CORRECT else False

    def   correct(self): return self.__update(self.right_timeout, True)
    def incorrect(self): return self.__update(self.wrong_timeout)

    # update review status and timeout
    def __update(self, timeout, answer=False):

        # update review status
        self.last_turn = answer

        # update timer
        deadline = time.time() + min_to_sec(timeout)
        self.timer = int(deadline)

        return self

class Deck(object):

    def __init__(self, deck, definition):
        self.sides = definition
        self.units = {}

        for unit in deck:
            self.units[unit] = []

            # for each card in input file, create a card object for each of
            # the definition's ordering styles
            for style in self.sides:
                self.units[unit] += [Card(self.sides, card, style) for card in deck[unit]]

    def get_cards(self, **kwargs):
        cards = []
        for unit in kwargs['units']:
            cards = cards + self.units[unit]
        return cards

def min_to_sec(m): return 60 * m

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    print '\n'

def stats(pending, waiting, done):
    return '%d pending : %d waiting : %d done' % (len(pending), len(waiting), done)

def timer_done(card):
    now = time.time()
    return True if now > card.timer else False

def prompt_char(s=''):
    if s: sys.stdout.write(s)

    char = getch.char()

    # handle signal codes (ctrl + c, d, z)
    if char == '\x03': raise KeyboardInterrupt()
    if char == '\x04': raise EOFError()
    if char == '\x1a': print '^Z handling is not implemented.'

    return char

def parse(card_file):
    with open(card_file) as fp:
        deck_data = yaml.load(fp)
        deck_definition = deck_data.pop('Definition')
        return (deck_data, deck_definition)

def quiz(cards):
    pending = copy.deepcopy(cards)
    waiting = []
    done = 0

    while pending or waiting:

        clear_screen()

        pending += [card for card in waiting if timer_done(card)]

        if not pending:
            card = min(waiting, key=lambda c: c.timer)
            waiting.remove(card)
            pending.append(card)

        print ind + stats(pending, waiting, done)
        print

        card = random.choice(pending)
        pending.remove(card)

        if card.last_turn:
            if card.review(): done += 1
            else: waiting.append(card.incorrect())

        else:
            if card.review(): waiting.append(card.correct())
            else: waiting.append(card.incorrect())

    print
    print
    print ind + 'Review over.'
    print

if __name__ == '__main__':
    deck_path = sys.argv[1]
    units = sys.argv[2:]
    deck_data, deck_def = parse(deck_path)

    deck = Deck(deck_data, deck_def)
    cards = deck.get_cards(units=units)

    quiz(cards)

