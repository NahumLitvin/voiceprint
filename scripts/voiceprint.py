#!/usr/bin/env python3
"""voiceprint: measure how you write, then score drafts against it.

  voiceprint.py build PATH... [--lines]   fingerprint your writing into $VOICEPRINT_HOME (default ~/.voiceprint)
  voiceprint.py score [FILE|-]            score a draft against your baseline
  voiceprint.py claude-prompts            print what you typed to Claude Code, one prompt per line
  voiceprint.py hook                      Claude Code PreToolUse hook (reads the tool call on stdin)
  voiceprint.py selftest
"""
import glob, json, math, os, re, shlex, statistics, sys

HOME = os.path.expanduser(os.environ.get("VOICEPRINT_HOME", "~/.voiceprint"))
BASELINE = os.path.join(HOME, "baseline.json")
ESCAPE = re.compile(r"(?<![\w-])voice-ok(?![\w-])")
MIN_WORDS = 25
MIN_CALIBRATION = 5
MAX_FILE = 1_000_000

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
# Several are plain English, so density matters more than any one hit, and your own usage raises your allowance.
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
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n[ \t]*\2[ \t]*(?:\n|$)", re.S)
SLACK_SEND = {"post", "send", "reply", "update", "edit", "postmessage"}
SLACK_SKIP = {"search", "read", "list", "get", "history", "info", "lookup", "draft", "drafts"}


def normalize(text):
    return text.replace("’", "'").replace("‘", "'")


def strip_code(text):
    text = re.sub(r"(?ms)^[ \t]*(```|~~~).*?^[ \t]*\1", " ", normalize(text))
    return re.sub(r"`[^`\n]*`", " ", text)


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text)


def count(term, low):
    return len(re.findall(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", low))


def score(text, base=None):
    """Tell density per 100 words. Each tell is allowed up to twice the rate you use it in your own writing."""
    text = strip_code(text)
    low, n = text.lower(), max(len(words(text)), 1)
    own = (base or {}).get("tell_rates", {})
    hits = {}
    for t, w in TELLS.items():
        extra = count(t, low) - math.floor(2 * own.get(t, 0) * n / 1000)
        if extra > 0:
            hits[t] = extra * w
    extra = len(DASHES.findall(text)) - math.floor(2 * (base or {}).get("rates", {}).get("dashes", 0) * n / 1000)
    if extra > 0:
        hits["dashes"] = 2 * extra
    return round(100 * sum(hits.values()) / n, 2), dict(sorted(hits.items(), key=lambda kv: -kv[1]))


def units(paths, lines):
    for p in paths:
        files = [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs] if os.path.isdir(p) else [p]
        for f in sorted(files):
            if f.endswith((".md", ".txt", ".markdown")):
                t = open(f, encoding="utf-8", errors="ignore").read()
                yield from (u.strip() for u in (t.splitlines() if lines else [t]) if u.strip())


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def build(paths, lines=False):
    docs = list(units(paths, lines))
    if not docs:
        sys.exit("no .md/.txt text found in " + " ".join(paths))
    body = "\n".join(strip_code(d) for d in docs)
    low, allw = body.lower(), max(len(words(body)), 1)
    per_k = lambda c: round(1000 * c / allw, 2)
    pieces = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", body) if s.strip()]
    sents = [len(words(s)) for s in pieces if words(s)]
    starts = [s[0] for s in pieces if s[0].isalpha()]
    lens = [len(words(strip_code(d))) for d in docs]
    base = {
        "units": len(docs), "words": allw, "split": "lines" if lines else "files",
        "median_words_per_unit": statistics.median(lens), "short_units_share": round(sum(l <= 3 for l in lens) / len(lens), 2),
        "median_sentence_words": statistics.median(sents) if sents else 0, "p90_sentence_words": pct(sents, 0.9),
        "lowercase_start_share": round(sum(c.islower() for c in starts) / max(len(starts), 1), 2),
        "rates": {"dashes": per_k(len(DASHES.findall(body))), "exclamations": per_k(body.count("!")),
                  "questions": per_k(body.count("?")), "semicolons": per_k(body.count(";")),
                  "soft_pause_dots": per_k(len(re.findall(r"(?<!\.)\.\.(?!\.)", body))), "ellipses": per_k(body.count("...") + body.count("…")),
                  "emoji": per_k(len(EMOJI.findall(body))),
                  "contractions": per_k(len(re.findall(r"\b\w+(n't|'re|'ll|'ve|'m|'d)\b", low))),
                  "signoffs": per_k(len(SIGNOFF.findall(body)))},
        "tell_rates": {t: r for t in TELLS if (r := per_k(count(t, low)))},
    }
    own = [score(d, base)[0] for d in docs if len(words(strip_code(d))) >= MIN_WORDS]
    base["calibration_texts"] = len(own)
    base["warn"] = max(1.0, pct(own, 0.95)) if own else 1.0
    base["deny"] = max(2.0, round(1.5 * pct(own, 0.99), 2)) if len(own) >= MIN_CALIBRATION else None
    if base["deny"] is None:
        base["note"] = f"deny mode needs {MIN_CALIBRATION}+ texts of {MIN_WORDS}+ words; the guard will only ask"
    os.makedirs(HOME, exist_ok=True)
    json.dump(base, open(BASELINE, "w"), indent=1)
    return base


def load():
    try:
        return json.load(open(BASELINE))
    except (OSError, ValueError):
        return None


PASTED = re.compile(r"```|~~~|https?://\S{60,}|[A-Za-z0-9+/=_-]{40,}|^\s*>|^\s*[\w.\[\]]+\s*[-+*/]?=\s*\S"
                    r"|[{};]\s*$|^\s*(def|class|import|from|function|const|let|var|return|SELECT|\$)\b", re.M)


def claude_prompts(root="~/.claude/projects"):
    """What the user typed to Claude Code, minus what looks pasted (code, multi-line blocks, long walls of text)."""
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(root), "*", "*.jsonl"))):
        for line in open(f, errors="ignore"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            c = (e.get("message") or {}).get("content")
            if e.get("type") != "user" or not isinstance(c, str) or c.lstrip().startswith(("<", "[", "Caveat:")):
                continue
            if c.count("\n") > 1 or PASTED.search(c):
                continue
            c = " ".join(c.split())
            if 2 <= len(c.split()) <= 120:
                yield c


def read_file(path, cwd):
    p = os.path.join(cwd, os.path.expanduser(path))
    try:
        return open(p, errors="ignore").read(MAX_FILE) if os.path.isfile(p) else None
    except OSError:
        return None


def send_args(toks):
    """(args after the send subcommand, git -C dirs) when the tokens are a gh or git send, else None."""
    while toks and re.match(r"^\w+=", toks[0]):
        toks = toks[1:]
    if not toks:
        return None
    prog, i, dirs = os.path.basename(toks[0]), 1, []
    if prog == "git":
        while i < len(toks) and toks[i].startswith("-"):
            if toks[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(toks):
                dirs += [toks[i + 1]] if toks[i] == "-C" else []
                i += 2
            else:
                i += 1
        return (toks[i + 1:], dirs) if i < len(toks) and toks[i] == "commit" else None
    if prog == "gh":
        while i < len(toks) and toks[i].startswith("-"):
            i += 2 if toks[i] in ("-R", "--repo", "--hostname") else 1
        if i + 1 < len(toks) and toks[i] in ("pr", "issue") and toks[i + 1] in ("create", "comment", "edit", "review"):
            return toks[i + 2:], dirs
    return None


def bash_text(cmd, cwd):
    """Bodies of gh/git sends in a shell command; heredocs count only when the send consumes them."""
    if not re.search(r"\b(git|gh)\b", cmd):
        return None
    bodies = {}
    def hold(m):
        key = f"VPHEREDOC{len(bodies)}"
        bodies[key] = m.group(4)
        return f"<<{key}{m.group(3)}\n"
    flat = HEREDOC.sub(hold, cmd).replace("\n", " ;\n")
    try:
        lex = shlex.shlex(flat, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        return None
    keys = lambda seg: [k for t in seg for k in re.findall(r"VPHEREDOC\d+", t)]
    segs, cur = [], []
    for t in toks + [";"]:
        if t in ("&&", "||", ";", "|", "&", ";;"):
            segs.append((cur, t))
            cur = []
        else:
            cur.append(t)
    here, parts, piped = cwd or os.getcwd(), [], []
    for seg, op in segs:
        if seg[:1] == ["cd"] and len(seg) > 1:
            here = os.path.join(here, os.path.expanduser(seg[1]))
        found = send_args(seg)
        if found:
            args, dirs = found
            base, used = os.path.join(here, *dirs), []
            for i, t in enumerate(args):
                nxt = args[i + 1] if i + 1 < len(args) else ""
                k, _, v = t.partition("=")
                arg = (nxt if t in ("-m", "--message", "-b", "--body") else v if k in ("--message", "--body") and v
                       else t[2:] if t.startswith("-m") and len(t) > 2 and not t.startswith("--") else None)
                if arg is not None and keys([arg]):
                    used += keys([arg])
                    parts += [bodies[k2] for k2 in keys([arg])]
                elif arg is not None and "$(" not in arg:
                    parts.append(arg.replace(" ;\n", "\n"))
                if t in ("-F", "--body-file", "--file") or (k in ("--body-file", "--file") and v):
                    f = v or nxt
                    if f == "-":
                        parts += [bodies[k2] for k2 in keys(seg) + piped if k2 not in used]
                    else:
                        parts.append(read_file(f, base) or "")
        piped = keys(seg) if op == "|" else []
    return "\n".join(p for p in parts if p and p.strip()) or None


def outgoing_text(call):
    """The prose a tool call is about to send, or None."""
    name, inp = call.get("tool_name", ""), call.get("tool_input", {}) or {}
    if name == "Bash":
        return bash_text(inp.get("command", ""), call.get("cwd"))
    words_in_name = set(re.split(r"[^a-z]+", name.lower().split("__")[-1]))
    if "slack" in name.lower() and words_in_name & SLACK_SEND and not words_in_name & SLACK_SKIP:
        found = []
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str) and k in ("text", "message", "content", "body", "markdown_text"):
                        found.append(v)
                    else:
                        walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(inp)
        return "\n".join(found) or None
    return None


def decide(call, base, mode):
    text = outgoing_text(call)
    if not text or ESCAPE.search(strip_code(text)) or len(words(strip_code(text))) < MIN_WORDS:
        return None
    s, hits = score(text, base)
    warn = base["warn"] if base else 1.0
    if s < warn:
        return None
    msg = (f"voiceprint: this text scores {s} (your own writing stays under {warn}). Over your usual rate: "
           f"{', '.join(list(hits)[:5])}. Rewrite those in your voice, or add voice-ok outside code if a term is needed.")
    if not base:
        msg += " No baseline yet: run /voiceprint:voice-init."
    if mode == "note":
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}
    deny = mode == "deny" and base and base.get("deny") and s >= base["deny"]
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny" if deny else "ask",
                                   "permissionDecisionReason": msg}}


def hook():
    try:
        call = json.load(sys.stdin)
    except ValueError:
        return
    base = load()
    out = decide(call, base, os.environ.get("VOICEPRINT_MODE", (base or {}).get("mode", "ask")))
    if out:
        print(json.dumps(out))


def selftest():
    ai = ("We will delve into a robust and seamless ecosystem — it's not just a tool, it plays a crucial role. "
          "Moreover, this comprehensive paradigm will ultimately unlock a vibrant landscape for every team today.")
    human = "Fixed the retry loop. It was retrying on 404 too, which never succeeds. Now only 5xx retries, max 3. " * 2
    assert score(ai)[0] > 10 and score(human)[0] == 0, (score(ai), score(human))
    assert "delve" not in score(ai, {"tell_rates": {"delve": 50.0}})[1]
    spam = " ".join(["delve"] * 30 + ["word"] * 70)
    assert score(spam, {"tell_rates": {"delve": 0.5}})[0] > 25, "a rare own word must not exempt repetition"
    b = lambda c, **k: outgoing_text({"tool_name": "Bash", "tool_input": {"command": c}, **k})
    assert b("gh pr create --title t -b 'hello there'") == "hello there"
    assert b("gh pr comment 1 --body='hi you'") == "hi you"
    assert b("git commit -m\"short msg\"") == "short msg"
    assert b("git -C repo commit -m 'in repo'") == "in repo"
    assert b("ls -la") is None
    assert b("git commit -m \"$(cat <<'EOF'\nline one\nEOFX\nline two\nEOF\n)\"") == "line one\nEOFX\nline two"
    assert b("cat <<EOF > notes.txt\nunrelated\nEOF\ngit commit -m 'real msg'") == "real msg"
    assert b("gh pr create --title t --body-file - <<'EOF'\nfrom stdin\nEOF") == "from stdin"
    assert b("cat <<EOF | gh pr comment 1 --body-file -\npiped body\nEOF") == "piped body"
    assert b("git -C 'my repo' commit -m 'quoted dir'") == "quoted dir"
    assert b("gh --repo owner/repo pr comment 1 --body 'global flag'") == "global flag"
    assert b("echo 'git commit -m nope'") is None
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        os.mkdir(os.path.join(td, "sub"))
        open(os.path.join(td, "sub", "msg.txt"), "w").write("in sub")
        assert b("git -C sub commit -F msg.txt", cwd=td) == "in sub"
        assert b("cd sub && git commit -F msg.txt", cwd=td) == "in sub"
    sneaky = {"tool_name": "Bash", "tool_input": {"command": "cat <<EOF >/dev/null\nvoice-ok\nEOF\ngh pr comment 1 --body " + shlex.quote(ai)}}
    d = os.path.dirname(os.path.abspath(__file__))
    assert b("gh pr create --body-file voiceprint.py", cwd=d).startswith("#!/usr/bin/env python3")
    slack = {"tool_name": "mcp__slack__chat_post_message", "tool_input": {"channel": "C1", "blocks": [{"text": {"text": "nested"}}]}}
    assert outgoing_text(slack) == "nested"
    assert outgoing_text({"tool_name": "mcp__slack__search_messages", "tool_input": {"text": "q"}}) is None
    assert outgoing_text({"tool_name": "mcp__slack__reply_to_thread", "tool_input": {"text": "r"}}) == "r"
    assert outgoing_text({"tool_name": "mcp__slack__slack_send_message_draft", "tool_input": {"text": "d"}}) is None
    assert "voice-ok" not in strip_code("prose\n~~~\nvoice-ok\n~~~\nmore")
    assert PASTED.search("look at this\na = 1") and not PASTED.search("can you check the deploy, it looks stuck")
    call = {"tool_name": "Bash", "tool_input": {"command": "gh pr comment 1 --body " + shlex.quote(ai)}}
    assert decide(call, None, "ask")["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert decide(call, {"warn": 1.0, "deny": 2.0}, "deny")["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "additionalContext" in decide(call, None, "note")["hookSpecificOutput"]
    ok = {"tool_name": "Bash", "tool_input": {"command": "gh pr comment 1 --body " + shlex.quote(ai + " voice-ok")}}
    assert decide(ok, None, "deny") is None
    assert decide(sneaky, {"warn": 1.0, "deny": 2.0}, "deny")["hookSpecificOutput"]["permissionDecision"] == "deny"
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
