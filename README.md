# voiceprint

Make Claude write like you, not like Claude. voiceprint reads your own posts, PR descriptions and messages, measures how you actually write, and turns that into a profile Claude drafts with. A small hook then checks anything Claude is about to post for you and flags words you never use.

Your voice stays yours: the corpus, profile and baseline are stored in `~/.voiceprint/` on your machine, never in this repo or anywhere else. Building the profile does pass samples through Claude, like anything else you show it, so `/voiceprint:voice-init` asks before it reads each source.

## Install

```bash
claude plugin marketplace add NahumLitvin/voiceprint && claude plugin install voiceprint@voiceprint
```

## Use

| Command | What it does |
|---|---|
| `/voiceprint:voice-init` | Finds where you write (blog, LinkedIn, Reddit, HN, GitHub, Slack, Telegram, WhatsApp, your Claude Code prompts), asks which to use, collects only your own text, measures it, and writes `~/.voiceprint/profile.md` with you |
| `/voiceprint:voice` | Drafts in your voice and scores the draft before showing it |
| the hook | Runs before `gh pr/issue create, comment, edit, review`, `git commit` and Slack tools. When the text scores above your own writing, it asks you before sending |

## How the guard scores

It counts words and phrases that mark machine-written English per 100 words: the 2023 vocabulary (`delve`, `seamless`, `it's not just X`, em dashes) and the words that suddenly spread in AI-written PRs in 2025 and 2026 (`load-bearing`, `quietly`, `genuinely`, `carve-out`), from the [load-bearing study](https://louisabraham.github.io/load-bearing/) of 461,121 GitHub PR texts. Any word you use in your own writing is dropped from the list, so your habits never count against you. The warn line is the 95th percentile of your own texts; the deny line is 1.5 times your worst one.

By default the hook asks you, with the score and the words, before the send runs. To block sends over the deny line instead (needs 5+ calibration texts of 25+ words), or to only tell Claude without asking:

```bash
export VOICEPRINT_MODE=deny   # or: note
```

Put `voice-ok` in a text, outside code, to let it through when a flagged term is needed. Texts under 25 words and code blocks are skipped.

## Without Claude Code

```bash
python3 scripts/voiceprint.py build ~/my-posts && python3 scripts/voiceprint.py score draft.md
```

`build` writes only the measured baseline; the written profile comes from `/voiceprint:voice-init`.

Python 3.8+, standard library only, macOS, Linux and Windows (the hook needs `python3` on PATH). `python3 scripts/voiceprint.py selftest` runs the checks.



## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues privately, see [SECURITY.md](SECURITY.md).

MIT license.
