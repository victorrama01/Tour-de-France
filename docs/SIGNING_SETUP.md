# Signing and Notarization Setup

This project can build and optionally sign desktop artifacts in GitHub Actions via `.github/workflows/build-desktop.yml`.

If signing secrets are missing, the workflow still builds unsigned artifacts.

## Required GitHub Secrets

Add these under **Repository Settings -> Secrets and variables -> Actions**.

### Windows signing

- `WINDOWS_CERT_BASE64`: Base64 of your `.pfx` code-signing certificate.
- `WINDOWS_CERT_PASSWORD`: Password for the `.pfx`.
- `WINDOWS_TIMESTAMP_URL` (optional): RFC3161 timestamp URL.  
  Default used when missing: `http://timestamp.digicert.com`

### macOS signing and notarization

- `APPLE_CERT_BASE64`: Base64 of your Developer ID Application `.p12`.
- `APPLE_CERT_PASSWORD`: Password for the `.p12`.
- `APPLE_SIGN_IDENTITY`: Exact identity string from Keychain, e.g.  
  `Developer ID Application: Your Company (TEAMID1234)`
- `APPLE_ID`: Apple ID email used for notarization.
- `APPLE_TEAM_ID`: Apple Developer Team ID.
- `APPLE_APP_SPECIFIC_PASSWORD`: App-specific password for that Apple ID.

## How to create Base64 secrets

### Windows PowerShell

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\codesign.pfx")) | Set-Clipboard
```

### macOS/Linux shell

```bash
base64 -i /path/to/codesign.p12 | pbcopy
```

## Notes

- Unsigned builds often trigger SmartScreen/Gatekeeper warnings.
- Signed + notarized macOS apps significantly reduce trust warnings.
- EV certificates improve SmartScreen reputation on Windows.
