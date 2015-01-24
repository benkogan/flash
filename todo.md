
TODO
====

- custom parser / format
- PHONY types (e.g. tags) in card spec; use vars instead of hard-coding to search by them
    - also do this for unit / nesting structure?
- make so different sides can be defined in definition, not just forwards / backwards
- UI: tag, search, etc. parsing
- line wrap for long lines
- be able to specify a single ordering direction, i.e. recognition only

New plan
--------

```
note = raw info for a fact
card = ordered and sided card for a fact; a fact can produce multiple cards
deck = all the cards for a specified search
     | a deck is dynamic, not to be confused with file containing notes
collection = a file that contains notes
definition = the cards that should be created for each note

build_deck():
  for each `note`
    create a `card` for each `card_type` in `definition`

TODO: define `quiz` algorithm; make cards stateless
TODO: define `review(card)`

algo:
  instead of timers, just do three boxes?
  add filters to prevent dupes, etc
  much simpler, more testable
```

Card commands
-------------

- `z`: undo
- `h` or `?`: show help overlay
- handle editing a card (and writing to card file)?

Algorithm
---------

- when forced to pick from waiting, choose a newer one!
	- but with some degree of randomness?
- if all are on last turn and I get one wrong, it seems to come up immediately next; should be way later
- serialize last session on SIGINT?
- try to not pick the reverse version of the card just shown
- make timer-expired cards take precedence?

User Interface
--------------

Search to start (searches configurable default location):

	$ flash review --deck vocab --search '(unit:U41 && tag:a) || unit:U42)'

Or feed in a deck:

	$ cat vocab | flash review --search '...'

Web hooks
---------

- jisho.org definition
- kanji diagram lookup feature

Program design
--------------

- disambiguate facts, sides dichotomy in card class

