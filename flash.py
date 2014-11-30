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

class Card(object):

    def __init__(self, sides, facts):
        self.sides = sides
        self.facts = facts

        self.timer = 0
        self.right_timeout = 10
        self.wrong_timeout = 1

        self.turn_count = 0
        self.first_turn = True
        self.last_turn = False
        self.is_done = False

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
                self.units[unit] += [Card(self.sides[style], card) for card in deck[unit]]

    def get_cards(self, **kwargs):
        cards = []
        for unit in kwargs['units']:
            cards = cards + self.units[unit]
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
    c = Color()

    if prev_correct is None:  symbol = ''
    if prev_correct is True:  symbol = '✔︎'
    if prev_correct is False: symbol = '✘'

    print c.g + symbol + c.e
    print
    print ind + stats(pending, waiting, done)
    print

def print_help():
    c = Color() # TODO: make global?

    print
    print
    print ind + 'Usage:'
    print c.g
    print ind + ind + 'Press any key to advance a card to its'
    print ind + ind + 'next side. Once the final side is reached,'
    print ind + ind + 'press `1` for a correct answer, or any'
    print ind + ind + 'other key (excluding the commands below)'
    print ind + ind + 'for an incorrect answer. Quit at any time'
    print ind + ind + 'with `^C` (control + c).'
    print c.e
    print ind + 'Commands:'
    print c.g
    print ind + ind + '`z`      undo and rewind one card'
    print ind + ind + '`h`      show this help screen'
    print c.e
    print ind + 'Press any key to leave this help screen.'
    print

def quiz(cards):
    pending = copy.deepcopy(cards)
    waiting = []
    done = []

    # queue of reviewed cards used for `undo`
    reviewed_q = []

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

                    prev_correct = None

                elif option == 'help':
                    clear_screen()
                    print_help()
                    prompt_char()

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

if __name__ == '__main__':
    deck_path = sys.argv[1]
    units = sys.argv[2:]
    deck_data, deck_def = parse(deck_path)

    deck = Deck(deck_data, deck_def)
    cards = deck.get_cards(units=units)

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

