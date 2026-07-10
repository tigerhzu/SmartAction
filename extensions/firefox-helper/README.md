# SmartAction Container Helper Extension

This WebExtension receives SmartAction Client Workspace launch requests through Native Messaging and opens each URL in the requested browser Container.

## Extension ID

The add-on id is fixed in `manifest.json`:

```text
smartaction-container-helper@naughtytiger06.local
```

This id must match the Native Messaging Host `allowed_extensions` value.

## Required Permissions

```json
[
  "tabs",
  "cookies",
  "contextualIdentities",
  "nativeMessaging"
]
```

`cookies` is required when opening a tab with `cookieStoreId`.
Without it, the browser may return:

```text
No permission for cookieStoreId: firefox-container-6
```

If you see this error, confirm `manifest.json` includes `cookies`, rebuild/re-sign the XPI, and reinstall or reload the extension.

## Build XPI

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

## Production Install

For normal release builds, production use requires a signed XPI.

Recommended flow:

1. Build `dist/firefox-helper.xpi`.
2. Submit/sign it using AMO Unlisted signing.
3. Install the signed XPI once.
4. Restart the browser; the extension remains installed.

Do not rely on `Load Temporary Add-on` for normal users. It is development-only and disappears after browser restart.

## Development Install

Development mode is still useful while editing `background.js` or `manifest.json`:

1. Open the browser.
2. Go to `about:debugging#/runtime/this-firefox`.
3. Click `Load Temporary Add-on`.
4. Select `extensions/firefox-helper/manifest.json`.

After manifest changes, click `Reload`. If there is no `Reload` button, remove the temporary add-on and load it again.
