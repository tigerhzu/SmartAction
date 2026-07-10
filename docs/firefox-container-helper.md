# SmartAction Firefox Container Helper

SmartAction Client Workspace V2 can open customer maintenance URLs in a specific Firefox Container.

The helper has two parts:

- Container Helper Extension: finds the Firefox Container by name and opens URLs with `cookieStoreId`.
- Native Messaging Host: bridges SmartAction and the extension using Firefox Native Messaging.

SmartAction only stores workspace metadata and URLs. It does not store passwords, cookies, tokens, or Firefox login state.

## Build the Container Helper Extension

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

The add-on id is fixed:

```text
smartaction-container-helper@naughtytiger06.local
```

The extension requires:

```json
[
  "tabs",
  "cookies",
  "contextualIdentities",
  "nativeMessaging"
]
```

## Install the Extension

For normal Firefox release builds, production use requires a signed XPI.

Recommended production flow:

1. Build `dist/firefox-helper.xpi`.
2. Submit/sign it using AMO Unlisted signing.
3. Install the signed XPI once in the Firefox profile used by SmartAction.
4. Restart Firefox. The extension remains installed.

Development mode is still available:

1. Open Firefox.
2. Go to `about:debugging#/runtime/this-firefox`.
3. Click `Load Temporary Add-on`.
4. Select `extensions/firefox-helper/manifest.json`.

Temporary add-ons are for development only. They disappear after Firefox restarts.

For signing details, see:

```text
docs/firefox-helper-signing.md
```

## Install the Native Messaging Host

Run:

```powershell
python native/firefox_helper_host/install_host_windows.py
```

The installer copies host files to:

```text
%LOCALAPPDATA%/SmartAction/firefox_helper_host/
```

It registers:

```text
HKCU\Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper
```

Communication files are stored in:

```text
%LOCALAPPDATA%/SmartAction/firefox_helper/
```

Files:

- `pending_launch.json`
- `last_result.json`
- `helper.log`

## Firefox Profile Rules

Client Workspace uses Firefox profiles from:

```text
%APPDATA%/Mozilla/Firefox/profiles.ini
```

In the Client Workspace editor, choose a profile from the Firefox Profile dropdown. The dropdown shows:

- profile name
- profile path
- `Default=1` when Firefox marks it as the default profile

SmartAction also supports a dedicated profile name:

```text
SmartAction-ClientWorkspace
```

Use `Create SmartAction Profile` in the Client Workspace client editor to create or select that fixed profile.

Important launch behavior:

- SmartAction never creates a temporary Firefox profile.
- SmartAction never uses `-no-remote`.
- If Firefox is already running, SmartAction does not start another Firefox process for Container launches.
- If Firefox is not running, SmartAction starts the selected fixed profile with:

```text
firefox.exe -P "SmartAction-ClientWorkspace" --new-window about:blank
```

After Firefox is running, URL opening is handled by the Helper Extension through Native Messaging.

## Create a Firefox Container

1. Open Firefox.
2. Install or enable Firefox Multi-Account Containers if needed.
3. Create a container for the customer, for example:

```text
ABC-Maintenance
```

## What To Put In SmartAction

In Client Workspace, set:

```text
containerName = ABC-Maintenance
```

The value must exactly match the Firefox Container name.

If `containerName` is empty, SmartAction uses the V1 behavior and opens URLs as normal Firefox tabs.

## Common Errors

### Helper Extension Did Not Respond

Check:

- Helper Extension is installed and enabled in the Firefox profile being launched.
- Firefox is using the expected profile, not a different profile.
- Native Messaging Host is registered under `HKCU`.
- `%LOCALAPPDATA%/SmartAction/firefox_helper/helper.log`

### Container Not Found

Check that `containerName` in SmartAction exactly matches the Firefox Container name.

SmartAction does not fall back to normal tabs when a container is requested, to avoid logging into the wrong customer environment.

### No Permission For cookieStoreId

This means the Container Helper Extension is missing the `cookies` permission or Firefox is still running an older installed copy of the extension.

Fix:

1. Confirm `extensions/firefox-helper/manifest.json` includes `"cookies"` in `permissions`.
2. Rebuild and re-sign the XPI if needed.
3. Reinstall the signed XPI, or reload the temporary add-on in development mode.

### Firefox Is Not Installed

Check:

- Firefox is installed.
- `firefox.exe` is available in PATH.
- Firefox is installed in `C:\Program Files\Mozilla Firefox\`.

### URLs Did Not Open

Check:

- The URL field is not empty.
- The URL starts with `http://` or `https://`.
- Container Helper Extension is enabled.
- The target Container exists.
