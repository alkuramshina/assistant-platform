# Phase 10 Verification

Status: automated pass, human UAT pending

Automated checks completed:

- `py -3 -m unittest tests.test_deployer tests.test_deploy_engine tests.test_console_ui tests.test_runtime_image tests.test_redact`
- `docker compose config`

Covered requirements:

- `ISO-01`: automated tests assert separate per-bot roots, data, workspace, secrets, compose files, secret files, and Compose project names.
- `ISO-02`: automated test asserts stopping one bot runs `docker compose down` only for that bot project.
- `HARD-01`: automated tests assert no docker.sock mount, no privileged mode, non-root user, allowlist, per-bot mounts, Compose secrets, and no raw copied test secrets in rendered Compose.

Remaining human check:

- Run `10-HUMAN-UAT.md` on the VM to confirm two real Telegram bots coexist and one can stop without affecting the other.
