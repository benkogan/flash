#!/usr/bin/python
# -*- coding: utf-8 -*-

# flash.py
# copyright (c) 2015 Ben Kogan

# note that up from main, functions are listed in order of use (ascending)

import os
import sys
import json
import random
import argparse

from functools import partial

# new cram mode: continuous iterations with bad ones first?
# should this be used for new cards in SRS?

# make mutable
# enables `shuffle, filter, choose, review, update`
#    for undo; track actions in each card along with time it was done

# TODO: `is_due` may need to be `partial`d based on mode
# TODO: special shuffle; handles spacing out twins (looks at last action using that filter fn to find last card), etc

def get_candidates(cards):
    # TODO: re-implement with partial and compose?
    # allows them to exists as re-usable global fns

    unfinished_cards = filter(lambda card: not card.done, cards)

    current_round = min(cards, key=lambda card: card.round)
    current_cards = filter(lambda card: card.round == current_round, cards)

    min_score = min(cards, key=lambda card: card.score).score
    return filter(lambda card: card.score == min_score, cards)

def shuffle(cards):
    random.shuffle(cards)
    # TODO: space out similar cards;
    # take last used card (by time) into effect
    return cards

# TODO: what does this do?
# TODO: handle escape sequences for ctrl etc

def get_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

class Screen(object):

    def __init__(self, mode):
        self.mode = mode
        self.srs = 'srs'
        self.cram = 'cram'
        self.content = ''
        self.indentation = '  '

    def prompt_answer(self):
        if self.mode == self.cram:
            self.__add_line('(1: correct, 2: incorrect) ')
            self.puts()
        elif self.mode == self.srs:
            # TODO
            pass
        else:
            # TODO: error
            pass

    def puts(self, clear=True, msg=None):
        if clear: self.__clear_screen()
        screen = msg if msg else self.content.split('\n')
        for line in screen: print self.indentation + line

    def __add_line(self, line):
        self.content += '\n%s' % line

    def __clear_screen(self):
        os.system('clear')

class Quiz(object):

    def __init__(self, mode):
        self.mode = mode
        self.screen = Screen(mode)

    def quiz_card(self, card):
        for side in card.sides:
            self.screen.side(card)
            if side == card.sides[-1]: break
            get_char()

        self.screen.prompt_answer()
        answer = get_char()
        return Result(answer)

    def review(self, cards):
        shuffle(cards)
        current = get_candidates(cards)
        if not current: return

        card = current[0]
        result = self.quiz_card(card)

        if result.answer: card.handle(result)
        elif result.undo: filter(last_action, cards).undo()
        else: raise RuntimeWarning('Invalid result produced')

        self.screen.update(result) # TODO: clear, add prev result char, etc
        self.review(cards)

class Card(object):
    def __init__(self, sides):
        self.sides = sides
        self.score = 0
        self.round = 0
        self.done = False
    def __repr__(self):
        out = ''
        for index, side in enumerate(self.sides):
            out += str(index) + ':' + str(side) + '\n'
        return out

class Fact(object):
    def __init__(self, key, value):
        self.key = key.encode('utf-8')
        self.value = value.encode('utf-8')
    def __repr__(self):
        return '%s: %s' % (self.key, self.value)

# TODO: what happens for keys that aren't defined?
#   -> need to specify a default value
# TODO: add SRS info

def build_card(ordering, note):
    def build_fact(key): return Fact(key, note[key])
    sides = [map(build_fact, side) for side in ordering]
    return Card(sides)

# TODO: style

def build_cards(definition, style, notes):
    cards = []
    for order_key in definition:
        builder = partial(build_card, definition[order_key])
        cards += map(builder, notes)
    return cards

def intersection(first, second):
    return filter(first.__contains__, second)

# TODO: this assumes all notes have tags; should tags be pre-populated if there aren't any?
# TODO: this this assume that all groups have tags too?

def filter_notes(query, all_notes):
    notes = []
    for group in query:
        def match_by_tag(note):
            return True if intersection(group.tags, note["tags"]) else False
        notes_by_unit = all_notes[group.unit]
        notes += filter(match_by_tag, notes_by_unit)
    return notes

def load_collection(collection_path):
    with open(collection_path) as collection_file:
        collection = json.load(collection_file)
    definition = collection['definition']
    notes = collection['notes']
    return (definition, notes)

class Group(object):
    def __init__(self, unit, tags):
        self.unit = unit
        self.tags = tags

# e.g. U1 U2[a] U3[a,b] (NO SPACES in TAGS)
# note this is boolean-OR for both levels (unit and tag level)
# TODO: re-implement using regexp

def parse_query_atom(atom):
    unit = atom
    tags = []
    if '[' in atom:
        brace1 = atom.index('[')
        brace2 = atom.index(']')
        unit = atom[:brace1]
        tags = atom[brace1+1:brace2].split(',')
    return Group(unit, tags)

def parse_query(search_query):
    query = search_query.split(' ')
    return map(parse_query_atom, query)

# TODO: replace using screen
def puts(msg):
    indentation = '  '
    print indentation + msg

def usage(exe):
    name = os.path.basename(exe)
    try: name = name[:name.index('.')]
    except: pass
    msg = ['',
            name + ' <command> [options]',
            '',
            'Commands:',
            '',
            '  review PATH           Review cards from collection at specified path',
            '',
            'Options:',
            '',
            '  -q, --query QUERY     Search for units seperated by spaces',
            '  -s, --style SIDE      Filter cards to show only specific side-order style',
            '  -h, --help            Output help message',
            '  -v, --version         Output version information',
            '']
    for line in msg: puts(line)

def parse_args(argv):
    parser = argparse.ArgumentParser()#add_help=False)
    parser.add_argument('--collection_path')
    parser.add_argument('-q', '--query')
    parser.add_argument('-s', '--style')
    #parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='version', version='0.0.1')

    exe = argv.pop(0)
    args = parser.parse_args(argv)
    return (exe, args)

def main(argv):
    exe, args = parse_args(argv)

    #if command not in ['review', 'cram', 'edit'] or args.help:
    #    usage(exe)
    #    sys.exit(1)

    search_groups = parse_query(args.query)
    defintion, all_notes = load_collection(args.collection_path)
    notes = filter_notes(search_groups, all_notes)
    cards = build_cards(defintion, args.style, notes)

    quiz = Quiz('cram') # TODO: mode
    quiz.review(cards)

if __name__ == '__main__': main(sys.argv[:])

