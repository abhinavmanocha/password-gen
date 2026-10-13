#!/usr/bin/env python3
"""Human-memorable password generator.

Style: modifier + Capitalized noun (camelCase), one leet substitution, 2-3 digits.

    fire + Fox      -> f!reFox99
    milton + Home   -> m!ltonHome604
    long + Track    -> longTr@ck77
    crunchy + Snack -> crunchySn@ck82

Usage:
    python gen.py                 # 10 passwords
    python gen.py -n 5 -w 3       # 5 stronger three-word passwords
    python gen.py --mixed         # 2- or 3-digit endings
    python gen.py --bits          # show the rough strength estimate
"""
from __future__ import annotations

import argparse
import math
import secrets

_MODIFIERS = """
fire milton brampton long crunchy blue happy silver copper iron golden red green
black white wild brave swift quiet loud bright dark deep high low north south
east west rocky sandy snowy rainy sunny windy stormy frosty dusty rusty mossy
foggy smoky maple cedar birch willow aspen oak pine thorn ivy jade onyx pearl
amber coral ruby ember ash snow ice steel brass glass stone brick sand river
lake ocean tidal coastal alpine timber urban rustic vintage modern turbo rapid
rocket comet meteor lunar solar stellar cosmic pixel cyber laser neon echo sonic
vinyl retro classic grand royal noble lucky jolly merry crispy juicy spicy sweet
salty zesty creamy toasty frosted silky fuzzy woolly cheeky sneaky clever witty
brisk eager steady solid prime alpha omega delta sigma mellow gentle bold sharp
smooth fresh clean tidy smart amber
""".split()

_NOUNS = """
fox home track snack grip place hawk wolf bear lynx otter badger beaver falcon
raven crow finch robin heron crane tiger lion panther cobra viper gecko dragon
phoenix griffin hunter ranger scout pilot captain skipper trader broker banker
baker brewer barber chef server host manager owner partner builder maker coder
writer reader rider driver walker hiker climber diver sailor route trail path
road lane street bridge tunnel harbor marina dock pier beach shore cliff canyon
valley meadow forest grove garden orchard vineyard farm ranch cabin cottage
lodge manor tower castle temple market plaza junction station depot terminal
gateway portal beacon signal radar anchor compass atlas ledger vault safe key
lock chain cable wire circuit engine motor turbine vector matrix cipher code
pixel byte cache socket packet stream buffer kernel quantum photon prism lens
mirror vibe rhythm beat tune melody chord tempo groove swing dance feast table
plate grill oven skillet kettle mug bottle barrel keg cask flask pantry cellar
kitchen counter booth patio terrace balcony atrium loft studio gallery museum
theatre arena stadium rink court field pitch green bunker summit ridge crest
peak slope basin delta oasis dune mesa bay cove creek falls spring brook
""".split()

# dict.fromkeys de-duplicates while keeping order
MODIFIERS = list(dict.fromkeys(_MODIFIERS))
NOUNS = list(dict.fromkeys(_NOUNS))

LEET = {"a": "@", "i": "!", "o": "0", "e": "3", "s": "$"}

# endings people actually remember (Milton/Pearl area codes, doubles)
SIGNIFICANT = ["604", "905", "416", "647", "365", "289", "437",
               "88", "99", "77", "55", "44", "22", "11", "21"]


def _leet_once(word: str) -> str:
    """Swap one interior letter for its leet twin (a->@, i->!, o->0, e->3, s->$)."""
    interior = [i for i, c in enumerate(word) if c.lower() in LEET and 0 < i < len(word) - 1]
    spots = interior or [i for i, c in enumerate(word) if c.lower() in LEET]
    if not spots:
        return word
    i = secrets.choice(spots)
    return word[:i] + LEET[word[i].lower()] + word[i + 1:]


def generate(words: int = 2, digits: int = 2, mixed: bool = False) -> str:
    """Return one password in the house style."""
    parts = [secrets.choice(MODIFIERS)]
    parts += [secrets.choice(NOUNS).capitalize() for _ in range(words - 1)]
    pw = _leet_once("".join(parts))

    if secrets.randbelow(4) == 0:
        ending = secrets.choice(SIGNIFICANT)
    else:
        n = digits + (1 if mixed and secrets.randbelow(2) else 0)
        ending = "".join(secrets.choice("0123456789") for _ in range(n))
        if ending.startswith("0"):
            ending = "7" + ending[1:]
    return pw + ending


def est_bits(words: int = 2, digits: int = 2) -> float:
    """Rough entropy estimate in bits (ignores the leet swap, which adds a few)."""
    combos = len(MODIFIERS) * len(NOUNS) ** (words - 1)
    return math.log2(combos) + math.log2(10 ** digits)


def main() -> None:
    p = argparse.ArgumentParser(description="Human-memorable password generator")
    p.add_argument("-n", "--count", type=int, default=10, help="how many (default 10)")
    p.add_argument("-w", "--words", type=int, default=2, choices=(2, 3, 4),
                   help="words per password (default 2)")
    p.add_argument("-d", "--digits", type=int, default=2, choices=(2, 3, 4),
                   help="digits at the end (default 2)")
    p.add_argument("--mixed", action="store_true", help="randomly mix in an extra digit")
    p.add_argument("--bits", action="store_true", help="print the strength estimate")
    args = p.parse_args()

    for _ in range(args.count):
        print(generate(args.words, args.digits, args.mixed))

    if args.bits:
        bits = est_bits(args.words, args.digits)
        print(f"\n~{bits:.0f} bits from word choice + digits alone "
              f"({args.words} word(s), {args.digits} digits).", file=__import__("sys").stderr)
        if bits < 40:
            print("Fine for Wi-Fi, streaming, PIN-style logins. "
                  "Use -w 3 for email or banking.", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
