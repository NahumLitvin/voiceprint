---
name: voice-init
description: Build the user's own writing voice from their own publications and messages - a measured fingerprint plus a profile Claude writes with, and the baseline the voiceprint prose guard scores against. Use for "build my voice", "learn how I write", "set up voiceprint", "refresh my voice", "/voice-init".
---

# voice-init

Builds the user's voice from text they wrote. Everything stays on their machine in `~/.voiceprint/` (or `$VOICEPRINT_HOME`). Never upload, commit or quote the corpus anywhere else.

## 1. Find sources, ask, then collect

First look at what this machine can reach, without reading any content yet: connected MCP tools (Slack, Gmail, Telegram, WhatsApp, Discord, Notion), CLIs on PATH (`gh`, a session-search tool such as `recall`), Claude Code transcripts in `~/.claude/projects/`, and export files the user mentions. Ask for their handles on public sites.

Show the user one menu of what you found and what each would collect, and get an explicit yes per source. Collect nothing they did not approve.

Rules for every source:
- Only text the user wrote. Never save other people's messages, even from a chat they were in.
- Skip what they pasted or had AI draft, when they can point to it.
- Save plain text under `~/.voiceprint/corpus/<source>/`: one `.md` per post for long form, one message per line in a `.txt` for chat.

| Source | How |
|---|---|
| Claude Code prompts | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/voiceprint.py" claude-prompts > ~/.voiceprint/corpus/claude/prompts.txt` (their most casual register) |
| Past sessions | If a session-search CLI like `recall` is installed, search their own messages with it |
| Blog, Medium, dev.to, Substack | The posts they name or the RSS feed; dev.to has `https://dev.to/api/articles?username=<name>` |
| LinkedIn | Their data export (Settings, Data privacy, Get a copy of your data) has `Shares.csv` and `Comments.csv` |
| Reddit | `https://www.reddit.com/user/<name>/comments.json?limit=100` and `submitted.json`, paging with `after` |
| Hacker News | `https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_<name>&hitsPerPage=1000` |
| X / Twitter | Their archive's `data/tweets.js`, without retweets |
| Bluesky, Mastodon | Their public author feed through the site's API |
| GitHub | `gh search prs --author=@me --limit 200 --json body --jq '.[].body'`, plus issue comments; drop bot templates |
| Slack, Gmail, Notion | The connected MCP tool, searching only what they sent (`from:me`, Sent mail) |
| Telegram | Telegram Desktop, Export chat history, JSON; keep messages whose `from_id` is theirs, or use the MCP tool if connected |
| WhatsApp | The chat export `.txt`, or the MCP tool if connected; keep only their lines |
| Discord | Their data package, `messages/*/messages.json` |
| Anything else | A folder of `.md` or `.txt` they point to |

Keep long form and chat in separate folders: they are different registers. Some sources are work data. Ask before mixing work chat into a voice they will use for personal writing.

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
