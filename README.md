# voiceprint

Make Claude write like you, not like Claude. voiceprint reads your own posts, PR descriptions and messages, measures how you actually write, and turns that into a profile Claude drafts with. A small hook then checks anything Claude is about to post for you and flags words you never use.

Your voice stays yours: the corpus, profile and baseline live in `~/.voiceprint/` on your machine and are never shared.

## Install

```bash
claude plugin marketplace add NahumLitvin/voiceprint && claude plugin install voiceprint@voiceprint
```

## Use

| Command | What it does |
|---|---|
| `/voice-init` | Collects your writing (blog, LinkedIn export, your GitHub PRs, chat exports), measures it, and writes `~/.voiceprint/profile.md` with you |
| `/voice` | Drafts in your voice and scores the draft before showing it |
| the hook | Runs before `gh pr/issue create, comment, edit, review`, `git commit` and Slack tools. Warns when the text scores above your own writing |

## How the guard scores

It counts words and phrases that mark machine-written English per 100 words: the 2023 vocabulary (`delve`, `seamless`, `it's not just X`, em dashes) and the words that suddenly spread in AI-written PRs in 2025 and 2026 (`load-bearing`, `quietly`, `genuinely`, `carve-out`), from the [load-bearing study](https://louisabraham.github.io/load-bearing/) of 461,121 GitHub PR texts. Any word you use in your own writing is dropped from the list, so your habits never count against you. The warn line is the 95th percentile of your own texts; the deny line is 1.5 times your worst one.

Default is warn only. To block sends over the deny line:

```bash
export VOICEPRINT_MODE=deny
```

Put `voice-ok` in a text to let it through when a flagged word is unavoidable. Texts under 25 words and code blocks are skipped.

## Without Claude Code

```bash
python3 scripts/voiceprint.py build ~/my-posts && python3 scripts/voiceprint.py score draft.md
```

Python 3.8+, standard library only. `python3 scripts/voiceprint.py selftest` runs the checks.

MIT license.
