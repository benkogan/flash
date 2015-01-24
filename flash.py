#!/usr/bin/python
# -*- coding: utf-8 -*-

# flash.py
# copyright (c) 2014 Ben Kogan

import os
import sys
import time
import copy
import yaml
import getch
import random
import signal
import argparse

# indentation
ind = '  '

class Color():
    b = '\033[96m' # blue
    p = '\033[95m' # purple
    n = '\033[92m' # green
    g = '\033[90m' # gray
    e = '\033[0m'  # end

# indicates process has been suspended (ctrl + z)
class SuspendInterrupt(Exception): pass

# indicates invalid search query
class QueryError(Exception):
    def __init__(self, query):
        self.query = query
    def __str(self):
        return self.query

class Card(object):

    def __init__(self, sides, facts, style):
        self.sides = sides
        self.facts = facts
        self.style = style # review side order style

        self.timer = 0
        self.right_timeout = 10
        self.wrong_timeout = 1

        self.turn_count = 0
        self.first_turn = True
        self.last_turn = False
        self.is_done = False

        # TODO: do this dynamically while printing?
        fact_keys = [key for side in self.sides for key in side]
        longest_key = max(fact_keys, key=len)
        self.sep_width = len(longest_key)

    def review(self):
        CORRECT = 1
        UNDO = 'z'
        HELP = 'h'
        c = Color()

        for side in self.sides:
            facts = [(fact, self.facts[fact]) for fact in side]

            for fact in facts:
                separator = '·'
                width = self.sep_width - len(fact[0]) + 2

                if self.first_turn: col = c.p
                elif self.last_turn: col = c.n
                else: col = c.b

                print ind + str.format('{key} {sep} {fct}',
                        key = col + fact[0] + c.e,
                        sep = separator.rjust(width),
                        fct = fact[1].encode('utf-8'))

            last_side = self.sides[-1]
            if side != last_side:
                r = prompt_char()
                if r == UNDO: return (None, 'undo')
                if r == HELP: return (None, 'help')

        answer = prompt_char('\n' + ind + '(1: correct, 2: incorrect) ')

        try: answer = int(answer)
        except: pass

        if answer == UNDO: return (None, 'undo')
        elif answer == HELP: return (None, 'help')
        elif answer == CORRECT: return (True, None)
        else: return (False, None)

    def rewind(self):
        self.turn_count -= 1
        if self.turn_count == 0: self.first_turn = True

        if self.is_done: self.is_done = False
        else: self.last_turn = False

        return self

    def done(self):
        self.turn_count += 1
        self.is_done = True
        return self

    def correct(self):
        self.turn_count += 1
        self.first_turn = False
        self.last_turn = True
        self.__update(self.right_timeout)
        return self

    def incorrect(self):
        self.turn_count += 1
        self.first_turn = False
        self.last_turn = False
        self.__update(self.wrong_timeout)
        return self

    # update review status and timer
    def __update(self, timeout):
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
                self.units[unit] += [Card(self.sides[style], card, style) for card in deck[unit]]

    def get_cards(self, **kwargs):
        cards = []
        for unit in kwargs['units']:
            cards = cards + self.units[unit]

        # apply review style filter if not None
        if kwargs['style']:
            cards = [card for card in cards if card.style == kwargs['style']]
        return cards

def min_to_sec(m): return 60 * m

def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')

def stats(pending, waiting, done):
    c = Color()
    return str.format('{pend} pending : {wait} waiting : {done} done',
            pend = c.p + str(len(pending)) + c.e,
            wait = c.b + str(len(waiting)) + c.e,
            done = c.n + str(len(done))    + c.e)

def timer_done(card):
    now = time.time()
    return True if now > card.timer else False

def prompt_char(s=''):
    if s: sys.stdout.write(s)

    char = getch.char()

    # handle signal codes (ctrl + c, d, z)
    if char == '\x03': raise KeyboardInterrupt()
    if char == '\x04': raise EOFError()
    if char == '\x1a': raise SuspendInterrupt()

    return char

def parse(card_file):
    with open(card_file) as fp:
        deck_data = yaml.load(fp)
        deck_definition = deck_data.pop('Definition')
        return (deck_data, deck_definition)

def print_status(prev_correct, pending, waiting, done):
    if prev_correct is None:  symbol = ''
    if prev_correct is True:  symbol = '✔︎'
    if prev_correct is False: symbol = '✘'

    c = Color()
    print c.g + symbol + c.e
    print
    print ind + stats(pending, waiting, done)
    print

def print_help():
    c = Color()
    print
    print
    print ind + 'Usage:'
    print c.g
    print ind + '  Press any key to advance a card to its'
    print ind + '  next side. Once the final side is reached,'
    print ind + '  press `1` for a correct answer, or any'
    print ind + '  other key (excluding the commands below)'
    print ind + '  for an incorrect answer. Quit at any time'
    print ind + '  with `^C` (control + c).'
    print c.e
    print ind + 'Commands:'
    print c.g
    print ind + '  `z`      undo and rewind one card'
    print ind + '  `h`      show this help screen'
    print c.e
    print ind + 'Press any key to leave this help screen.'
    print

def quiz(cards):
    pending = copy.deepcopy(cards)
    waiting = []
    done = []

    # queue of reviewed cards used for `undo`
    reviewed_q = []

    suspended = None

    prev_correct = None

    while pending or waiting:

        for card in waiting:
            if timer_done(card):
                waiting.remove(card)
                pending.append(card)

        if not pending:
            card = min(waiting, key=lambda c: c.timer)
            waiting.remove(card)
            pending.append(card)

        card = random.choice(pending)
        pending.remove(card)

        # replace any suspended cards (see below)
        if suspended:
            waiting.append(suspended)
            suspended = None

        # problem: if all cards are green and get one wrong, that one's timer will
        # be a lot less than the rest -> will show up again immediately
        # => if card is within last five cards, choose another, then put it back in waiting

        # if card in last five reviewed cards, try again and then replace
        # TODO: suspend for a random number of turns > 5 instead of exactly 5
        # TODO !!!!: this might cause issues with undo !!
        if card in reviewed_q[-5:] and len(reviewed_q) > 5:
            suspended = card
            continue

        while True:

            clear_screen()
            print_status(prev_correct, pending, waiting, done)

            try: correct, option = card.review()
            except SuspendInterrupt: os.kill(os.getpid(), signal.SIGTSTP)
            else:

                if option == 'undo':
                    if card.first_turn: pending.append(card)
                    else: waiting.append(card)

                    if reviewed_q:
                        card = reviewed_q.pop()
                        card.rewind()
                    else:
                        # repeat current card
                        pass

                    if card in waiting: waiting.remove(card)
                    if card in pending: pending.remove(card)
                    if card in done: done.remove(card)
                    if card == suspended: suspended = None

                    prev_correct = None

                elif option == 'help':
                    while True:
                        try:
                            clear_screen()
                            print_help()
                            prompt_char()
                        except SuspendInterrupt: os.kill(os.getpid(), signal.SIGTSTP)
                        else: break

                elif correct:
                    if card.last_turn: done.append(card.done())
                    else: waiting.append(card.correct())

                    reviewed_q.append(card)
                    prev_correct = True

                elif not correct:
                    waiting.append(card.incorrect())

                    reviewed_q.append(card)
                    prev_correct = False

                if option is None: break

def help():
    name = sys.argv[0]
    name = os.path.basename(name)

    print
    print ind + name, '<command> [options]'
    print
    print ind + 'Commands:'
    print
    print ind + '  review PATH           Review cards from deck file at specified path'
    print
    print ind + 'Options:'
    print
    print ind + '  -q, --query QUERY     Search for units seperated by spaces'
    print ind + '  -s, --style SIDE      Filter cards to show only specific side-order style'
    print ind + '  -h, --help            Output help message'
    print ind + '  -v, --version         Output version information'
    print
    sys.exit()

def parse_args():
    parser = argparse.ArgumentParser(description='A plaintext flashcard app', add_help=False)

    if len(sys.argv) < 3: help()

    if sys.argv.pop(1) != 'review': help()
    deck_path = sys.argv.pop(1)

    parser.add_argument('-q', '--query')
    parser.add_argument('-s', '--style')
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='version', version='0.0.1')

    args = parser.parse_args()

    if args.help: help()

    deck = deck_path
    query = args.query
    side = args.style
    return (deck, query, side)

if __name__ == '__main__':

    deck_path, query, style_filter = parse_args()
    deck_search = query.split(' ')

    deck_data, deck_def = parse(deck_path)

    deck = Deck(deck_data, deck_def)
    cards = deck.get_cards(units=deck_search, style=style_filter)

    try:
        quiz(cards)
        print
        print
        print ind + 'Review done!'
        print

    except (KeyboardInterrupt, EOFError):
        print
        print ind + 'Quit!'
        print
        sys.exit()

