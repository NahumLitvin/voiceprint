---
name: voice
description: Write in the user's own voice using the profile built by voice-init, then check the draft with their prose guard before showing it. Use for any prose a person will read - posts, emails, PR descriptions, Slack or chat replies - and for "sounds like AI", "make it sound like me", "humanize this".
---

# voice

1. Read `${VOICEPRINT_HOME:-$HOME/.voiceprint}/profile.md`, including its chat section. If it does not exist, say so and offer `/voiceprint:voice-init`. Do not invent a voice.
2. Draft for the medium: chat follows the chat section (length, casing, typos left alone), long form follows the long-form one.
3. Score via stdin (use `python` where the commands say `python3` if only that exists), or a file under `${VOICEPRINT_HOME:-$HOME/.voiceprint}`. Never create a draft file in the user's repo:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/voiceprint.py" score - <<'DRAFT'
The draft goes here.
DRAFT
```

For chat, use `VOICEPRINT_HOME="${VOICEPRINT_HOME:-$HOME/.voiceprint}/chat"` on the score command if that folder contains a valid baseline; otherwise use the default home. The profile always comes from the default home.

4. If the score is at or over `warn_at`, rewrite each listed word or dash the way the profile says they would put it, and score again, at most twice. Do not swap one listed word for another. A term the topic needs (a product called Ecosystem, a real asymmetry) stays; tell the user it is why the score is high.
5. Show the draft with its score. Never send it on the user's behalf without their go.

A text the user pastes themselves passes no hook, so step 3 is the only check it gets.
