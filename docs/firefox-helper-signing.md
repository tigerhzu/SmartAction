# Container Helper Extension Signing

SmartAction Container Helper must be installed as a signed XPI for normal Firefox release builds.

Development mode can use `Load Temporary Add-on`, but that is only for testing. Temporary add-ons disappear when Firefox restarts.

Production mode uses a signed XPI. The user installs it once, and Firefox keeps it installed after restart.

## Add-on ID

The fixed add-on id is:

```text
smartaction-container-helper@naughtytiger06.local
```

This id must match:

- `extensions/firefox-helper/manifest.json`
- `native/firefox_helper_host/host_manifest.json.template`
- Firefox Native Messaging Host `allowed_extensions`

## Build The XPI

From the SmartAction project root:

```powershell
build_extension.bat
```

or:

```powershell
python tools/build_firefox_extension.py
```

Output:

```text
dist/firefox-helper.xpi
%LOCALAPPDATA%/SmartAction/firefox-helper.xpi
```

## AMO Unlisted Signing

Use Mozilla Add-ons Developer Hub to sign the XPI as an unlisted add-on.

1. Open:

```text
https://addons.mozilla.org/developers/
```

2. Sign in with a Firefox/Mozilla account.
3. Choose to submit a new add-on.
4. Select distribution:

```text
On your own
```

This is AMO unlisted distribution. The add-on is signed by Mozilla but is not listed publicly.

5. Upload:

```text
dist/firefox-helper.xpi
```

6. Complete validation and submission.
7. Download the signed XPI from AMO after processing.
8. Replace the local unsigned file with the signed one if desired:

```text
%LOCALAPPDATA%/SmartAction/firefox-helper.xpi
```

## Install Signed XPI

In SmartAction Client Workspace:

1. Select the client.
2. Confirm the Firefox Profile dropdown uses the profile you want.
3. Click `Install Helper Extension`.
4. Firefox opens the XPI with that profile.
5. Confirm the installation prompt.
6. Click `Check Helper`.

If `Check Helper` succeeds, Launch Workspace can open URLs in the requested Firefox Container.

## Development Mode

Use only while editing the extension:

1. Open Firefox.
2. Go to:

```text
about:debugging#/runtime/this-firefox
```

3. Click `Load Temporary Add-on`.
4. Select:

```text
extensions/firefox-helper/manifest.json
```

Temporary Add-on mode is not production. Firefox removes the extension after restart.
