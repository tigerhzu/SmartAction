# SmartAction v1.1.0 Release Notes

SmartAction v1.1.0 focuses on long-running stability, lower resource usage, a more flexible action ring, and easier configuration.

## Download

Download `SmartAction-Release-v1.1.0.zip` from the GitHub Release and extract the complete folder before running `install.bat` or `SmartAction.exe`.

## Highlights

- Replaced the long-running keyboard hook with the Windows native `RegisterHotKey` API.
- Added drag rotation: hold an action and move the mouse clockwise or counter-clockwise.
- Increased the drag threshold so ordinary clicks do not accidentally rotate the Ring.
- Made both action bubbles and their text labels clickable.
- Added 12 zodiac constellation backgrounds.
- Added configurable constellation line and star colour.
- Removed connector lines between action bubbles for a cleaner constellation view.
- Added a Settings action type and a default Settings Ring entry.
- Restores an existing or minimized Settings window instead of silently doing nothing.
- Supports 9–10 directly visible Ring actions by adapting slot spacing.

## Performance and cleanup

- Removed duplicate emoji skin-tone variants while keeping the default skin tone.
- Reduced the runtime emoji database and lowered Emoji Picker loading pressure.
- Resized theme animation frames to 160 px for lower memory and decode cost.
- Loads full animation frames only for the active theme; previews remain static.
- Removed obsolete screenshots, unused styles, old platform stubs, duplicate assets, and internal planning documents from the application bundle.
- Switched the packaged Qt dependency to `PySide6-Essentials` and excluded unused Qt modules/plugins.

## Configuration compatibility

- Existing v1.0 action files are upgraded to schema v1.1 automatically.
- User actions are preserved during migration.
- A missing Settings action is inserted into a visible Ring position without duplicating an existing Settings entry.
- Constellation selection and colour are included in profile import/export.

## Validation

- 13 automated regression tests cover native hotkey parsing, emoji filtering, constellation data, Settings actions, config migration, Ring clicking/rotation, overflow slots, and theme loading.
- The Windows package was rebuilt with PyInstaller and validated through the release packaging checks.
- The packaged executable was manually verified by opening the Ring with F24 and launching Settings from its label card.
