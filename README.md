# voiceprint

Make Claude write like you, not like Claude. voiceprint reads your own posts, PR descriptions and messages, measures how you actually write, and turns that into a profile Claude drafts with. A small hook then checks anything Claude is about to post for you and flags words you never use.

Your voice stays yours: the corpus, profile and baseline are stored in `~/.voiceprint/` on your machine (or `VOICEPRINT_HOME`), never in this repo or anywhere else. Building the profile does pass samples through Claude, like anything else you show it, so `/voiceprint:voice-init` asks before it reads each source.

## Install

```bash
claude plugin marketplace add NahumLitvin/voiceprint && claude plugin install voiceprint@voiceprint
```

## Use

| Command | What it does |
|---|---|
| `/voiceprint:voice-init` | Finds where you write (blog, LinkedIn, Reddit, HN, GitHub, Slack, Telegram, WhatsApp, your Claude Code prompts), asks which to use, collects all of your own text back to the oldest message each source holds, measures it, and writes `~/.voiceprint/profile.md` with you |
| `/voiceprint:voice` | Drafts in your voice and scores the draft before showing it |
| the hook | Runs before `gh pr/issue create, comment, edit, review`, `git commit` and Slack sends, scheduled messages and canvas create/update tools. Drafts are excluded. When the text scores above your own writing, it asks you before sending |

## How the guard scores

It looks for words and phrases that mark machine-written English: the 2023 vocabulary (`delve`, `seamless`, `it's not just X`, em dashes) and the words that suddenly spread in AI-written PRs in 2025 and 2026 (`load-bearing`, `quietly`, `genuinely`, `carve-out`), from the [load-bearing study](https://louisabraham.github.io/load-bearing/) of 461,121 GitHub PR texts. Each tell gets an allowance of twice your own rate, scaled to the draft's word count, plus one occurrence if your rate is at least 0.5 per 1,000 words. The allowance stays fractional, so short drafts keep that allowance while repetition still counts. If you also give it text from after you started using AI tools, it learns your own drift: words that became much more frequent in your later writing, which then count like tells (`build ... --recent DIR`). Any dash asks when you never use dashes. Words in any script count, so Hebrew or Arabic messages are measured too. Only the three biggest hits count, per 100 words with a floor of 100 words, so a long text isn't flagged for being long. The warn line is the 95th percentile of your own texts, at least 2; the deny line is 1.5 times your 99th percentile, at least 3.

Long form uses `VOICEPRINT_HOME/baseline.json`; chat uses `VOICEPRINT_HOME/chat/baseline.json`. Slack sends use the chat baseline when valid, falling back to the default. GitHub and git use the default. The shared `profile.md` contains both registers.

By default the hook asks you, with the score and the words, before the send runs. To block sends over the deny line instead (needs 5+ calibration texts of 25+ words), or to only tell Claude without asking:

```bash
export VOICEPRINT_MODE=deny   # or: note
```

You can add `voice-ok` to a text, outside code, to let it through when a flagged term is needed. Claude is asked to rewrite flagged words in your voice; if a term is needed, it leaves it for you to approve. Texts under 25 words and code blocks are skipped. Mode comes only from `VOICEPRINT_MODE`, defaulting to `ask`.

The hook reads UTF-8, replacing invalid bytes. Invalid baselines are ignored; unexpected hook errors produce no output. Shell commands over 200,000 characters are skipped.

The hook is a writing check, not a security boundary. It reads the command as text and never runs it, so a body that comes from a shell variable, a wrapper such as `timeout`, or `gh api` is not seen, and neither are `gh pr merge --body`, `git tag -m` or `git merge -m`. Use `/voiceprint:voice` for anything you paste yourself.

## Without Claude Code

```bash
python3 scripts/voiceprint.py build ~/my-posts
python3 scripts/voiceprint.py score - < ~/.voiceprint/draft.md
```

`build` writes only the measured baseline; the written profile comes from `/voiceprint:voice-init`. It accepts `.md`, `.txt` and `.markdown` in any casing, skips files over 5 MB, strips quoted replies and reply/forward tails, and warns for missing or empty source paths. An empty corpus or missing score file reports an error without a traceback. Use `--lines` for chat and set `VOICEPRINT_HOME` to your default home's `chat` subfolder when building or scoring that register. Keep draft files under your voiceprint home, or pipe text into `score -`.

Python 3.8+, standard library only, macOS, Linux and Windows (the hook needs `python3` on PATH). `python3 scripts/voiceprint.py selftest` runs the checks.



## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues privately, see [SECURITY.md](SECURITY.md).

MIT license.
