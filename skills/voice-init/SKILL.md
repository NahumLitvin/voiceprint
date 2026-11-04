---
name: voice-init
description: Build the user's own writing voice from their own publications and messages - a measured fingerprint plus a profile Claude writes with, and the baseline the voiceprint prose guard scores against. Use for "build my voice", "learn how I write", "set up voiceprint", "refresh my voice", "/voice-init".
---

# voice-init

Builds the user's voice from text they wrote. Files are stored in `${VOICEPRINT_HOME:-$HOME/.voiceprint}`. Never upload, commit or quote the corpus anywhere else. Tell the user up front that samples you read pass through this conversation, then start with `mkdir -p "${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus"`.

## 1. Find sources, ask, then collect everything

The more of their own writing, and the older, the better: old text shows the voice before AI tools, and drift needs 5,000+ words of it. So the goal is every message and post they ever wrote, back to the oldest one a source holds.

**Discover.** With one permission to look, list what this machine can reach, reading metadata only (counts, oldest and newest date), no content: connected MCP tools (Slack, Gmail, Telegram, WhatsApp, Discord, Notion), CLIs on PATH (`gh`, `gws`, a session-search tool such as `recall`), local app databases and backups from the table, Claude Code transcripts in `~/.claude/projects/`, and export files. Ask for their handles on public sites and for blogs they ever had, including dead ones.

**Ask.** Show one menu: each source, how many of their messages it holds and how far back it goes. Get an explicit yes per source. A yes means the full history of that source, unless they set a limit or exclude chats or people. Collect nothing they did not approve. Ask before mixing work chat into a voice for personal writing.

**Collect all of it.** Page until the source is empty, not until you have "enough". Where an API caps results per query (Slack search, Gmail), split by date (month by month, then year by year) back to the oldest message. Include replies: thread replies, email answers, comments. When a source's history ends, say whether that is where their writing starts or where the tool stops (a free Slack plan hides old messages, an MCP only holds what it synced), and offer the full export for the rest.

**Preview.** Before measuring, show a few lines from each source and each era so they can drop what isn't theirs (quotes, forwarded mail, pasted AI text, secrets).

Rules for every source:
- Only text the user wrote. Never save other people's messages, even from a chat they were in.
- Skip what they pasted or had AI draft, when they can point to it. In chat, drop forwarded and pasted text: messages marked forwarded, multi-paragraph blocks, lines with dashes or bullets they never type, and anything far longer than their usual message.
- Save plain text under `${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus/<source>/`, one file per year (`2016.txt`, or `2016-<slug>.md` per post), so eras can be split later: one `.md` per post for long form, one message per line in a `.txt` for chat. Keep each file under 5 MB.
- For any email source, strip quoted replies and forwarded text before saving. Keep only the user's new text, even when the quoted text was originally theirs.

| Source | How to get the full history |
|---|---|
| Claude Code prompts | `mkdir -p "${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus/claude" && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/voiceprint.py" claude-prompts > "${VOICEPRINT_HOME:-$HOME/.voiceprint}/corpus/claude/prompts.txt"` (their most casual register; the collector drops prompts that look pasted, such as code, quotes, long lines and multi-line blocks, but not all of them, so preview it) |
| Past sessions | If a session-search CLI like `recall` is installed, search their own messages with it |
| WhatsApp, full history | The phone holds every year; desktop apps only hold what synced since they were linked. On iPhone, make a Finder backup of the phone (unencrypted, or decrypt it), find `ChatStorage.sqlite` (domain `AppDomainGroup-group.net.whatsapp.WhatsApp.shared` in the backup's `Manifest.db`) and read it read-only: `sqlite3 "file:<path>?mode=ro" "select strftime('%Y', ZMESSAGEDATE + 978307200, 'unixepoch'), replace(ZTEXT, char(10), ' ') from ZWAMESSAGE where ZISFROMME = 1 and ZTEXT is not null"`, one file per year. The Mac app keeps the same database at `~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`; check its oldest `ZISFROMME = 1` date before relying on it. On Android the local backup is encrypted, so use Export chat per chat (without media) for their busiest chats |
| WhatsApp, recent | The MCP tool if connected; keep only their lines |
| Slack | Search `from:me` with the connected tool, one month per query from today back to the workspace start, paging every month to the end; search results include thread replies. A workspace export has everything if they are an admin |
| Gmail and other email | All sent mail: `in:sent` with the connected tool or `gws`, one year per query back to the account's first message, or a Google Takeout mbox. Strip quoted replies and forwarded text, then preview |
| Blog, Medium, dev.to, Substack | Every post: RSS, the site's API (dev.to `https://dev.to/api/articles?username=<name>&per_page=1000`), Medium's export. For blogs that are gone, the Wayback Machine (`https://web.archive.org/cdx/search/cdx?url=<domain>/*&output=json&filter=statuscode:200`) |
| LinkedIn | Their data export (Settings, Data privacy, Get a copy of your data): `Shares.csv`, `Comments.csv` and the `Articles` folder |
| Reddit | `https://www.reddit.com/user/<name>/comments.json?limit=100` and `submitted.json`, paging with `after` until it stops (Reddit returns about 1,000 items; their data request has all) |
| Hacker News | `https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_<name>&hitsPerPage=1000`, paging with `numericFilters=created_at_i<<oldest>` |
| X / Twitter | Their archive's `data/tweets.js`, without retweets |
| Bluesky, Mastodon | Their public author feed through the site's API, paging with the cursor to the first post |
| GitHub | PR bodies are often AI-written. Ask for a cutoff date before they used AI writing tools, then search all their PRs and issue comments with `gh`, year by year. Drop bot templates and templated bodies: mostly headings like `## Summary`, `## Test plan`, checkboxes or a tool's footer, even when old. Include only text they confirm they wrote |
| Notion | The connected tool, pages they created |
| Telegram | Telegram Desktop, Export chat history, JSON; keep messages whose `from_id` is theirs, or use the MCP tool if connected |
| Discord | Their data package, `messages/*/messages.json` |
| Anything else | A folder of `.md` or `.txt` they point to: old documents, school or university work, forum posts |

Keep long form and chat in separate folders: they are different registers. Long-form files dated after their AI cutoff go in `corpus/recent/` (see Drift).

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
