# Contributing

Bug reports, new sources for `/voiceprint:voice-init`, tell words and fixes are welcome.

## Layout

| Path | What |
|---|---|
| `scripts/voiceprint.py` | Everything that runs: `build`, `score`, `claude-prompts`, `hook`, `selftest`. One file, standard library only, Python 3.8+ |
| `skills/voice-init/SKILL.md` | How Claude finds sources, asks, collects and writes the profile |
| `skills/voice/SKILL.md` | How Claude drafts in the user's voice and scores the draft |
| `hooks/hooks.json` | The PreToolUse hook registration |

## Before a pull request

```bash
python3 scripts/voiceprint.py selftest
```

- A bug fix adds a check to `selftest()` that fails without the fix.
- Keep it standard library only, and working on macOS, Linux and Windows. CI runs the self-test on all three.
- Keep README and both skills consistent with code. Long-form baselines live in `VOICEPRINT_HOME`, chat in its `chat` subfolder; Slack falls back to the default when the chat baseline is absent or invalid. Mode comes only from `VOICEPRINT_MODE`.
- Read text as UTF-8 with replacement for invalid bytes. Keep hook failures silent, corpus files capped at 5 MB and shell commands capped at 200,000 characters.
- Strip quoted replies and forwarded text from corpus sources. Drafts and collected text belong under the voiceprint home, never in the user's repo.
- A new tell word needs a public source showing it rose in machine-written text, linked in the PR. Plain English words are fine, since the user's own rate is allowed, but say why the word belongs.
- A new collection source goes in the voice-init table: where the user's own text lives, how to keep only their messages, and whether it needs an export or a connected tool.

## Never commit

- Anyone's real writing: no corpus, profile or baseline, yours included. Tests use made-up text.
- Messages from other people, even as test fixtures.

## Security

Report vulnerabilities privately, see [SECURITY.md](SECURITY.md).
