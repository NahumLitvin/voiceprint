# Security

## Reporting a vulnerability

Please report it privately: [open a security advisory](https://github.com/NahumLitvin/voiceprint/security/advisories/new). Do not open a public issue, since the fix is not out yet. I aim to answer within a week and credit the report in the release notes, unless you ask me not to.

## What counts

voiceprint reads the writing you give it and every Bash or Slack tool call Claude is about to make. A vulnerability is anything that turns either of those into more than a local score, for example:

- your corpus, profile or baseline leaving your machine, or landing in a repo, a log or a tool call
- the hook reading a file the command did not name, or reading outside the size limit
- the hook running, evaluating or expanding any part of the command it inspects
- crafted command text or a crafted baseline making the hook allow a call it should ask about or deny, or crash in a way that blocks every call
- the collector saving other people's messages as the user's own

A tell word missing from the list, or a draft that scores lower than it should, is a normal bug: open an issue.

## Supported versions

Only the latest release gets fixes. Update with `claude plugin marketplace update voiceprint && claude plugin update voiceprint@voiceprint`.
