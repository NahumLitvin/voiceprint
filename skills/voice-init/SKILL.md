---
name: voice-init
description: Build the user's own writing voice from their own publications and messages - a measured fingerprint plus a profile Claude writes with, and the baseline the voiceprint prose guard scores against. Use for "build my voice", "learn how I write", "set up voiceprint", "refresh my voice", "/voice-init".
---

# voice-init

Builds the user's voice from text they wrote. Everything stays on their machine in `~/.voiceprint/` (or `$VOICEPRINT_HOME`). Never upload, commit or quote the corpus anywhere else.

## 1. Collect their writing

Ask which sources they want, then save each as plain text under `~/.voiceprint/corpus/<source>/`. Only text the user wrote themselves. Skip anything quoted, pasted or AI-drafted they can point to.

| Source | How |
|---|---|
| Blog, Medium, dev.to | Fetch each post they name (or the RSS feed), save the body as one `.md` per post |
| LinkedIn | Their data export (Settings, Data privacy, Get a copy) has `Shares.csv`; save one post per file |
| GitHub | `gh search prs --author=@me --limit 200 --json body --jq '.[].body'`, one file per body, drop bot templates |
| Chat (Slack, WhatsApp, Discord export) | Their own messages only, one message per line in a `.txt` |
| Anything else | A folder of `.md` or `.txt` they point to |

Keep long-form and chat in separate folders: they are different registers.

## 2. Measure

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/voiceprint.py" build ~/.voiceprint/corpus/posts ~/.voiceprint/corpus/prs
```

For a chat folder add `--lines` and build it separately into its own home, for example `VOICEPRINT_HOME=~/.voiceprint/chat`. The output is `baseline.json`: sentence lengths, short-message share, dash, emoji, contraction and sign-off rates, which AI-tell words they actually use, and the warn and deny lines the guard uses.

## 3. Write the profile

Read 20 to 30 samples across sources, then write `~/.voiceprint/profile.md` with these sections, each backed by numbers from `baseline.json` or quotes from the samples:

- **Rhythm**: sentence and message length, how paragraphs open and close.
- **Punctuation and marks**: what they use and what they never use (dashes, `!`, emoji, lowercase starts).
- **Words**: phrases they reach for, words they never write, how they swear or joke.
- **Structure**: how a post opens (story, number, claim), how it ends, lists or none.
- **Per medium**: how chat differs from long form.
- **Never**: the things that would make a reader say "this isn't them".

Show the profile to the user and fix what they say is wrong. Their correction beats the numbers.

## 4. Refresh

Rerun step 2 when they publish more. The guard reads the new baseline at once.
