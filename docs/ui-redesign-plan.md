# SmartAction UI 鏀圭増瑷堢暙

Date: 2026-07-09

## Current Actual Phase Status - 2026-07-10 Phase 5

- Latest executed phase: **Phase 5 - Final QA / Release Readiness**.
- Formal entry remains: `Set-Location C:\Users\naugh\smartaction; python -m app.main`.
- Phase 5 status: **completed for automated/code-level QA; manual desktop QA still required**.
- Backup created for this phase: `backups/ui-redesign-before-phase5/`.
- Files modified in Phase 5:
  - `docs/ui-redesign-plan.md`
  - `SmartAction_功能架構與使用指南.md`
  - `SmartAction_架構與功能說明.md`
- No Python code was changed in Phase 5.
- Automated verification completed:
  - `python -m compileall -q app core ui platforms native\firefox_helper_host tools` passed.
  - `python -m app.main` reached the formal entry path and exited cleanly with code 0 because an existing SmartAction instance already holds `data/smartaction.lock`.
  - Offscreen construction passed for:
    - `TrayIcon`
    - `StartupSplash`
    - `RingWindow`
    - `SettingsWindow`
    - `PowerShellLibraryWindow`
    - `ClientWorkspaceWindow`
    - `EnvironmentCheckResultDialog`
    - `HelpModal`
    - `EmojiPickerDialog`
    - `HotkeyPickerDialog`
    - `AddLocalUserForm`
    - `JoinDomainForm`
    - `ScriptEditorDialog`
    - `ParameterDialog`
    - `ConfirmRunDialog`
    - `ResultDialog`
  - PowerShell Library Ring action dispatch was smoke-tested with a callback and correctly invoked the library opener path.
  - Action registry smoke test passed for the registered executable action handlers:
    - `app`
    - `client_workspace`
    - `command`
    - `environment_check`
    - `form`
    - `paste`
    - `powershell`
    - `powershell_library`
    - `ps_form`
    - `submenu`
    - `url`
  - JSON parse smoke test passed for:
    - `config/actions.json`
    - `resources/config.json`
    - `data/powershell_library.json`
    - `data/client_workspaces.json`
- Manual QA still required before release:
  - Real Windows tray menu visual inspection and About dialog click.
  - Real startup splash playback with the actual MP4/GIF asset.
  - Real hotkey trigger for Ring open/close and click-outside behavior.
  - Real 1080p / 2K / DPI scaling checks.
  - Real F11 / Esc checks for Settings, PowerShell Library, Client Workspace, Environment Check, and Help.
  - Real functional clicks for Settings Save/Cancel/Import/Export, PowerShell Library add/edit/run, Client Workspace launch/import/export, Emoji Picker selection/favorites, Hotkey Picker apply/clear.
  - Real regression check for existing action types that can affect the machine, especially Command, PowerShell, PS Form, Join Domain, and Add Local User.
- Known limitations after Phase 5:
  - PowerShell Library action type opens the PowerShell Library window only; it still does **not** bind and directly execute a single library script from the Ring.
  - `ui/main_window.py` remains outside the formal displayed UI flow.
  - This workspace is currently not a Git repository, so `git status` / `git diff` cannot be used here for source-control verification.
- Explicitly not changed in Phase 5:
  - `ui/main_window.py`
  - `app/main.py`
  - `app/application.py`
  - `core/action_runner.py`
  - `core/actions/*`
  - `build/`
  - `dist/`

## Current Actual Phase Status - 2026-07-10

- Latest executed phase: **Phase 4 - Tray / startup polish**.
- Formal entry remains: `Set-Location C:\Users\naugh\smartaction; python -m app.main`.
- Phase 4 status: **completed with code-level and offscreen verification**.
- Backup created for this phase: `backups/ui-redesign-before-phase4/`.
- Files modified in Phase 4:
  - `ui/tray_icon.py`
  - `ui/startup_splash.py`
  - `docs/ui-redesign-plan.md`
  - `SmartAction_功能架構與使用指南.md`
  - `SmartAction_架構與功能說明.md`
- Phase 4 completed work:
  - System tray icon was restyled from the old flat ember/white-dot icon into a dark ember radial launcher icon with a small neon accent.
  - Tray context menu now uses the shared dark neon productivity palette for background, hover, separator, and text states.
  - About dialog no longer uses the default bright/native message box path; it now uses a dark themed QMessageBox while keeping the same informational purpose.
  - Startup splash now uses screen `availableGeometry()` through `ui/window_utils.py`, clamps its initial size for smaller screens, and centers itself on the active screen.
  - Startup splash media host, status text, and Skip button were aligned with the existing dark neon token system.
  - GIF and image fallback scaling were stabilized so fallback media follows the splash host size.
- Verification completed:
  - `python -m py_compile ui\tray_icon.py ui\startup_splash.py` passed.
  - Offscreen construction passed for `TrayIcon`, tray menu action list, generated tray icon, and `StartupSplash`.
  - `python -m app.main` was attempted after the changes. It exited cleanly with code 0 because an existing SmartAction instance already holds `data/smartaction.lock`; this still requires real desktop tray/splash QA.
- Not completed in Phase 4:
  - Real system tray visual inspection on Windows desktop is still required.
  - Real startup splash playback test with the actual MP4/GIF asset is still required.
  - No Phase 5 work was started.
- Explicitly not changed in Phase 4:
  - `ui/main_window.py`
  - `app/main.py`
  - `app/application.py`
  - `core/action_runner.py`
  - `core/actions/*`
  - `build/`
  - `dist/`

## Current Actual Phase Status - 2026-07-09

- Latest executed phase: **Phase 3.5 - Feature Integration / Display Stability**.
- Formal entry remains: `Set-Location C:\Users\naugh\smartaction; python -m app.main`.
- Phase 3.5 status: **partially completed with code-level and offscreen verification**.
- Backup created for this phase: `backups/ui-redesign-before-phase3-5/`.
- Files modified in Phase 3.5:
  - `app/application.py`
  - `core/actions/powershell_library_action.py`
  - `core/actions_config.py`
  - `ui/window_utils.py`
  - `ui/settings_window.py`
  - `ui/ring_ui.py`
  - `ui/powershell_library_window.py`
  - `ui/client_workspace_window.py`
  - `ui/environment_check_window.py`
  - `ui/help_modal.py`
  - `ui/emoji_picker.py`
  - `ui/hotkey_picker.py`
  - `docs/ui-redesign-plan.md`
- Phase 3.5 completed work:
  - PowerShell Library can now be used as a Ring action type that opens the PowerShell Library window.
  - The `powershell_library` Ring action no longer directly executes a stored script id.
  - Settings can select `PowerShell Library` without requiring a script selection or target field.
  - Main/support dialogs now use screen `availableGeometry()` based initial sizing and centering through `ui/window_utils.py`.
  - Settings, PowerShell Library, Client Workspace, Environment Check, and Help Modal support F11 fullscreen toggle and Esc to leave fullscreen.
  - Emoji Picker and Hotkey Picker use adaptive initial sizing while preserving their existing Enter/Esc picker behavior.
  - Ring container is clamped to the current screen available area and scales its painter/hit-test coordinates when the available area is smaller than the design size.
- Verification completed:
  - `python -m py_compile` passed for all modified Phase 3.5 Python files.
  - Offscreen construction passed for Settings, PowerShell Library, Client Workspace, Environment Check, Help Modal, Emoji Picker, Hotkey Picker, and Ring.
  - Offscreen action dispatch confirmed that `powershell_library` invokes the PowerShell Library opener callback.
  - `python -m app.main` was attempted. It exited cleanly with code 0 because an existing SmartAction instance already holds `data/smartaction.lock`; this does not replace manual tray/hotkey QA.
- Not completed in Phase 3.5:
  - PowerShell Library does **not** support binding a single library script to a Ring action and executing it directly.
  - Real 1080p and 2K monitor manual visual verification is still required.
  - Manual F11/Esc verification is still required on a real desktop.
  - Manual regression testing for all existing action types is still required.
- Explicitly not changed in Phase 3.5:
  - `ui/main_window.py`
  - `build/`
  - `dist/`
  - broad `app/main.py` startup flow
  - broad `core/action_runner.py` dispatch logic

## Previous Phase Status - 2026-07-09

- Latest executed phase: **Phase 3 - Supporting dialogs QA / polish**.
- Formal entry remains: `Set-Location C:\Users\naugh\smartaction; python -m app.main`.
- Phase 3 status: **partially completed with code-level and offscreen dialog verification**.
- Backup created for this phase: `backups/ui-redesign-before-phase3/`.
- Files modified in Phase 3:
  - `ui/powershell_library_window.py`
  - `ui/client_workspace_window.py`
  - `ui/environment_check_window.py`
  - `ui/help_modal.py`
  - `ui/emoji_picker.py`
  - `ui/hotkey_picker.py`
  - `ui/widgets.py`
  - `ui/forms/base_form.py`
  - `ui/forms/add_local_user_form.py`
  - `ui/forms/join_domain_form.py`
  - `docs/ui-redesign-plan.md`
- Phase 3 completed work:
  - Unified supporting-dialog hover, pressed, disabled, focus, scrollbar, table/list, checkbox, and message-box visual states.
  - Kept the existing workflows intact for PowerShell Library, Client Workspace, Environment Check, Help, Emoji Picker, Hotkey Picker, and PowerShell forms.
  - Replaced remaining native bright `QMessageBox.warning/information/question` calls in Phase 3 surfaces with dark themed equivalents.
  - Improved BaseForm status feedback with dark semantic success/error/waiting surfaces instead of text-only color changes.
- Verification completed:
  - `python -m py_compile` passed for all modified Phase 3 Python files.
  - Offscreen construction passed for PowerShell Library, its editor/parameter/confirm/result dialogs, Client Workspace, Environment Check, Help, Emoji Picker, Hotkey Picker, Add Local User Form, and Join Domain Form.
  - `python -m app.main` was attempted. It exited cleanly with code 0 because an existing SmartAction instance already holds `data/smartaction.lock`; this confirms no immediate crash in import/startup path, but does not replace manual tray/window QA.
- Not fully verified yet:
  - Manual visual inspection on a real desktop for every Phase 3 window.
  - Manual functional clicks for PowerShell script add/edit/delete/run, Client Workspace import/export/launch, Emoji Picker selection/favorites, Hotkey Picker apply/clear, Environment Check copy, and Help scrolling.
  - Real message box visual check for `ui/forms/join_domain_form.py` success path, because that flow can trigger a reboot prompt and was not executed.
- Explicitly not changed in Phase 3:
  - `ui/main_window.py`
  - `app/main.py`
  - `app/application.py`
  - `core/actions/*`
  - `core/action_runner.py`
  - `build/`
  - `dist/`

## Current Phase Status - 2026-07-09

- Phase executed in the latest pass: **Phase 1 - Settings window visual redesign**.
- Formal entry confirmed: `Set-Location C:\Users\naugh\smartaction; python -m app.main`.
- Formal UI target updated: `ui/settings_window.py`.
- Backup created before this phase: `backups/ui-redesign-before-next-phase/`.
- Scope completed in this pass:
  - Dark neon productivity dashboard styling for Settings.
  - Unified field, combobox, checkbox, table, sidebar, and button visual states.
  - Actions sidebar selected/hover states refined.
  - Sub Actions table restyled as a dark card-like work surface.
  - Save/Cancel/Add/Delete/Export/Import/Set Hotkey controls aligned to one visual system.
- Explicitly not changed:
  - `ui/main_window.py`.
  - `app/main.py` and `app/application.py` startup flow.
  - Action execution logic.
  - Hotkey/theme/profile save/import/export behavior.
渚濇摎锛歚docs/ui-audit.md` 鐨勬巸鎻忕祼鏋?鐙€鎱嬶細**搂1鈥撀?銆伮?銆伮?1 step 1鈥?/9 宸插畬鎴愪甫椹楄瓑锛浡? / 搂11 step 7鈥?锛圧ing 鍏夋殘鑸囧嫊鏁堣鍙冿級灏氭湭闁嬪銆?* 瑭崇窗浜ゆ帴鍏у瑕?`docs/ui-redesign-handoff.md`銆?
---

## 0. 瑷▓瀹氫綅锛堜竴鍙ヨ┍锛?
**"Cut steel, not rounded plastic."** 涓€鏀纾ㄥ埄鐨勫伐妤伐鍏凤紝榛戞洔宀╁簳鑹?+ 涓€閬撶惀鐝€鑹茬殑鍒€閶掞紝鑰屼笉鏄張涓€鍊嬬传鑹叉几灞ょ殑 AI SaaS 琛ㄥ柈銆傚搧鐗岄尐榛炴部鐢ㄥ皥妗堣！宸茬稉瀛樺湪鐨?`tiger` 涓婚锛坄core/theme.py` 鐨?`preview_color: "#F97316"`锛宍assets/themes/tiger/` 宸叉湁灏嶆噳缇庤璩囨簮锛夆€斺€斾笉鏄柊鐧兼槑涓€鍊嬪悏绁ョ墿锛屾槸鎶婂畠寰炪€屼簲閬镐竴鐨勫叾涓竴鍊嬩富椤屻€嶅崌鏍兼垚鏁村€?App 鐨勯爯瑷韩鍒嗐€?
绨藉悕鍏冪礌锛坰ignature锛屾暣鍊嬫敼鐗堝彧鍦ㄩ€欎竴浠朵簨涓婂ぇ鑶斤紝鍏堕淇濇寔鍏嬪埗锛夛細**鍠竴鍒囪锛坰ingle corner-cut锛?*銆傛墍鏈夐潰鏉裤€佹寜閳曘€佸皪瑭辨妯欓鍒楃殑鍙充笂瑙掍互 45掳 鍒囨帀涓€灏忓锛?鈥?0px锛夛紝鍙栦唬鐩墠鍒拌檿閮芥槸鐨勫湏瑙掋€傚懠鎳夈€岃鍓婇亷鐨勯嫾鏉?鐖棔鍒囧彛銆嶏紝鑰屼笉鏄椋炬€х殑鍦栨銆?
> 鈿狅笍 **鍩疯寰屼慨姝?*锛氶€欒！鍘熸湰鍋囪ō鍒囪鍙互鐢ㄣ€岀磾 CSS/QSS 閭婃铏曠悊銆嶅仛鍒扳€斺€?*閫欏€嬪亣瑷槸閷殑**锛孮t Style Sheet 鍙敮鎻?`border-radius`锛堝湏瑙掞級锛屾矑鏈変换浣曞爆鎬ц兘鐣换鎰忚搴︾殑鍒囪銆傚闅涘彧鏈夋湰渚嗗氨鐢?`paintEvent` 鑷躬鐨?`_ThemeCard`锛圫ettings 涓婚鍗★級鍋氬埌浜嗙湡姝ｅ垏瑙掞紝鍏堕鎵€鏈夋婧?`QPushButton`/`QLineEdit` 閫欐閮芥敼鐢ㄥ皬鍦撹锛?px锛変唬鏇裤€傝┏瑕?`docs/ui-redesign-handoff.md` 搂4銆?
---

## 1. 瑕栬棰ㄦ牸 鉁?宸插畬鎴?
- **鍩鸿**锛氭繁鑹茬偤涓伙紙鐒℃泛鑹叉ā寮忥級锛屽喎榛戣儗鏅?+ 鏆栨鍒€閶掕壊 + 鏆栫櫧鏂囧瓧銆傞伩鍏嶇洰鍓嶃€岀櫧搴曡〃鍠?+ 娣虹传榛炵洞銆嶇殑闋愯ō Qt 瑙€鎰熴€?- **灞ゆ闈犲皪姣旇垏閭婃锛屼笉闈犻櫚褰辨ā绯?*锛氱洰鍓?`theme_painter.py` 澶ч噺浣跨敤鏌斿拰鏀惧皠鐙€ glow锛堟ā绯婂厜鏆堬級锛屾敼鐗堟柟鍚戞槸绺皬妯＄硦鍗婂緫銆佹媺楂橀倞绶ｅ皪姣旓紝鐢ㄣ€岄噾灞倞绶ｅ弽鍏夈€嶇殑涓€姊?1px 楂樺厜绶氬彇浠ｅぇ闈㈢鍏夋殘鈥斺€旇唱鎰熸洿鍍忔墦纾ㄩ亷鐨勯噾灞紝涓嶆槸闇撹櫣鐕堛€?- **绂佺敤娓呭柈锛堝欢绾屼娇鐢ㄨ€呴渶姹傦級**锛氱传鑹叉几灞ゃ€佺磾鐧借〃鍠儗鏅€?3px 浠ヤ笅鐣朵綔闋愯ō鏈枃瀛楃礆銆佸崱鐗囧鍗＄墖锛坰ection 鐢ㄥ垎闅旂窔 + 妯欑堡锛屼笉瑕佸啀鍖呬竴灞ゆ湁搴曡壊/闄板奖鐨勫収灞ゅ崱鐗囷級銆佸ぇ鏂?8px 鐨勫湏瑙掋€佺劇闄愬惊鐠扮殑鐧煎厜鍕曠暙銆?- **鏃㈡湁 dark console 鍗€濉婏紙PowerShell Library 琛ㄦ牸銆丒nvironment Check 杓稿嚭銆丼ettings 涓婚鍒楋級涓嶇敤鍐嶅柈鐛ㄨō瑷?* 鈥斺€?瀹冨€戝師鏈氨鏄繁鑹诧紝鏀圭増寰屽崌绱氭垚銆屽叏 App 绲变竴鐨勬繁鑹茬郴绲便€嶇殑涓€閮ㄥ垎锛岃€屼笉鏄鎬殑娣辫壊瀛ゅ扯銆?
## 2. 鑹插僵绯荤当 鉁?宸插畬鎴愶紙`ui/style_tokens.py`锛?3 鍊嬫獢妗堝鐢級

鏂板涓€浠藉叡鐢?token锛堝缓璀版柊妾旀 `ui/style_tokens.py`锛岀磾璩囨枡锛屼緵鎵€鏈?QSS 瀛椾覆濂楃敤锛屼笉鏀硅畩浠讳綍 widget 閭忚集锛夛細

| Token | Hex | 鐢ㄩ€?|
|---|---|---|
| `void` | `#0B0D10` | App / 灏嶈┍妗嗘渶搴曞堡鑳屾櫙 |
| `charcoal` | `#15181D` | 闈㈡澘銆佽几鍏ユ銆佽〃鏍艰儗鏅紙姣?void 浜竴闅庯級 |
| `steel` | `#1E2229` | 鍐嶄寒涓€闅庯細hover 鑳屾櫙銆乨isabled 鍏冧欢搴曡壊 |
| `ash` | `#2A2F38` | 鎵€鏈?1px 鍒嗛殧绶?/ 閭婃 |
| `bone` | `#ECE8E1` | 涓昏鏂囧瓧锛堟殩鐧斤紝閬垮厤姝荤櫧鍒虹溂锛?|
| `fog` | `#9AA0AA` | 娆¤ / 瑾槑鏂囧瓧銆乸laceholder |
| `ember` | `#F2760B` | 鍝佺墝涓昏壊锛圱iger 姗橈級鈥斺€?涓绘寜閳曘€侀伕鍙栫媭鎱嬨€乫ocus |
| `ember-hover` | `#FF8B2E` | hover 鏅傛彁浜?|
| `ember-pressed` | `#C2570A` | 鎸変笅 / active |
| `ember-wash` | `rgba(242,118,11,0.12)` | 妤垫贰姗樿壊搴曪紙閬稿彇鍒楄儗鏅級锛岄潪鐧煎厜 |
| `signal-red` | `#E5484D` | 鍗遍毆鎿嶄綔锛堟部鐢ㄧ従鏈?`#DC2626` 绯昏獮鎰忥紝鐣ヨ鏆栦互璨艰繎鏁撮珨鑹叉韩锛?|
| `signal-green` | `#3FB27F` | 鎴愬姛 / 宸查€ｇ窔鐙€鎱?|
| `signal-amber` | `#D9932A` | 璀﹀憡鐙€鎱?|

鏄庣⒑娣樻卑锛歚#5B21B6`/`#6D28D9`/`#4C1D95`锛堢传鑹蹭富鑹诧級銆乣#2563EB`/`#1D4ED8`锛堝彟涓€鏀棈鑹蹭富鑹诧紝渚嗚嚜 `widgets.py`/`forms/base_form.py`/legacy pages锛夆€斺€?绲变竴鎴愬柈涓€ `ember` 鍝佺墝鑹诧紝瑙ｆ焙 audit 搂3.2 鎻愬埌鐨勯洐鍝佺墝鑹插晱椤屻€?
`core/theme.py` 鐨?5 鍊?ring 涓婚淇濈暀锛坧urple / tiger / ice / lava / cosmic 浠嶆槸浣跨敤鑰呭彲閬哥殑妗岄潰涓婚锛夛紝浣嗭細
1. `DEFAULT_THEME` 寰?`"purple"` 鏀圭偤 `"tiger"`銆?2. `THEME_ORDER` 鎶?`"tiger"` 绉诲埌绗竴浣嶏紝Settings 鐨勪富椤岄伕鎿囧垪绗竴寮靛崱闋愯ō灏辨槸 Tiger銆?3. 淇 audit 搂3.5 鎻愬埌鐨?`theme_painter.py` `_theme_colors()` 鑸?`core/theme.py` 鐨勯噸瑜囪壊绁ㄢ€斺€斿叐铏曟暩鍊艰鍦ㄥ悓涓€娆?commit 瑁′竴璧锋敼锛屼甫寤鸿涔嬪緦璁?`_theme_colors()` 鐩存帴 `import` `core.theme.THEMES` 鑰屼笉鏄墜鍕曠董璀风浜屼唤鎷疯矟锛堥€欏爆鏂间綆棰ㄩ毆鐨勭▼寮忕⒓鏁翠降锛屼笉鏀硅畩瑕栬杓稿嚭锛夈€?
## 3. 瀛楅珨鑸囧瓧绱?鈿狅笍 閮ㄥ垎瀹屾垚 鈥斺€?Oswald 宸插収宓岋紙`core/fonts.py`锛変笖鍙纰鸿級鍏ワ紝浣?*灏氭湭濂楃敤鍒颁换浣曠暙闈?*锛涘瓧绱?闁撹窛 token 宸插缓绔嬫柤 `ui/style_tokens.py`锛屽鏁哥暙闈㈠彧鎻涗簡椤忚壊锛岄倓娌掓湁閫愪竴濂楃敤鍒版瘡鍊嬪瓧绱?
鐩墠瀹屽叏娌掓湁鎸囧畾瀛楀瀷瀹舵棌锛屽叏閮ㄥ悆 Windows 闋愯ō瀛楀瀷锛涘瓧绱氬叏 App 鍙湁 11鈥?4px 骞剧ó锛岀己涔忎竴鑷寸殑姣斾緥灏恒€?
**瀛楀瀷瀹舵棌锛堝叐鏀鑹诧紝鍏嬪埗浣跨敤锛夛細**
- **UI 鏈枃** 鈥?`Segoe UI Variable`锛圵in11 鍘熺敓璁婃暩瀛楅噸锛屾壘涓嶅埌灏?fallback `Segoe UI`锛夈€傜悊鐢憋細涓嶉澶栫秮瀛楀瀷妾斻€佷笉澧炲姞 PyInstaller 鎵撳寘棰ㄩ毆锛屽悓鏅傛瘮闋愯ō `Segoe UI` 鏈夋洿濂界殑瀛楅噸灞ゆ锛屻€屽皧閲?Windows 骞冲彴銆嶆湰韬氨鏄竴绋笉钀戒織濂楃殑閬告搰锛堜笉鏄毃渚垮涓€鍊嬬恫闋侀ⅷ鏍煎瓧鍨嬶級銆?- **妯欓 / 鍝佺墝瀛楋紙鍍呯敤鏂煎皪瑭辨澶ф椤屻€乺ing 涓績鏂囧瓧銆乤bout 闋佸搧鐗屽瓧锛屽叾椁樹竴寰嬩笉鐢級** 鈥?`Oswald`锛圫IL Open Font License锛屽彲鍚堟硶鍏у祵锛屽伐妤劅绐勯珨瀛楋紝PyInstaller 鍏у祵鏂瑰紡鑸囩従鏈?`assets/` 璩囨簮鎵撳寘娴佺▼鐩稿悓锛夈€傚叏澶у銆佸井澧炲瓧璺濅娇鐢紝濉戦€犮€宲ower tool銆嶇殑璀樺垾搴︼紝浣嗗彧鍑虹従鍦ㄥ皯鏁稿咕鍊嬪湴鏂癸紝涓嶆渻璁婃垚鍒拌檿閮芥槸鐨勮椋惧瓧銆?- **绛夊 / console** 鈥?缍寔鐝炬湁 `Consolas, "Cascadia Mono", monospace`锛圥owerShell Library銆丒nvironment Check 杓稿嚭闈㈡澘宸插湪鐢紝涓嶇敤鏀癸級銆?
**瀛楃礆灏哄害锛?px 鐐哄熀婧栫殑姣斾緥灏猴紝鍙栦唬鐩墠閫愭獢妗堝悇鑷焙瀹氱殑浣滄硶锛夛細**

| Token | Size | 鐢ㄩ€?|
|---|---|---|
| `display` | 30px, Oswald, 澶у | Ring 涓績/姝¤繋鐣潰鍝佺墝瀛楋紙妤靛皯鐢級 |
| `h1` | 20px, Segoe UI Semibold | 灏嶈┍妗嗘椤?|
| `h2` | 14px, Segoe UI Semibold + ember 搴曠窔 4px | Section 妯欑堡 |
| `body` | 14px, Segoe UI Regular | 琛ㄥ柈娆勪綅銆佹寜閳曘€佷竴鑸枃瀛楋紙寰炵洰鍓嶇殑 13px 寰崌锛屽洖鎳夈€屽瓧澶皬銆嶇殑鍟忛锛?|
| `body-dense` | 13px | 琛ㄦ牸鍒椼€佹竻鍠垪锛堣硣瑷婂瘑搴﹁純楂樼殑鍦版柟淇濈暀杓冨皬瀛楃礆锛?|
| `caption` | 12px, fog 鑹?| 瑾槑鏂囧瓧銆佹瑕佹绫?|
| `micro` | 11px, 瀛楄窛 +0.4px, 澶у, fog 鑹?| 鐗堟湰铏熴€佹檪闁撴埑瑷?|
| `mono` | 13px, Cascadia Mono | Console/鑵虫湰杓稿嚭 |

## 4. 闁撹窛绯荤当 鉁?宸插畬鎴?
鏂板 4px 鍩烘簴鐨勯枔璺濆埢搴︼紝鍙栦唬鐩墠姣忓€嬫獢妗堝悇鑷墜瑾跨殑 padding 鏁稿瓧锛歚4 / 8 / 12 / 16 / 20 / 24 / 32 / 40`銆?
- 灏嶈┍妗嗗閭婅窛锛氱当涓€ `24px`锛堢洰鍓嶅鏁告槸 `16鈥?0px` 涓嶇瓑锛夈€?- Section 涔嬮枔鍨傜洿闁撹窛锛歚24px` + 1px `ash` 鍒嗛殧绶氾紙涓嶅啀鐢ㄦ湁搴曡壊鐨勫収灞ゅ崱鐗囧寘 section锛夈€?- 琛ㄥ柈娆勪綅鍨傜洿闁撹窛锛歚12px`銆?- 鎸夐垥鏈€灏忛珮搴︼細寰炵洰鍓?`32px` 鎻愬崌鍒?`36px`锛堟洿濂芥寜銆佹洿绗﹀悎銆岀┅瀹氥€嶇殑鎿嶄綔瑷存眰锛夛紱杓稿叆妗嗛珮搴﹀悓姝ュ緸 `30px` 鎻愬崌鍒?`34鈥?6px`銆?- 琛ㄦ牸/娓呭柈鍒楅珮搴︼細`36px`锛堢洰鍓嶅亸绶婃箠锛宒rag-handle 鍛戒腑鍗€瑕佽窡钁楃瓑姣旇鏁达紝瑕?搂11 棰ㄩ毆鎻愰啋锛夈€?
## 5. 鎸夐垥妯ｅ紡 鈿狅笍 閮ㄥ垎瀹屾垚 鈥斺€?瑕?`docs/ui-redesign-handoff.md` 搂4

**瀵﹂殯绲愭灉璺熼€欒！鐨勮ō瑷堟湁钀藉樊锛岃閷勪竴涓嬫柟渚夸箣寰屽皪鐓э細** QSS 娌掕睛娉曠暙浠绘剰瑙掑害鍒囪锛屾墍浠ュ彧鏈?`_ThemeCard`锛圫ettings 涓婚鍗★紝鏈締灏辨槸鑷躬锛夊仛鍒颁簡鐪熸鐨勫垏瑙掞紱鍏堕鎵€鏈?`QPushButton` 閫欐鏀圭敤 3px 灏忓湏瑙掍唬鏇匡紝鑹插僵/hover/active/disabled 瑕忓墖鍓囧畬鍏ㄧ収涓嬮潰鐨勮鏍煎仛浜嗐€?
绲变竴鎸夐垥褰㈢媭瑾炶█锛氱煩褰€佸彸涓婅 6px 鍒囪锛堜笉鏄湏瑙掞級锛岀劇閭婃锛坧rimary/danger锛夋垨 1px `ash` 閭婃锛坰econdary锛夈€?
```
Primary锛堜緥锛氬劜瀛樸€佸煼琛岋級
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈺?鈹? Save changes 鈹?  background: ember   text: void锛堟繁鑹叉枃瀛楋紝姗樺簳閰嶆繁瀛楀皪姣旀渶寮凤級
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?  font: body, semibold

Secondary锛堜緥锛氬彇娑堬級
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈺?鈹?   Cancel     鈹?  background: transparent   border: 1px ash   text: bone
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
Danger锛堜緥锛氬埅闄ゃ€佸煼琛岄珮棰ㄩ毆鑵虫湰锛?鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈺?鈹?Delete action 鈹?  background: signal-red   text: bone
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?```

## 6. Hover / Active / Disabled 鐙€鎱嬭鍓?鈿狅笍 閮ㄥ垎瀹屾垚 鈥斺€?Hover/Active/Disabled/Selected 閮藉仛浜嗭紱涓嬮潰閫欐銆孎ocus銆嶇殑 2px 澶栨娌掓湁鍙﹀瀵︿綔锛岀洰鍓嶉嵉鐩?focus 鍙潬娆勪綅鏈韩 `:focus` 鏅傞倞妗嗚畩鎴?`ember`锛堣窡 hover 鍏辩敤鍚屼竴鍊嬭瑕虹窔绱級锛屾矑鏈夐澶栧仛涓€鍦堢崹绔嬬殑 focus outline

绲变竴瑕忓墖锛屽叏 App 濂楃敤鍚屼竴濂楅倧杓紙涓嶅啀姣忓€嬪皪瑭辨鍚勮嚜瀹氱京锛夛細

- **Hover**锛氳儗鏅彁浜竴闅庯紙渚嬶細`ember` 鈫?`ember-hover`锛沗charcoal` 鈫?`steel`锛夛紝secondary 鎸夐垥閭婃璁婃垚 `ember`銆傜姝㈡ā绯婂厜鏆堬紱鍙厑瑷辩磾鑹茶畩鍖?+ 闋傞儴 1px `rgba(255,255,255,.18)` 楂樺厜绶氾紙閲戝爆鍙嶅厜鎰燂級銆?- **Active/Pressed**锛氳儗鏅姞娣变竴闅庯紙`ember` 鈫?`ember-pressed`锛夛紝涓嶅姞閭婃璁婂寲锛岀郸浜恒€岃鎸変笅鍘汇€嶇殑鎰熻锛屼笉鍋氫綅绉诲嫊鐣€?- **Focus锛堥嵉鐩ょ劍榛烇紝灏嶉€欏€嬪伐鍏风壒鍒ラ噸瑕侊紝鍥犵偤 hotkey picker / emoji picker 澶ч噺閸电洡鎿嶄綔锛?*锛?px `ember` 瀵︾窔澶栨锛宍offset 2px`锛屼换浣曞彲閸电洡鎿嶄綔鍏冧欢閮借鏈夋竻妤氬彲瑕嬬殑 focus 妯ｅ紡锛堢洰鍓嶅鏁稿皪瑭辨瀹屽叏娌掓湁鑷▊ focus 妯ｅ紡锛屽彧鍚?Qt 闋愯ō锛夈€?- **Disabled**锛氬幓褰╁害锛屽彧鍓?`steel` 鑳屾櫙 + `fog` 鏂囧瓧锛堥檷鍒?50% 閫忔槑搴︼級锛屼笉鍙嚭鐝句换浣?`ember` 鐥曡贰銆?- **Selected锛堟竻鍠垪銆乼heme card銆乮con cell锛?*锛氬乏鍋?3px `ember` 鑹叉 + `ember-wash` 鑳屾櫙锛岃€屼笉鏄儚鐩墠 `_ThemeCard` 鐢ㄦ暣鍦堢櫦鍏夐倞妗嗭紱淇濇寔鏂囧瓧鍙畝鎬э紝閬垮厤銆岀硸鏋滄劅銆嶃€?
## 7. Settings 闋?Layout 鉁?宸插畬鎴?
鐝炬硜锛坄ui/settings_window.py`锛変笉鏄闋佸紡瑷畾涓績锛岃€屾槸銆屽嫊浣滄竻鍠?CRUD 绶ㄨ集鍣ㄣ€嶏細宸﹀伌 action 娓呭柈銆佸彸鍋磋〃鍠€佷笅鏂逛富椤岄伕鎿囧垪銆乭otkey 鍒椼€乸rofile 鍖叆/鍖嚭鍒楀叏閮ㄥ鍦ㄥ悓涓€鍊嬪皪瑭辨鍨傜洿鎹插嫊銆傛敼鐗?*涓嶆柊澧炲垎闋佺祼妲?*锛堥偅鏄灦妲嬫敼鍕曪紝涓嶅湪閫欐瑕栬鏀圭増绡勫湇锛夛紝鑰屾槸鍦ㄦ棦鏈夐鏋朵笂鍋氳瑕烘暣鐞嗭細

```
鈹?SmartAction Settings 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈺?鈹?鈹屸攢 Actions 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹屸攢 Edit action 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹愨攤
鈹?鈹?鈰嫯 馃惎 Tiger tools   鈹?鈹?Label      [___________]     鈹傗攤
鈹?鈹?鈰嫯 馃寪 Client sites  鈹?鈹?Short label[___]              鈹傗攤
鈹?鈹?鈰嫯 馃捇 PS Library    鈹?鈹?Icon       [馃惎][Choose鈥      鈹傗攤
鈹?鈹?鈰嫯 馃搧 IT Folder     鈹?鈹?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€     鈹傗攤
鈹?鈹?                    鈹?鈹?Type       [Command 鈻綸        鈹傗攤
鈹?鈹?[+ Add action]      鈹?鈹?Target     [___________]      鈹傗攤
鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?Sub-actions [table...]        鈹傗攤
鈹?                         鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹樷攤
鈹?鈹€鈹€ Theme 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€  鈹?鈹? [馃惎Tiger*][Ice][Lava][Purple][Cosmic]                    鈹?鈹?鈹€鈹€ Hotkey 鈹€鈹€  Ctrl+Alt+Space          [Change鈥           鈹?鈹?鈹€鈹€ Profile 鈹€鈹€ [Import] [Export]          [Cancel] [Save]  鈹?鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?```

- 宸﹀伌娓呭柈缍寔 `_ActionListWidget` 鐨?drag-handle 姗熷埗涓嶅嫊锛屽彧鎻涜壊锛坄charcoal` 鑳屾櫙銆侀伕鍙栧垪 `ember-wash` + 宸﹀伌鑹叉锛夈€?- 鍙冲伌琛ㄥ柈鍏х殑鍗€濉婃敼鐢ㄣ€?px `ash` 鍒嗛殧绶?+ `h2` 妯欑堡銆嶅垎娈碉紝鍙栨秷浠讳綍鍏у堡鐧借壊鍗＄墖鑳屾櫙銆?- 涓婚鍒楃殑 `_ThemeCard` 鍔犲ぇ鍒?`120脳140`锛屽鐢ㄥ柈涓€鍒囪锛岄伕鍙栫媭鎱嬫敼鎴愬乏涓婅灏忓嬀閬?+ 搴曢儴 `ember` 鑹叉锛屽彇娑堢洰鍓嶆暣鍦堢櫦鍏夐倞妗嗐€?- 瑕栫獥闋愯ō灏哄锛歚resize(1100, 1100)` 鐩墠鎺ヨ繎姝ｆ柟褰€佹氮璨诲瀭鐩寸┖闁擄紝鏀圭偤 `resize(1180, 760)`锛宍setMinimumSize(980, 640)`锛堝師鏈?`900, 620`锛屽井鍗囦互瀹圭磵鏂扮殑瀛楃礆鑸囬枔璺?銆?
## 8. Radial Menu锛圧ing锛夊嫊鏁?鉂?灏氭湭闁嬪

Ring 鐨?`paintEvent`/鍛戒腑娓│鑰﹀悎鏄叏灏堟棰ㄩ毆鏈€楂樼殑鍗€濉婏紙瑕?audit 搂6锛夛紝閫欐鏀圭増**涓嶉噸瀵嫊鐣垨骞句綍绯荤当**锛屽彧瑾挎暣鏃㈡湁鍙冩暩鑸囧皯閲忕枈鍔犳晥鏋滐細

- **闁嬪牬鍕曠暙**锛氫繚鐣欑従鏈?`QParallelAnimationGroup`锛坥pacity 180ms OutCubic + scale 200ms OutBack锛夛紝浣嗛檷浣?`OutBack` 鐨?overshoot 骞呭害锛岃畵褰堝嚭鎰熷緸銆孮 褰堝彲鎰涖€嶈畩鎴愩€屾姊板紡鍒颁綅鎰熴€嶁€斺€旀洿璨艰繎銆宲ower/fast銆嶈€屼笉鏄€岀帺鍏枫€嶃€?- **姣忓€?slot 鐨勯€插牬鍔犱笂灏忓箙搴︽檪闁撳樊锛坰tagger锛?*锛氫緷 slot index 鐤婂姞 8鈥?2ms 鐨勫欢閬诧紝鍋氬嚭銆屼緷搴忛粸浜€嶇殑绡€濂忔劅銆?*閫欏彧褰遍熆绻＝鏅傜殑閫忔槑搴?绺斁鎻掑€硷紝涓嶆敼璁?`_slot_centre()` 搴ф鎴栧懡涓脯瑭﹂倧杓?*锛屼絾鍥犵偤 audit 宸叉寚鍑恒€屽嫊鐣腑瑕栬浣嶇疆鑸囧懡涓綅缃湰渚嗗氨鏈変簺寰笉鍚屾銆嶏紝閫欓爡鏀瑰嫊瀹屾垚寰屽繀闋堝娓嫋鏇?榛炴搳鏅傚簭锛屼笉鑳藉彧鐪嬭瑕恒€?- **涓績鎸夐垥**锛氶枊鍟熺灛闁撳姞涓€娆℃€э紙闈炲惊鐠帮級鐨?`ember` 鑹茬挵鑴堣锛堥€忔槑搴?0鈫?.4鈫?锛岀磩 900ms锛屽彧鎾竴娆★級锛屽彇浠ｇ洰鍓?`theme_painter.py` 鍋忔煍鍜岀殑甯搁鍏夋殘锛涗竴娆℃€у嫊鐣鍚堛€岄伩鍏嶅粔鍍瑰父椐愮櫦鍏夈€嶇殑闇€姹傘€?- **鍏夋殘瑾挎暣**锛歚draw_energy_bubble` 鐨勬斁灏勭媭 glow 鍗婂緫绺皬銆佷笉閫忔槑搴﹂檷浣庯紝鏀圭敤涓€姊濇洿娓呮櫚鐨勯爞閮ㄩ珮鍏夊姬绶氬仛銆岄噾灞倞绶ｅ弽鍏夈€嶏紝鍙栦唬澶ч潰绌嶆ā绯婂厜鏆堛€傞€欐槸瑾垮弮鏁革紙`theme_painter.py` 鍏ф棦鏈夌殑 gradient stop 鏁稿€硷級锛屼笉鏄噸瀵躬鍦栭倧杓€?- Folder 閫插嚭鐨?120ms pop 鍕曠暙缍寔涓嶅嫊锛坅udit 鏈寚鍑哄晱椤岋紝鏀瑰嫊棰ㄩ毆澶ф柤鏀剁泭锛夈€?
## 9. Icon / Emoji Selector 鏀瑰杽 鉁?宸插畬鎴?
`ui/emoji_picker.py` 鐩墠鍔熻兘瀹屾暣锛堟悳灏嬨€佸垎椤炪€佹渶鎰涖€侀嵉鐩ゅ皫瑕斤級锛屽晱椤岀磾绮规槸瑕栬锛?
- 鏁撮珨寰炴泛鑹诧紙`#F8FAFC` 闋愯鑳屾櫙绛夛級鎻涙垚娣辫壊绯荤当锛氬皪瑭辨鑳屾櫙 `void`锛宨con 鏍煎瓙鑳屾櫙 `charcoal`锛宧over 閭婃 `ember`銆?- Icon 鏍煎瓙濂楃敤鍠竴鍒囪閫犲瀷锛岄伕鍙栫媭鎱嬬敤 `ember-wash` 鑳屾櫙 + 宸﹀伌鑹叉锛堝彇浠ｇ洰鍓嶄緷璩?Qt 鍕曟厠灞€?`[selected="true"]` 鐨勬泛鑹插簳閭忚集鈥斺€?*閬稿彇姗熷埗鏈韩涓嶅嫊**锛屽彧鎻涙ǎ寮忓瓧涓茶！鐨勯鑹插€硷級銆?- 鍒嗛鍋存瑒鐨勪綔鐢ㄤ腑鍒嗛锛屾敼鎴愬乏鍋?`ember` 鑹叉锛屽彇娑堟暣濉婅畩鑹茬殑浣滄硶锛堣窡娓呭柈閬稿彇鐙€鎱嬬当涓€瑾炶█锛夈€?- 鏀惰棌鏄熻櫉鏀规垚 `ember` 鍚岃壊绯荤殑鐞ョ弨鑹诧紝鑰屼笉鏄爯瑷粌鑹诧紝缍寔鑹插僵绯荤当涓€鑷淬€?- 鍛藉悕涓€鑷存€э細`emoji_picker.py` 鐢?`COLS = 8`锛宍hotkey_picker.py` 鍏х‖绶ㄧ⒓ `10`鈥斺€旈€欐鏀圭増鎶婂叐鑰呴兘鏀规垚鍏峰悕甯告暩锛堝悇鑷繚鐣欏師鏈瑒鏁革紝鍙槸涓嶅啀鏄瓟琛撴暩瀛楋級锛岄爢鎵嬩慨鎺?audit 搂3.9 鎻愬埌鐨勫皬鐟曠柕锛岄ⅷ闅サ浣庛€?
## 10. 瑕栫獥闋愯ō灏哄绺借 鉁?宸插畬鎴愶紙瀵﹂殯鏁稿€肩稉鎴湒瀵︽脯瑾挎暣锛岃窡鍘熶及瑷堟湁鍑哄叆锛?
| 瑕栫獥 | 鍘熸湰 min / resize | 瀵﹂殯鎺＄敤 min / resize | 瑾槑 |
|---|---|---|---|
| Settings | 900脳620 / 1100脳1100 | **980脳640 / 1180脳760** | 鐓у師瑷堢暙鍩疯 |
| Client Workspace | 980脳660 / 1080脳720 | **980脳660 / 1300脳760** | 鍘熶及銆屼笉璁娿€嶏紝浣嗗娓?8 鎸夐垥宸ュ叿鍒楄鍒囷紝鏀瑰涓︽妸娆¤鎸夐垥鎻涙垚灏忓昂瀵革紙瑕?handoff 搂4锛?|
| PowerShell Library锛堜富瑕栫獥锛?| 980脳680 / 1120脳760 | 涓嶈畩 | 瀵︽脯娌掑晱椤?|
| Emoji Picker | 760脳560 / 820脳620 | 涓嶈畩 | 瀵︽脯娌掑晱椤岋紝娌掓湁璁婃摖 |
| Hotkey Picker | 620脳540 / 660脳590 | **680脳560 / 740脳600** | 鍘熶及銆屼笉璁娿€嶏紝浣嗗娓?10 娆勬寜閸电恫鏍兼渶寰屼竴娆勮瑁佸垏锛屾敼瀵紙瑕?handoff 搂4锛?|
| Environment Check | 760脳620 / 鈥?| 涓嶈畩 | 宸插悎鐞?|
| Help Modal | 620脳460 / 760脳680 | 涓嶈畩 | 宸插悎鐞?|
| Main (dev launcher) | 鍥哄畾 320脳338 | 涓嶈畩锛堥潪姝ｅ紡鐢㈠搧鍏ュ彛锛?| 浣庡劒鍏?|
| Ring | 460脳460锛坄WINDOW_SIZE`锛?| **娌掓湁鏀?* | 鐗藉嫊鍏ㄩ儴绻湒鑸囧懡涓脯瑭﹀骇妯欙紝閫欐鏀圭増涓嶅嫊 |

## 11. 鍝簺鏀瑰嫊鍙互浣庨ⅷ闅厛鍋氾紙寤鸿瀵︿綔闋嗗簭锛?
1. 鉁?**寤虹珛鍏辩敤 token 妾旓紙鏂版獢妗堬紝渚嬪 `ui/style_tokens.py`锛?*鈥斺€旂磾璩囨枡/瀛椾覆甯告暩锛屼笉纰颁换浣曢倧杓€傞€欐槸寰岀簩鎵€鏈夋敼鍕曠殑鍦板熀銆?2. 鉁?**`ui/tray_icon.py`**鈥斺€斿彧鏈?6 琛岀躬鍦栫▼寮忕⒓姹哄畾鍝佺墝鑹诧紝鏀规垚 `ember`锛屽叏 App 鏇濆厜搴︽渶楂樸€侀ⅷ闅渶浣庛€?3. 鉁?**`core/theme.py` 鐨?`DEFAULT_THEME`/`THEME_ORDER` 瑾挎暣 + 鍚屾淇 `theme_painter.py` 鐨勯噸瑜囪壊绁?*鈥斺€斿叐鍊嬫獢妗堣鍦ㄥ悓涓€鍊?commit 鍏т竴璧锋敼銆?4. 鉁?**`ui/settings_window.py` 鐨?QSS 甯告暩瀛椾覆**锛坄_S_FIELD`/`_S_BTN_PRIMARY` 绛夛級鎻涙垚鏂?token 鐨勯鑹?瀛楃礆/鍒囪鈥斺€旈€欎簺鏄瓧涓叉浛鎻涳紝涓嶅嫊浠讳綍 signal/slot 閭忚集锛岄ⅷ闅綆銆佸彲瑕嬪害鏈€楂樸€?5. 鉁?**`ui/client_workspace_window.py`銆乣ui/powershell_library_window.py`銆乣ui/environment_check_window.py`銆乣ui/help_modal.py`銆乣ui/emoji_picker.py`銆乣ui/hotkey_picker.py`銆乣ui/forms/*.py` 鐨?QSS 甯告暩**鈥斺€斿悓涓婏紝姗熸寮忔浛鎻涳紝绛?(4) 椹楄瓑閬庢ā寮忓彲琛屽緦鍐峛atch铏曠悊銆傦紙`ui/forms/join_domain_form.py` 闄ゅ锛屽埢鎰忎笉鍕曪紝瑕?handoff 搂2锛?6. 鉁?**`ui/settings_window.py` 瑕栫獥闋愯ō灏哄寰**锛?100脳1100 鈫?1180脳760锛夆€斺€斾竴琛屾暩瀛椼€傦紙Client Workspace銆丠otkey Picker 瀵︽脯寰屼篃涓€浣佃鏁达紝鍘熻▓鐣矑闋愪及鍒帮級
7. 鉂?**Ring 鐨?glow/gradient 鍙冩暩寰**锛坄theme_painter.py` 鍏х殑 gradient stop銆侀€忔槑搴︽暩鍊硷級鈥斺€?*灏氭湭闁嬪**銆傞渶瑕佸湪鏀瑰畬寰屾柤澶氬€嬭灑骞?澶氬€嬩富椤屼笅瀵︽脯锛屾瘮鍓嶉潰骞鹃爡棰ㄩ毆鐣ラ珮銆?8. 鉂?**Ring 闁嬪牬鍕曠暙鐨?overshoot 骞呭害銆乻lot stagger銆佷腑蹇冭剤琛?*鈥斺€?*灏氭湭闁嬪**銆傞ⅷ闅渶楂樼殑涓€鎵癸紝蹇呴爤鏈€寰屽仛锛屼笖姣忎竴姝ラ兘瑕佸柈鐛ㄦ脯瑭︽嫋鏇炽€佸懡涓€佸铻㈠箷鎯呭锛屼笉瑕佷竴娆″叏閮ㄦ敼瀹屾墠娓€?9. 鉁?**`ui/settings_ui.py` + `ui/pages/*` legacy 鍒嗘敮**鈥斺€斿凡纰鸿獚鐒′换浣曢€插叆榛烇紝宸叉柤 Phase 0 鍒櫎锛堝惈 `ui/menu_editor.py`锛夛紝瑭宠 `docs/ui-redesign-handoff.md` 搂2銆?
---

## 寰呯⒑瑾嶄簨闋咃紙宸插叏閮ㄥ洖瑕嗕甫鍩疯瀹岀暍锛?
- ~~鏄惁瑕佸収宓?`Oswald` 瀛楀瀷妾攡~ 鈫?**鍏у祵**銆傚凡瀹屾垚鍩虹瑷柦锛坄core/fonts.py` + `assets/fonts/`锛夛紝纰鸿獚鎵撳寘/杓夊叆娌掑晱椤岋紙`smartaction.spec` 涓嶇敤鏀癸級銆?*灏氭湭濂楃敤鍒颁换浣曠暙闈?*鈥斺€旈€欐槸涓嬩竴闅庢鍙互鍋氱殑瑕栬宸ヤ綔銆?- ~~`settings_ui.py`/`pages/*` 鏄惁鍙互鍒櫎~~ 鈫?**涓诲嫊鍒櫎**銆傚凡鏂?Phase 0 瀹屾垚锛岄亷绋嬩腑鐧肩従涓︿慨姝ｄ簡鍘?audit 灏?`core/menu_model.MenuItem` 鐨勮鍒わ紙瀹冨叾瀵︽槸 production 璺緫鐨勬牳蹇冭硣鏂欏瀷鍒ワ紝涓嶈兘鍒紱鐪熸瑭插埅鐨勫彧鏈?`ConfigManager.menu_items`/`load_menu_tree()`锛夈€?- ~~闆欒硣鏂欐ā鍨嬪晱椤屾槸鍚︿竴浣佃檿鐞唦~ 鈫?**涓€浣佃檿鐞?*锛屼笖绡勫湇姣斿師鏈摂蹇冪殑灏忓緢澶氾細`ConfigManager.menu_items` 鍙槸瀹屽叏鐒′富鐨勬璺緫锛屽埅鎺?legacy pages 寰岀洿鎺ユ竻鎺夊嵆鍙紝涓嶉渶瑕佸嫊 `ActionsConfig`/`MenuItem` 閫欐鐪熸鐨?production 璩囨枡娴併€?
瑭崇窗鍩疯绱€閷勩€侀璀夋柟寮忋€佽垏鍘熻▓鐣殑钀藉樊瑾槑锛岃 `docs/ui-redesign-handoff.md`銆?
