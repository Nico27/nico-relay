# AGENTS.md — working agreement for this repository

## Always run `localtest` before pushing

`localtest` means the full local verification for this project:

```bash
./scripts/verify.sh      # canonical localtest: stack, seed, API, tests, UI proxy
```

Faster subsets while iterating (they do not replace `localtest` before a push):

```bash
make test-api            # backend only, no database
make test-api-all        # backend incl. Postgres integration tests
make test-web            # frontend typecheck + vitest
```

Rules:

1. **Run `localtest` before every push to GitHub.** No exceptions, including "one-line"
   changes and documentation-only changes that touch commands.
2. **If anything fails, fix the code first.** Then run `localtest` again — from the start,
   not just the failing step — and only push once it is green.
3. **Never push red.** Do not disable, skip, `xfail`, or comment out a failing test to get a
   green run. Do not push with a known failure to "fix it in the next commit".
4. When a failure is caused by the environment rather than the code (database not running,
   port taken, missing tool), say so explicitly and stop; a workaround that weakens a check
   is not a fix.
5. Report the exact command and its result in the hand-off, including any test that is
   skipped and why.

## Human-only files — no AI writes

These files belong to humans only:

- `AI_LOG.md`
- `PLAN.md`

AI must **not** create, write, edit, append to, reformat, rename, move, or delete them, and
must not generate them as a side effect of another task (no scaffolding, no "helpful" first
draft, no codemod, no formatter). Reading them for context is allowed; changing them is not,
even when a change looks obviously correct.

If a task seems to require a change to one of these files, stop and ask the human instead of
editing. If they do not exist, leave them absent.

## Scope

Local development only. There is no production deployment in this repository, so do not add
release, deploy, or production-image configuration without being asked.
