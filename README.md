# Password Generator

Readable passwords you can actually type from memory:

```
f!reFox99      m!ltonHome604   longTr@ck77
crunchySn@ck82 blueGr!p43      h@ppyPlace44
```

Every password is a modifier + noun camelCase phrase, one letter swapped for its symbol
twin (`a`→`@`, `i`→`!`, `o`→`0`, `e`→`3`, `s`→`$`), then two to four digits.

**Live site:** https://abhinavmanocha.github.io/password-gen/

## What's here

| Path | What it is |
|------|------------|
| `index.html` | The whole web app — one self-contained file, no build step, no dependencies |
| `gen.py` | Command-line version, same generator |
| `manifest.json`, `icons/` | PWA manifest + icons, so the site installs to a phone home screen |
| `tools/make_icons.py` | Redraws the PNG icons and the Android launcher mipmaps (needs Pillow) |
| `mobile/` | Capacitor project used to build the Android APK (gitignored) |

Everything runs on the device — no network calls, nothing is stored or sent anywhere.

## CLI

```bash
python gen.py                 # 10 passwords
python gen.py -n 5 -w 3 -d 3  # 5 longer, stronger ones
python gen.py --mixed --bits  # randomised digit count + strength estimate
```

## Strength, honestly

The two-word default lands around **21 bits** from word choice, plus a few more for the symbol
swap — roughly 25 bits. That is fine for Wi-Fi, streaming logins and anything that rate-limits
guessing, and it is *not* enough for email, banking or a password-manager master password.
Switch to 3 or 4 words there: three words is ~32 bits, four is ~39, and a longer master password
should get extra length on top of that.

## How it was built

`index.html` is the source of truth for the web app and the APK. The APK is produced by copying
`index.html`, `manifest.json` and `icons/` into `mobile/www/` and building with Capacitor:

```bash
cd mobile
./sync-web.sh          # copy the web files into www/
npx cap sync android
cd android && ./gradlew assembleRelease
```

## License

MIT — do whatever you like with it.
