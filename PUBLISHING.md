# Publish Mote on GitHub Releases

This repository is configured to build portable downloadable bundles on native GitHub-hosted runners.

## One-time setup

1. Upload this repository to `MustafaKhurram2k4/MdotK-Mote`.
2. Confirm **Settings → Actions → General → Workflow permissions** permits workflows to create releases (the release workflow declares `contents: write`).
3. Check the **Actions** tab and run CI or `release.yml` with workflow dispatch to confirm builds. Manual dispatch builds and stores the OS artifacts but does not publish a release.

## Publish a version

From the repository root, create and push a version tag:

```bash
git tag v0.2.1
git push origin v0.2.1
```

The `Build and Publish Portable Releases` workflow will build on Windows, macOS Apple Silicon, macOS Intel, and Ubuntu x64, then publish the following assets to the GitHub Release for that tag:

- `Mote-Windows-x64.zip` (portable `Mote.exe`)
- `Mote-macOS-arm64.zip` (`Mote.app`)
- `Mote-macOS-x64.zip` (`Mote.app`)
- `Mote-Linux-x64.zip` (portable executable)

## Important distribution caveats

These are unsigned portable builds, not installers. Windows SmartScreen and macOS Gatekeeper may warn. macOS apps are not code-signed/notarized. Linux builds are built on Ubuntu and may require system libraries on other distributions. Virtual controller drivers are not bundled or installed by the workflow.

The CI builds prove compilation and packaging on the runners; they do not replace real-device testing of remote pairing, OS actions, game input, or app behavior on target computers.
