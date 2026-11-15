# Requirements first

New behaviour starts with a requirement, not with code.

- Before implementing a new feature or a change in behaviour (backend, mobile app or dashboard app), add or update the requirement in `docs/requirements/<backend|mobile|dashboard>/*.sdoc` with `STATUS: Draft`. Show the new or changed requirement text to the user and get agreement before writing the code.
- Add the matching verification in `docs/verifications/<app>/*.sdoc` (`Parent` relation to the requirement, `ROLE: Verifies`). Prefer `METHOD: Test` with the test file and test names in `TEST`. Use Demonstration or Inspection only when an automated test is not practical, and say why in `COMMENT`.
- When the change is done and verified, set the requirement to `STATUS: Active`. A removed behaviour becomes `STATUS: Deprecated`; don't delete it.
- Changes that affect several apps get a requirement in each affected app, linked with a `Parent` relation (e.g. a dashboard requirement whose parent is a backend API requirement).
- No new requirement is needed when the change is already covered by an existing one: a bugfix that makes the code meet an existing requirement, a refactor, dependency updates, tooling, CI or docs. Name the requirement UID(s) it falls under in the summary to the user.
  - If a bugfix shows that the existing verification missed the bug, add or tighten the verification.
  - If a bug turns out to be behaviour no requirement describes, it is not covered: write the requirement first.
- Run `strictdoc export docs --output-dir /tmp/sdoc` after editing; it must pass.
