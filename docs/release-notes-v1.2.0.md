# SmartAction v1.2.0 Release Notes

SmartAction v1.2.0 improves multi-monitor workflows and adds practical organisation tools to Client Workspace.

## Download

Download `SmartAction-Release-v1.2.0.zip` from the GitHub Release and extract the complete folder before running `install.bat` or `SmartAction.exe`.

## Multi-monitor improvements

- Settings, PowerShell Library and Client Workspace now open on the monitor where the Ring was used.
- Existing or minimized windows are restored and moved to the current working monitor.
- Ring-launched input forms, PowerShell forms and Environment Check dialogs follow the same monitor placement.
- Window sizing and centring support monitors positioned to the left or above the primary display.

## Client Workspace folders and ordering

- Added folders for grouping clients by engineer, project, region or any other category.
- Clients can be dragged up or down to persist a custom order.
- Clients can be dragged directly into another folder.
- New and existing clients can select a folder in the client editor.
- Folders can be created, renamed and deleted.
- Deleting a folder keeps its clients and moves them to `Unassigned`.
- Existing Client Workspace 1.0 data is migrated safely to the 1.1 schema.
- Import and export support both legacy 1.0 input and the new 1.1 folder structure.

## Validation

- 17 automated regression tests cover hotkeys, emoji filtering, constellation settings, Ring interaction, theme loading, multi-monitor placement, Client Workspace migration, folders and drag ordering.
- Ruff, compile checks and release-package validation passed.
- The packaged Windows application completed a startup smoke test.
