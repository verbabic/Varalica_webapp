# Varalica localization audit

Read-only inventory of user-visible text. Application code, game data, tests, and the Excel workbook were not modified.

Catalog: `docs/localization/VARALICA_UI_TRANSLATION_INVENTORY.csv`

Total catalog entries: **263**. Each key is unique. Status is `PENDING_REVIEW`. `translation_sr` and `translation_de` are blank. `translation_hr` is filled only when the current source string is already Croatian wording taken from the code.

## Counts by source file

| Source | Entries |
| --- | ---: |
| `static/app.js` | 132 |
| `main.py` | 63 |
| `static/index.html` | 47 |
| `words.py` | 15 |
| Image assets flagged for visual review | 6 |

## Counts by section

| Section | Entries |
| --- | ---: |
| api_errors | 55 |
| results | 37 |
| lobby | 20 |
| reveal | 19 |
| voting | 16 |
| data | 15 |
| rules | 14 |
| a11y | 11 |
| errors | 11 |
| confirm | 9 |
| discussion | 9 |
| setup | 7 |
| status | 7 |
| assets | 6 |
| host | 5 |
| toast | 5 |
| players | 4 |
| chat | 3 |
| system | 3 |
| navigation | 2 |
| mode | 2 |
| meta | 1 |
| brand | 1 |
| overtime | 1 |

Screens with the most entries: API responses (55), results (31), room chrome (30), lobby (26), discussion (18), private card (16), home (17), rules modal (13), voting (11).

## Verified user-facing content

Included when a string is rendered in HTML, set as a button, label, placeholder, `aria-label`, `title`, toast, confirm dialog, rules paragraph, or returned to the client as `detail`, `message`, `spectator_message`, or `outcome`.

The full rules modal text from `static/index.html` lines 122–133 is cataloged as twelve separate entries, without summarization.

CSS `content` values in `static/styles.css` are empty decorative strings and are not cataloged.

## Uncertain candidates

- Mixed Croatian and Serbian spelling in one sentence, for example `Da li zelis prenijeti hosta` and `Glasanje je nerešeno` next to `Glasanje je neriješeno`. These are separate keys because the wording differs.
- English UI that is still shown to players: `Live`, `Chat`, `Lobby`, `Host`, `Host panel`, `Cancel`, `Stable`, `Reconnecting`, `Disconnected`, `Active`, `Away`, `Idle`, `Offline`, `Mini scoreboard`, `QR`, `Username`.
- `source_language=mixed` means the current sentence is not consistently one language. It is not a translation.

## Not expanded

- `words.py` `STARTER_WORDS` is a content corpus, not interface chrome. One catalog row, `data.word_corpus`, records that each entry has `hr`, `sr`, and `hint_pool`, with `hint_hr`, `hint_sr`, and `hint_de` prepared in code but not regenerated into the file. Individual secret words and hints are not copied into this UI catalog.
- Category labels from `WORD_CATEGORIES` are included because they appear in the lobby select.
- Painted text inside `Landing.png`, the private-card PNGs, the countdown PNG, and the result-scene PNGs was not OCR-extracted. Six asset rows flag those files for a separate visual review.
- Player names, room codes, avatars, vote counts, and emoji reactions are runtime data, not translatable copy.

## Strings that cannot be safely extracted as one static sentence

- Duration options are built as `{seconds}/60 + " min"`.
- Final-discussion and discussion timers are numeric.
- Result lines interpolate the localized word, player names, and vote totals.
- API `detail` text is shown through `showError(data.detail)`.
- The secret hint is chosen on the server and rendered by `localizedHint()`.

## Language architecture

- The interface has no language switcher. `static/app.js` uses `UI_LANGUAGE = "hr"` only to choose `word.hr` or `word.sr` and `hint_hr` or `hint_sr` when those fields exist.
- The server does not trust a client language. `GAME_LANGUAGE` in `main.py` is the constant `"hr"`.
- The Excel workbook columns are `category_key`, `word_sr`, `hint_sr`, `word_hr`, `hint_hr`, `word_de`, `hint_de`.
- The importer can keep those hint lists separate. The running `words.py` file was not regenerated, so current records still use `hint_pool`.
- Legacy pools are interpreted as Croatian first and Serbian second. A single pool item is treated as the shared hint kept when both languages were identical.
- A missing hint for the active language becomes `Smjernica nije dostupna na odabranom jeziku.` It is not replaced from another language.
- The Varalica private payload does not include the secret word. The normal player payload does include `hr` and `sr`; the Croatian screen displays `hr` only.

## Language-mixing and secrecy risks

- Many interface strings are already a mix of Croatian, Serbian, and English. Translating only new screens would leave that mix in place.
- Two tie sentences differ only by `nerešeno` versus `neriješeno`. They need separate review.
- Public results intentionally reveal the word after the round. That string must stay out of the Varalica view before results.
- Image assets may still show Croatian or Serbian words that the UI catalog cannot change.

## Recommended review workflow

1. Review this catalog in Excel. Do not change `key`, `source_text`, or `source_line`.
2. Fill `translation_sr` and `translation_de`. Adjust `translation_hr` only where the current wording should change.
3. Keep placeholders such as `{player_name}`, `{seconds}`, `{mode}`, and `{count}` unchanged.
4. Approve category labels and then decide whether the word corpus is a separate content project.
5. Review the six image assets visually before any art replacement.
6. Only after copy approval should a later task add a language model and replace the source strings.

## Confirmation

This audit created only:

- `docs/localization/VARALICA_UI_TRANSLATION_INVENTORY.csv`
- `docs/localization/VARALICA_LOCALIZATION_AUDIT.md`

No application source, game data, configuration, dependency, or existing test was modified for this inventory. The temporary generator used to write the CSV was removed. Nothing was committed, pushed, or deployed.
