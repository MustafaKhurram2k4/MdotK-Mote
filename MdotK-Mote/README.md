# MdotK - Mote

Mote is a consent-based phone remote for a desktop host on a trusted local network. The desktop host serves the mobile web client, pairs it using a shared secret, and routes only allowlisted actions.

## Download for regular users

Official downloadable builds are published on the [GitHub Releases page](https://github.com/MustafaKhurram2k4/MdotK-Mote/releases). The release workflow builds on native GitHub runners when a version tag (`v*`) is pushed.

- **Windows:** download `Mote-Windows-x64.zip`, extract, and run `Mote.exe`.
- **macOS Apple Silicon:** download `Mote-macOS-arm64.zip`, extract, and open `Mote.app`. This unsigned build may require approval in macOS Privacy & Security.
- **Linux x64:** download `Mote-Linux-x64.zip`, extract, and run `./Mote`. Some desktop environments require installing system libraries and granting access to `/dev/uinput` for gamepad support.

The workflow also builds macOS Intel (`Mote-macOS-x64.zip`) for Intel Macs. These are portable bundles, not signed MSI/PKG/DEB installers. Windows users may see SmartScreen; macOS users may see Gatekeeper warnings because builds are not code-signed/notarized. Never bypass warnings for a download you did not obtain from the official Releases page.

## Features

- Desktop control center with tray, QR code and local status banner.
- Secret token stored in OS credential manager.
- Phone-only remote page and tablet/desktop landing page.
- AES-GCM encrypted WebSocket command payloads with PBKDF2 key derivation and sequence validation.
- Five UI device slots (the current host controls one PC instance).
- App/stream shortcuts, media controls, voice typing, keyboard input, power shortcuts and controller UI.
- Sensitive keyboard, gamepad and power permissions are off by default and require desktop opt-in.
- Original artwork assets preserved in `static/assets/`.

## First use

1. Install or extract the OS-specific build and launch Mote.
2. Create a token of at least 8 characters or generate a random token, then click **Lock & Save Token**.
3. Click **Start Mote**.
4. On your phone, join the same trusted private Wi-Fi. Scan the QR code or open the local address shown in Mote.
5. Enter your token and pair.
6. Enable desktop permission toggles only for features you intend to use. **Pause / Disconnect Remote** stops phone commands immediately.

## Requirements and limitations

- Use only trusted home/private LANs. The host serves plain HTTP, and pairing-token submission is not TLS-protected. Do not use guest/public Wi-Fi and do not port-forward the Mote port to the Internet. See `SECURITY.md`.
- Windows virtual Xbox gamepad requires the compatible ViGEmBus driver and is not guaranteed to work with every game. Game detection is heuristic and is not an anti-cheat bypass.
- Linux virtual gamepad support depends on the uinput backend and system permission to access it.
- macOS has no native virtual Xbox backend in this release; controller input uses fallback behavior.
- Game focus detection is heuristic, not a universal game detector.
- macOS build in this workflow targets Apple Silicon. Windows/Linux release builds target x64.
- Release binaries are portable packages, not code-signed/notarized installers.
- Device slots are UI selectors; each running Mote host instance represents one PC.

## Build from source

Python 3.11+ recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python desktop_app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python desktop_app.py
```

Run tests: `python -m unittest discover -s tests -v`

Build the native portable package on the current OS: `python build_installer.py` (install PyInstaller first). PyInstaller is not a cross-compiler.

## Releases

Push a version tag, such as `v0.2.1`, to trigger native builds and publish the portable bundles to GitHub Releases. Builds are created on GitHub-hosted runners; this repository does not claim that a build has been physically tested on every target OS.

## License

MIT. See `LICENSE`.
