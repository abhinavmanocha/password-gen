#!/usr/bin/env python3
"""Generator invariants — run this after touching the word lists or the leet swap.

    python tools/test_gen.py

Three layers:
  1. a deterministic pipeline check (secrets stubbed) that pins the exact expected output
  2. a large random sample asserting the style invariants
  3. regression tests for the swap itself

The invariants exist because all three of these shipped as real bugs first: a swap that ate the
camelCase hump (`loud$wing`), a pair with nothing to swap (`fuzzyMug`, no symbol at all), and a
fallback that swapped the opening character (`0nyxDune`).
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gen  # noqa: E402

ALLOWED = re.compile(r"^[A-Za-z0-9@!0$3]+$")
SYMBOLS = set("@!0$3")
SAMPLES = 20_000

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + label + (("  " + detail) if detail else ""))
    if not ok:
        failures.append(label)


def style_problems(pw: str) -> list[str]:
    """Invariants that hold regardless of where the swap landed."""
    problems = []
    if not re.match(r"^[a-z]", pw):
        problems.append("does not start lowercase")
    if not re.search(r"[A-Z]", pw):
        problems.append("lost the uppercase hump")
    if not any(c in SYMBOLS for c in pw):
        problems.append("no leet symbol at all")
    if not re.search(r"\d{2,4}$", pw):
        problems.append("does not end with 2-4 digits")
    if not ALLOWED.match(pw):
        problems.append("contains an unexpected character")
    return problems


class _Deterministic:
    """Stub for `secrets` that always takes the first option, so output is predictable."""

    def __init__(self, randbelow_value: int = 0) -> None:
        self._randbelow = randbelow_value

    @staticmethod
    def choice(seq):
        return seq[0]

    def randbelow(self, n):
        return self._randbelow


def main() -> int:
    real_secrets = gen.secrets

    # 1. deterministic pipeline: modifier[0] + noun[0], swap at the first eligible letter
    gen.secrets = _Deterministic(0)
    first_words = gen.MODIFIERS[0] + gen.NOUNS[0].capitalize()
    expect_swap = gen._leet_once(first_words)
    check("deterministic: words are the first modifier + first noun",
          first_words == "fireFox", first_words)
    check("deterministic: swap lands on an interior lowercase letter",
          expect_swap == "f!reFox", expect_swap)
    check("deterministic: significant ending used when randbelow(4)==0",
          gen.generate(2, 2) == expect_swap + "604", gen.generate(2, 2))

    # leading-zero guard: a 3-digit ending starting with 0 must be forced to start with 7
    gen.secrets = _Deterministic(3)
    out = gen.generate(2, 2, mixed=True)
    check("deterministic: leading zero in the ending is replaced with 7",
          out == expect_swap + "700", out)
    gen.secrets = real_secrets

    # 2. random sample
    bad: list[str] = []
    seen_swaps: set[str] = set()
    draws = 0
    for _ in range(SAMPLES):
        for words, digits in ((2, 2), (2, 4), (3, 3), (4, 2)):
            pw = gen.generate(words, digits)
            draws += 1
            for symbol in SYMBOLS:
                if symbol in pw:
                    seen_swaps.add(symbol)
            problems = style_problems(pw)
            if problems and len(bad) < 5:
                bad.append(f"{pw}: {problems[0]}")
    check(f"random sample holds every style invariant ({draws:,} passwords)", not bad,
          "; ".join(bad))
    check("every swap character appears across the sample", len(seen_swaps) == len(SYMBOLS),
          "".join(sorted(seen_swaps)))
    check("draws are distinct (300 fresh 2-word passwords)",
          len(set(gen.generate(2, 2) for _ in range(300))) >= 295)

    # 3. the swap itself
    check("swap never eats the second word's capital (loudSwing)",
          all(re.search(r"[A-Z]", gen._leet_once("loudSwing")) for _ in range(500)))
    check("swap never touches the opening character (onyxDune)",
          all(gen._leet_once("onyxDune")[0] == "o" for _ in range(500)))
    check("a swap is always applied when the phrase allows one",
          all(any(c in SYMBOLS for c in gen._leet_once(w))
              for w in ("loudSwing", "happyPlace", "miltonHome", "crunchySnack")
              for _ in range(200)))
    check("phrases with nothing to swap are never drawn",
          all(gen._swap_positions(gen._build_words(2)) for _ in range(2000)))
    check("three-word phrases always find a swap position",
          all(gen._swap_positions(gen._build_words(3)) for _ in range(2000)))

    print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILED"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
