# SmartAction Firefox Native Messaging Host

This host bridges SmartAction and the Container Helper Extension.

SmartAction writes launch requests here:

```text
%LOCALAPPDATA%/SmartAction/firefox_helper/pending_launch.json
```

The native host sends that request to the Firefox extension over Firefox Native Messaging. The extension opens the URLs in the requested Firefox Container and sends a result back. The host writes the result here:

```text
%LOCALAPPDATA%/SmartAction/firefox_helper/last_result.json
```

Logs are written to:

```text
%LOCALAPPDATA%/SmartAction/firefox_helper/helper.log
```

## Install on Windows

Run this from the SmartAction project folder or from the packaged external `native/firefox_helper_host` folder:

```powershell
python native/firefox_helper_host/install_host_windows.py
```

The installer copies the host files to a stable location:

```text
%LOCALAPPDATA%/SmartAction/firefox_helper_host/
```

It then creates:

- `%LOCALAPPDATA%/SmartAction/firefox_helper_host/smartaction_firefox_host.py`
- `%LOCALAPPDATA%/SmartAction/firefox_helper_host/smartaction_firefox_host.cmd`
- `%LOCALAPPDATA%/SmartAction/firefox_helper_host/host_manifest.json`
- Registry key:
  `HKCU\Software\Mozilla\NativeMessagingHosts\smartaction_firefox_helper`

The Firefox extension id must be:

```text
smartaction-container-helper@naughtytiger06.local
```
