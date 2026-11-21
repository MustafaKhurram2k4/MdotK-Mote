# Security model and responsible use
Mote is for owner-operated computers and phones on trusted private LANs. The desktop UI visibly shows running/paused/connected state and provides Pause/Disconnect. Keyboard, gamepad mapping and power commands require explicit desktop toggles. Power actions additionally require phone confirmation.

## Protections implemented
- Shared token stored in OS credential store.
- Token length validation and IP failed-pairing lockout (five failures, 15 minutes).
- Private-IP checks for pairing and WebSocket sessions.
- Enum/allowlist command mapping; no remote shell command strings.
- AES-GCM command/response envelopes; PBKDF2-HMAC-SHA256 (600,000 iterations); sequence validation and timestamp freshness checks.
- Sessions bound to pairing IP and expire after 12 hours.
- Sensitive permissions default off.

## Limitations
This is not bank-grade security. HTTP is not TLS. The initial pairing token is sent in an ordinary HTTP request, so application-layer encrypted WebSocket payloads do not protect the token during pairing from a LAN interceptor. The host decrypts messages to execute actions; this is not host-opaque end-to-end encryption. IP/user-agent controls can be spoofed and are not authentication guarantees. The session store is in-memory and the host/device-slot design is not a hardened production identity system.

## Safe use
- Pair only on trusted private Wi-Fi.
- Avoid public, guest, hotel and shared networks.
- Do not port-forward port 8765 or expose via public proxy.
- Leave Keyboard, Gamepad and Power permissions off unless needed.
- Pause/disconnect when finished; rotate token if exposure is suspected.

Report security issues privately to the maintainer. No security bounty or SLA is offered.

## Verification boundaries

Portable protocol and allowlist checks are not a penetration test. This build's remote is served over plain HTTP on the LAN; authenticated command envelopes are AES-GCM, but HTTP metadata and browser-host trust remain unprotected. Do not use it on public, guest, or untrusted Wi-Fi and do not port-forward it. A trusted LAN does not make this system "bank-grade" or production-certified.

## Gamepad virtualization note
The Windows virtual gamepad backend relies on `vgamepad` and ViGEmBus. ViGEmBus is a separate system driver with its own lifecycle and license/installer requirements. Install drivers only from trusted official sources and only after the desktop user approves. Mote does not read game memory, inject code into game processes, bypass anti-cheat, or manipulate gameplay state; foreground detection is process-name based only.
