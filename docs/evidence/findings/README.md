# Finding closure evidence

This directory contains evidence for the remediation items in
`docs/findings/register.yml`. One subdirectory is created for a finding when it
first has evidence to retain.

A closed finding has exactly one `closure.md`. Its YAML frontmatter follows
`docs/findings/closure-packet.schema.json` and carries the reproducible facts;
the Markdown body explains the result in plain language. Raw machine-readable
outputs sit beside it and are named in the frontmatter with their SHA-256
hashes.

The publication restrictions in `SECURITY.md` apply. No credential, key,
certificate, real identity, deployment location, or sensitive traffic belongs
in a closure packet or attached artifact.
