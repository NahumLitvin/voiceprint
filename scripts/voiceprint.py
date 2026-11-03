#!/usr/bin/env python3
"""voiceprint: measure how you write, then score drafts against it.

  voiceprint.py build PATH... [--lines]   fingerprint your writing into $VOICEPRINT_HOME (default ~/.voiceprint)
  voiceprint.py score [FILE|-]            score a draft against your baseline
  voiceprint.py claude-prompts            print what you typed to Claude Code, one prompt per line
  voiceprint.py hook                      Claude Code PreToolUse hook (reads the tool call on stdin)
  voiceprint.py selftest
"""
import glob, json, os, re, shlex, statistics, sys

HOME = os.path.expanduser(os.environ.get("VOICEPRINT_HOME", "~/.voiceprint"))
BASELINE = os.path.join(HOME, "baseline.json")
ESCAPE = "voice-ok"
MIN_WORDS = 25

# Words and phrases that mark machine-written English. Public knowledge, not anyone's voice.
# 2023 register: the classic ChatGPT vocabulary, now rarer.
TELLS = {w: 1 for w in """
delve delves delving tapestry leverage leveraging utilize utilizing robust seamless seamlessly comprehensive
streamline foster harness unlock landscape ecosystem paradigm pivotal crucial intricate nuanced meticulous
meticulously underscore underscores showcase showcasing testament realm embark elevate empower holistic synergy
invaluable notably moreover furthermore additionally ultimately essentially fundamentally vibrant transformative
resonate resonates captivating endeavor plethora myriad multifaceted noteworthy groundbreaking interplay
""".split()}
# 2025-26 register: words that suddenly spread in AI-written PR text (louisabraham.github.io/load-bearing).
# Several are plain English, so density matters more than any one hit, and your own usage exempts a word.
TELLS.update({w: 1 for w in """
load-bearing plainly quietly refusal survived re-derived asserted genuinely deliberately premise outright
provably vacuously asymmetry carve-out chokepoint backstop restated rung ceiling defect
""".split()})
TELLS.update({p: 2 for p in [
    "it's not just", "not only", "in today's", "dive into", "deep dive", "it's worth noting", "in conclusion",
    "at its core", "serves as a", "plays a crucial role", "i hope this helps", "great question", "game-changer",
    "cutting-edge", "let's explore", "in the realm of", "here's the thing", "the bottom line",
]})
DASHES = re.compile(r"—|–| -- ")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
SIGNOFF = re.compile(r"^(thanks|thank you|best|regards|cheers|sincerely|warmly)\b[^\n]{0,30}$", re.I | re.M)


def strip_code(text):
    return re.sub(r"`[^`\n]*`", " ", re.sub(r"(?s)```.*?```", " ", text))


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", text)


def score(text, base=None):
    """Tell density per 100 words, ignoring tells the writer uses in their own work."""
    text = strip_code(text)
    low, n = text.lower(), max(len(words(text)), 1)
    own = (base or {}).get("tell_rates", {})
    hits = {}
    for t, w in TELLS.items():
        c = len(re.findall(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", low))
        if c and own.get(t, 0) < 0.5:  # per 1,000 words; a word you really use is your voice, not a tell
            hits[t] = c * w
    d = len(DASHES.findall(text))
    if d and (base or {}).get("rates", {}).get("dashes", 0) < 0.5:
        hits["dashes"] = 2 * d
    return round(100 * sum(hits.values()) / n, 2), dict(sorted(hits.items(), key=lambda kv: -kv[1]))


def units(paths, lines):
    for p in paths:
        files = [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs] if os.path.isdir(p) else [p]
        for f in sorted(files):
            if not f.endswith((".md", ".txt", ".markdown")):
                continue
            t = open(f, encoding="utf-8", errors="ignore").read()
            for u in (t.splitlines() if lines else [t]):
                if u.strip():
                    yield u.strip()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def build(paths, lines=False):
    docs = list(units(paths, lines))
    if not docs:
        sys.exit("no .md/.txt text found in " + " ".join(paths))
    allw = sum(len(words(strip_code(d))) for d in docs)
    per_k = lambda c: round(1000 * c / max(allw, 1), 2)
    body = "\n".join(strip_code(d) for d in docs)
    low = body.lower()
    sents = [len(words(s)) for s in re.split(r"(?<=[.!?])\s+|\n+", body) if words(s)]
    starts = [s.strip()[0] for s in re.split(r"(?<=[.!?])\s+|\n+", body) if s.strip()[:1].isalpha()]
    lens = [len(words(d)) for d in docs]
    base = {
        "units": len(docs), "words": allw, "split": "lines" if lines else "files",
        "median_words_per_unit": statistics.median(lens), "short_units_share": round(sum(l <= 3 for l in lens) / len(lens), 2),
        "median_sentence_words": statistics.median(sents) if sents else 0, "p90_sentence_words": pct(sents, 0.9),
        "lowercase_start_share": round(sum(c.islower() for c in starts) / max(len(starts), 1), 2),
        "rates": {"dashes": per_k(len(DASHES.findall(body))), "exclamations": per_k(body.count("!")),
                  "questions": per_k(body.count("?")), "semicolons": per_k(body.count(";")),
                  "soft_pause_dots": per_k(body.count("..") - 2 * body.count("...")), "emoji": per_k(len(EMOJI.findall(body))),
                  "contractions": per_k(len(re.findall(r"\b\w+(n't|'re|'ll|'ve|'m|'d)\b", low))),
                  "signoffs": per_k(len(SIGNOFF.findall(body)))},
        "tell_rates": {t: r for t in TELLS if (r := per_k(len(re.findall(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", low))))},
    }
    own = [score(d, base)[0] for d in docs if len(words(d)) >= MIN_WORDS]
    base["warn"] = max(1.0, pct(own, 0.95)) if own else 1.0
    base["deny"] = max(2.0, round(1.5 * max(own), 2)) if own else None
    os.makedirs(HOME, exist_ok=True)
    json.dump(base, open(BASELINE, "w"), indent=1)
    return base


def claude_prompts(root="~/.claude/projects"):
    """What the user typed to Claude Code: their most casual written register."""
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(root), "*", "*.jsonl"))):
        for line in open(f, errors="ignore"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            c = (e.get("message") or {}).get("content")
            if e.get("type") == "user" and isinstance(c, str) and not c.lstrip().startswith(("<", "[", "Caveat:")):
                c = " ".join(c.split())
                if 2 <= len(c.split()) <= 300:
                    yield c


def load():
    return json.load(open(BASELINE)) if os.path.exists(BASELINE) else None


def outgoing_text(call):
    """The prose a tool call is about to send, or None."""
    name, inp = call.get("tool_name", ""), call.get("tool_input", {}) or {}
    if name == "Bash":
        cmd = inp.get("command", "")
        if not re.search(r"\bgh\s+(pr|issue)\s+(create|comment|edit|review)\b|\bgit\s+commit\b", cmd):
            return None
        out = re.findall(r"<<-?\s*'?\"?(\w+)'?\"?\n(.*?)\n\1", cmd, re.S)
        if out:
            return "\n".join(b for _, b in out)
        try:
            toks = shlex.split(cmd)
        except ValueError:
            return None
        parts = []
        for i, t in enumerate(toks[:-1]):
            if t in ("-m", "--message", "-b", "--body"):
                parts.append(toks[i + 1])
            elif t in ("-F", "--body-file", "--file") and os.path.isfile(toks[i + 1]):
                parts.append(open(toks[i + 1], errors="ignore").read())
        return "\n".join(parts) or None
    if "slack" in name.lower():
        return "\n".join(v for k, v in inp.items() if isinstance(v, str) and k in ("text", "message", "content", "body")) or None
    return None


def hook():
    text = outgoing_text(json.load(sys.stdin))
    if not text or ESCAPE in text or len(words(strip_code(text))) < MIN_WORDS:
        return
    base = load()
    s, hits = score(text, base)
    warn = base["warn"] if base else 1.0
    if s < warn:
        return
    top = ", ".join(list(hits)[:5])
    deny = base and base.get("deny") and os.environ.get("VOICEPRINT_MODE", base.get("mode", "warn")) == "deny" and s >= base["deny"]
    msg = (f"voiceprint: this text scores {s} (your own writing stays under {warn}). Words you never use: {top}. "
           f"Rewrite those in your voice, or add '{ESCAPE}' if a word is unavoidable.")
    if not base:
        msg += " No baseline yet: run /voice-init."
    out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}, "systemMessage": msg}
    if deny:
        out["hookSpecificOutput"].update(permissionDecision="deny", permissionDecisionReason=msg)
    print(json.dumps(out))


def selftest():
    ai = ("We will delve into a robust and seamless ecosystem — it's not just a tool, it plays a crucial role. "
          "Moreover, this comprehensive paradigm will ultimately unlock a vibrant landscape for every team today.")
    human = "Fixed the retry loop. It was retrying on 404 too, which never succeeds. Now only 5xx retries, max 3. " * 2
    assert score(ai)[0] > 10 and score(human)[0] == 0, (score(ai), score(human))
    assert "delve" not in score(ai, {"tell_rates": {"delve": 2.0}})[1]
    call = {"tool_name": "Bash", "tool_input": {"command": "gh pr create --title t --body-file /nonexistent -b 'hello there'"}}
    assert outgoing_text(call) == "hello there"
    assert outgoing_text({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}) is None
    heredoc = {"tool_name": "Bash", "tool_input": {"command": "git commit -m \"$(cat <<'EOF'\nline one\nEOF\n)\""}}
    assert outgoing_text(heredoc) == "line one"
    assert outgoing_text({"tool_name": "mcp__slack__post", "tool_input": {"channel": "C1", "text": "hi"}}) == "hi"
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "build":
        b = build([p for p in a[1:] if p != "--lines"], "--lines" in a)
        print(json.dumps({k: v for k, v in b.items() if k != "tell_rates"}, indent=1))
    elif a[0] == "score":
        t = sys.stdin.read() if len(a) < 2 or a[1] == "-" else open(a[1]).read()
        s, hits = score(t, load())
        print(json.dumps({"score": s, "hits": hits, "warn_at": (load() or {}).get("warn", 1.0)}))
    elif a[0] == "claude-prompts":
        seen = set()
        for p in claude_prompts():
            if p not in seen:
                seen.add(p)
                print(p)
    elif a[0] == "hook":
        hook()
    elif a[0] == "selftest":
        selftest()
