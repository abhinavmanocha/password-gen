#!/usr/bin/env python3
"""Real-browser check for the password generator page.

    python -m http.server 8099          # from the project root
    python tools/ui_check.py http://127.0.0.1:8099/ shot.png

Asserts the page renders passwords in the intended shape, that the controls change
what is produced, and that Copy responds. Saves a phone-viewport screenshot.
"""
from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099/"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "shot.png"

# word body allowed characters; the swap puts one of @!0$3 inside the words
ALLOWED = re.compile(r"^[A-Za-z0-9@!0$3]+$")
SYMBOLS = set("@!0$3")


def shape_ok(value: str) -> bool:
    """Lowercase start, an uppercase hump, a swap in the words, 2-4 trailing digits."""
    body = re.sub(r"\d{1,4}$", "", value)
    return (bool(re.match(r"^[a-z]", value))
            and bool(re.search(r"[A-Z]", value))
            and any(c in SYMBOLS for c in body)
            and bool(re.search(r"\d{2,4}$", value))
            and bool(ALLOWED.match(value)))

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + label + (("  " + detail) if detail else ""))
    if not ok:
        failures.append(label)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    page.goto(URL, wait_until="load")
    page.wait_for_selector(".row code")

    first = page.eval_on_selector_all(".row code", "els => els.map(e => e.textContent)")
    check("six rows render by default", len(first) == 6, f"got {len(first)}")
    check("every password matches the house shape", all(shape_ok(v) for v in first),
          ", ".join(first))
    check("every password has a swap in the words",
          all(any(c in SYMBOLS for c in re.sub(r"\d{1,4}$", "", v)) for v in first))
    check("all six are unique", len(set(first)) == 6)

    # three-word mode must produce longer output
    page.click('#segWords button[data-v="3"]')
    page.wait_for_timeout(150)
    second = page.eval_on_selector_all(".row code", "els => els.map(e => e.textContent)")
    check("three-word mode regenerates", second != first)
    check("three-word passwords are longer",
          min(len(v) for v in second) > min(len(v) for v in first),
          f"{min(map(len, first))} -> {min(map(len, second))}")
    check("three-word passwords still match", all(shape_ok(v) for v in second))

    # strength meter reacts
    bits = page.inner_text("#bitsValue")
    check("strength meter reports bits", bool(re.search(r"about \d+ bits", bits)), bits)

    # last word: the first row renders as plain text, no markup injected
    check("password rendered as text, not markup",
          page.eval_on_selector(".row code", "e => e.children.length === 0"))

    # copy button feedback
    page.click('#segWords button[data-v="2"]')
    page.wait_for_timeout(150)
    page.click(".row .copy")
    page.wait_for_timeout(120)
    check("copy button confirms", page.inner_text(".row .copy").strip().lower() == "copied",
          page.inner_text(".row .copy"))

    # count field
    page.fill("#count", "12")
    page.dispatch_event("#count", "change")
    page.wait_for_timeout(150)
    check("count field drives row count",
          page.eval_on_selector_all(".row", "e => e.length") == 12)

    page.fill("#count", "6")
    page.dispatch_event("#count", "change")
    page.wait_for_timeout(150)
    page.screenshot(path=SHOT, full_page=True)
    check("no console or page errors", not errors, " | ".join(errors[:3]))
    browser.close()

print("\n" + ("ALL CHECKS PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
