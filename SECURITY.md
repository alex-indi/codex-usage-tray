# Security policy

## Supported versions

Security fixes are provided for the latest release only while the project is in its pre-1.0 stage.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose credentials, execute untrusted code, or compromise a user's Windows account.

Use GitHub's **Report a vulnerability** button on the repository's Security tab. If private vulnerability reporting is not yet enabled, contact the maintainer through the address listed on their GitHub profile and share only a minimal description until a private channel is agreed.

Include:

- affected version or commit;
- Windows and Codex Desktop versions;
- impact and realistic attack scenario;
- minimal reproduction steps;
- suggested remediation, if known.

Never include real access tokens, cookies, `.codex/auth.json`, crash dumps containing secrets, or private account data.

## Security boundaries

Codex Usage Tray:

- starts the locally installed official `codex app-server --stdio` runtime;
- sends only read requests for usage and rate-limit information;
- does not read or store Codex credential files;
- does not redeem saved resets;
- does not require elevation; optional per-user autostart is enabled only by the user;
- does not download or execute updates.

An explicit `CODEX_USAGE_TRAY_CODEX_PATH` environment override is intended for developers. Pointing it to an untrusted executable is equivalent to running that executable directly and is outside the application's security guarantees.

## Release verification

Official release assets include SHA-256 checksums generated after packaging. Code signing is planned for stable releases. Until then, users should download only from this repository's Releases page and compare the checksum before running the executable.
