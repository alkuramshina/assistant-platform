# Phase 10 Human UAT

Status: passed

Human verification: confirmed by user on 2026-04-21.

Run after deploying the current branch to a VM.

1. Run deployer without `--domain`.
   - Expected: deploy succeeds and prints an HTTP warning.

2. Optional domain path: run deployer with `--domain <domain>`.
   - Expected: console backend binds to localhost and Caddy reverse-proxies HTTPS.

3. Create two bots with different Telegram tokens and allowlisted users.
   - Expected: both can be created without exposing saved token/key values in the UI.

4. Start both bots.
   - Expected: both show running; Runtime logs are scoped to the selected bot.

5. Message each bot in Telegram.
   - Expected: each bot responds; Activity logs appear only under the matching selected bot.

6. Stop one bot.
   - Expected: stopped bot stops responding; the other bot keeps responding.

7. On the VM, inspect bot directories and Compose projects.
   - Expected: each bot has a separate `/opt/nanobot-console/bots/<bot-id>/` directory and separate Compose project.
