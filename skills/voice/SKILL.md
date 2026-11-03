---
name: voice
description: Write in the user's own voice using the profile built by voice-init, then check the draft with their prose guard before showing it. Use for any prose a person will read - posts, emails, PR descriptions, Slack or chat replies - and for "sounds like AI", "make it sound like me", "humanize this".
---

# voice

1. Read `${VOICEPRINT_HOME:-~/.voiceprint}/profile.md`. If it does not exist, say so and offer `/voiceprint:voice-init`. Do not invent a voice.
2. Draft for the medium: chat follows the chat section (length, casing, typos left alone), long form follows the long-form one.
3. Score it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/voiceprint.py" score draft.md
```

4. If the score is at or over `warn_at`, rewrite each listed word or dash the way the profile says they would put it, and score again, at most twice. Do not swap one listed word for another. A term the topic needs (a product called Ecosystem, a real asymmetry) stays; tell the user it is why the score is high.
5. Show the draft with its score. Never send it on the user's behalf without their go.

A text the user pastes themselves passes no hook, so step 3 is the only check it gets.
