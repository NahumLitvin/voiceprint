---
name: voice-init
description: Build the user's own writing voice from their own publications and messages - a measured fingerprint plus a profile Claude writes with, and the baseline the voiceprint prose guard scores against. Use for "build my voice", "learn how I write", "set up voiceprint", "refresh my voice", "/voice-init".
---

# voice-init

Builds the user's voice from text they wrote. Files are stored in `${VOICEPRINT_HOME:-$HOME/.voiceprint}`. Never upload, commit or quote the corpus anywhere else. Tell the user up front that samples you read pass through this conversation, then start with `mkdir -p "${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus"`.

## 1. Find sources, ask, then collect

First look at what this machine can reach, without reading any content yet: connected MCP tools (Slack, Gmail, Telegram, WhatsApp, Discord, Notion), CLIs on PATH (`gh`, a session-search tool such as `recall`), Claude Code transcripts in `~/.claude/projects/`, and export files the user mentions. Ask for their handles on public sites.

Show the user one menu of what you found and what each would collect, and get an explicit yes per source. Collect nothing they did not approve. Before measuring, show a few lines from each source so they can drop what isn't theirs (quotes, forwarded mail, pasted AI text, secrets).

Rules for every source:
- Only text the user wrote. Never save other people's messages, even from a chat they were in.
- Skip what they pasted or had AI draft, when they can point to it. In chat, drop forwarded and pasted text: messages marked forwarded, multi-paragraph blocks, lines with dashes or bullets they never type, and anything far longer than their usual message.
- Save plain text under `${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus/<source>/` (create the folder first): one `.md` per post for long form, one message per line in a `.txt` for chat.
- For any email source, strip quoted replies and forwarded text before saving. Keep only the user's new text, even when the quoted text was originally theirs.

| Source | How |
|---|---|
| Claude Code prompts | `mkdir -p "${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus/claude" && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/voiceprint.py" claude-prompts > "${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus/claude/prompts.txt"` (their most casual register; the collector drops prompts that look pasted, such as code, quotes, long lines and multi-line blocks, but not all of them, so preview it) |
| Past sessions | If a session-search CLI like `recall` is installed, search their own messages with it |
| Blog, Medium, dev.to, Substack | The posts they name or the RSS feed; dev.to has `https://dev.to/api/articles?username=<name>` |
| LinkedIn | Their data export (Settings, Data privacy, Get a copy of your data) has `Shares.csv` and `Comments.csv` |
| Reddit | `https://www.reddit.com/user/<name>/comments.json?limit=100` and `submitted.json`, paging with `after` |
| Hacker News | `https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_<name>&hitsPerPage=1000` |
| X / Twitter | Their archive's `data/tweets.js`, without retweets |
| Bluesky, Mastodon | Their public author feed through the site's API |
| GitHub | PR bodies are often AI-written. Ask for a cutoff date before they used AI writing tools, then search their PRs before that date with `gh` and preview the bodies with them. Drop bot templates and templated bodies: mostly headings like `## Summary`, `## Test plan`, checkboxes or a tool's footer, even when old, since templated AI text scores low. Include only text they confirm they wrote. Apply the same checks to issue comments. |
| Slack, Notion | The connected MCP tool, searching only what they sent (`from:me`) |
| Gmail and other email | The connected tool or a Sent mail export, keeping only what they sent. Strip quoted replies and forwarded text before saving, then preview the remaining text. |
| Telegram | Telegram Desktop, Export chat history, JSON; keep messages whose `from_id` is theirs, or use the MCP tool if connected |
| WhatsApp | The chat export `.txt`, or the MCP tool if connected; keep only their lines |
| Discord | Their data package, `messages/*/messages.json` |
| Anything else | A folder of `.md` or `.txt` they point to |

Keep long form and chat in separate folders: they are different registers. Some sources are work data. Ask before mixing work chat into a voice they will use for personal writing.

## 2. Measure

Use a separate top-level source folder for each register. Chat folder names are `claude` (Claude prompts), `slack`, `whatsapp`, `telegram` and `discord`. Build every other folder into the default baseline. This command discovers all source folders, including any long-form sources beyond posts and PRs:

```bash
python3 - <<'PY'
import os
from pathlib import Path
import subprocess
import sys

home = Path(os.path.expanduser(os.environ.get("VOICEPRINT_HOME") or "~/.voiceprint"))
script = Path("${CLAUDE_PLUGIN_ROOT}") / "scripts" / "voiceprint.py"
chat_names = {"claude", "claude-prompts", "slack", "whatsapp", "telegram", "discord"}
folders = sorted(p for p in (home / "corpus").iterdir() if p.is_dir() and p.name != "recent")
recent = home / "corpus" / "recent"
for chat in (False, True):
    sources = [str(p) for p in folders if (p.name.lower() in chat_names) == chat]
    if sources:
        env = dict(os.environ, VOICEPRINT_HOME=str(home / "chat" if chat else home))
        extra = ["--lines"] if chat else (["--recent", str(recent)] if recent.is_dir() else [])
        subprocess.run([sys.executable, str(script), "build", *sources] + extra,
                       env=env, check=True)
PY
```

The outputs are `${VOICEPRINT_HOME:-$HOME/.voiceprint}/baseline.json` for long form and `${VOICEPRINT_HOME:-$HOME/.voiceprint}/chat/baseline.json` for chat, built with `--lines`. Each measures sentence lengths, short-message share, dash, emoji, contraction and sign-off rates, which AI-tell words they actually use, and the warn and deny lines. Files over 5 MB are skipped with a warning. `.md`, `.txt` and `.markdown` extensions are case-insensitive. The builder also strips quoted replies and reply/forward tails.

Slack sends use the chat baseline when available, otherwise the default. GitHub and git sends use the default baseline.

**Drift.** Text the user wrote after they started using AI tools (posts, PR bodies, long messages after their cutoff date) goes in `corpus/recent/`, not in the voice corpus. The long-form build compares it with their earlier writing and stores the words that became much more frequent as `drift` in `baseline.json`: their personal AI tells. Show the list. Topic words (a product they started working on, a new tool) are not tells: remove them from `drift` in the JSON with the user before moving on. Under 5,000 words of earlier writing, `build` skips drift and says so (`drift_note`): ordinary words would look like drift. Tell the user and offer to add more earlier writing (old email, posts) instead.

## 3. Write the profile

Read 20 to 30 long-form samples across sources. For chat, read whole threads, not corpus lines: 5 to 10 conversations of about 30 consecutive messages from the source (MCP tool or export), so turn-level habits show up: messages sent in bursts, how they greet and sign off, how they escalate or push back, humor, how they introduce themselves to strangers, slang per language. Quote only their own lines. Then write `${VOICEPRINT_HOME:-$HOME/.voiceprint}/profile.md` with these sections, each backed by numbers from the two baselines or quotes from the samples:

- **Rhythm**: sentence and message length, how paragraphs open and close.
- **Punctuation and marks**: what they use and what they never use (dashes, `!`, emoji, lowercase starts).
- **Words**: phrases they reach for, words they never write, how they swear or joke.
- **Structure**: how a post opens (story, number, claim), how it ends, lists or none.
- **Per medium**: separate chat and long-form sections, including how they differ.
- **Never**: the things that would make a reader say "this isn't them".

Show the profile to the user and fix what they say is wrong. Their correction beats the numbers.

## 4. Refresh

Rerun step 2 when they publish more. The guard reads the new baseline at once.
