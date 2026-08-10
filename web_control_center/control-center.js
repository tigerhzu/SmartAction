(() => {
  "use strict";

  const launchFragment = new URLSearchParams(location.hash.slice(1));
  const requestedView = launchFragment.get("view") || "";
  const token = launchFragment.get("token") || "";
  if (token) history.replaceState(null, "", location.pathname);

  const state = { token, status: null, settings: null, preferences: null, actions: [], editorParentId: null, psScripts: [], psRunScript: null, webBackgroundSource: null, webBackgroundUrl: null, workspace: { clients: [], folders: [], profiles: [], selectedClientId: null, expandedClientId: null, helperConnected: null, draggedElement: null } };
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const pretty = (value) => String(value || "-").replaceAll("_", " ");
  const themes = ["tiger", "purple", "ice", "lava", "cosmic", "halloween", "kawaii", "sakura", "cyber", "ocean"];
  const constellations = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"];
  const constellationLabels = { aries: "牡羊座", taurus: "金牛座", gemini: "雙子座", cancer: "巨蟹座", leo: "獅子座", virgo: "處女座", libra: "天秤座", scorpio: "天蠍座", sagittarius: "射手座", capricorn: "摩羯座", aquarius: "水瓶座", pisces: "雙魚座" };
  const emojiRange = (start, end) => Array.from({ length: end - start + 1 }, (_unused, index) => String.fromCodePoint(start + index));
  const emojiCatalog = [
    { name: "常用", keywords: "星星 火焰 提示 勾叉 目標 火箭 工作", icons: ["⭐", "✨", "🔥", "💡", "⚡", "✅", "❌", "❗", "📌", "🎯", "🚀", "🧠", "💼", "📁", "⚙️", "🌐", "🔗", "🎵", "📷", "👍"] },
    { name: "表情與人物", keywords: "笑臉 人物 表情 機器人 揮手 鼓掌 讚 感謝", icons: emojiRange(0x1F600, 0x1F64F) },
    { name: "自然與活動", keywords: "天氣 植物 動物 運動 遊戲 自然 活動", icons: emojiRange(0x1F300, 0x1F3FA) },
    { name: "動物與食物", keywords: "動物 食物 飲料 水果 料理", icons: emojiRange(0x1F400, 0x1F4FF) },
    { name: "物件與工具", keywords: "物件 工具 文件 電腦 設定 鎖 安全", icons: emojiRange(0x1F500, 0x1F5FF) },
    { name: "交通與地點", keywords: "交通 汽車 火車 飛機 地圖 建築", icons: emojiRange(0x1F680, 0x1F6FF) },
  ];
  const defaultActionIcons = { folder: "📁", settings: "⚙️", url: "🔗", app: "🖥️", command: "⌨️", powershell: "💻", powershell_library: "📚", environment_check: "🛠️", client_workspace: "💼", paste: "📋", form: "📝", ps_form: "⚡" };
  let emojiPickerCategory = "常用";
  const actionTypes = [
    ["folder", "Folder", true], ["settings", "Settings", false], ["url", "URL", true], ["app", "App / File", true],
    ["command", "Command", true], ["powershell", "PowerShell", true], ["powershell_library", "PowerShell Library", false],
    ["environment_check", "Environment Check", false], ["client_workspace", "Client Workspace", false], ["paste", "Paste", true],
    ["form", "Form", true], ["ps_form", "PS Form", true],
  ];
  const psCategories = ["System", "Network", "User Management", "Domain / AD", "Repair Tools", "Custom"];

  let noticeTimer = null;
  function showNotice(message, error = false) { const notice = $("#notice"); clearTimeout(noticeTimer); notice.textContent = message; notice.classList.remove("hidden"); notice.classList.toggle("error", error); if (!error) noticeTimer = setTimeout(clearNotice, 3600); }
  function clearNotice() { $("#notice").classList.add("hidden"); }
  async function api(path, options = {}) {
    if (!state.token) throw new Error("This Control Center link is missing its local access token. Open it from SmartAction.");
    const response = await fetch(path, { ...options, headers: { "X-SmartAction-Token": state.token, ...(options.headers || {}) }, cache: "no-store" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok && !options.allowHttpFailure) throw new Error(payload?.error?.message || "SmartAction Core did not accept this request.");
    return payload;
  }
  function jsonOptions(method, body) { return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }; }
  async function psRequest(operation, payload = {}, allowFailure = false) { return api("/api/v1/powershell/execute", { ...jsonOptions("POST", { operation, payload }), allowHttpFailure: allowFailure }); }
  function fillSelect(selector, options, value) { const select = $(selector); select.replaceChildren(...options.map(([id, label]) => { const option = document.createElement("option"); option.value = id; option.textContent = label; return option; })); select.value = value || select.options[0]?.value; }
  function fillSimpleSelect(selector, options, value) { fillSelect(selector, options.map((item) => [item, pretty(item)]), value); }

  function applySettings(settings) {
    state.settings = settings;
    $("#setting-hotkey").value = settings.hotkey || "";
    fillSimpleSelect("#setting-theme", themes, settings.theme);
    fillSelect("#setting-constellation", constellations.map((item) => [item, constellationLabels[item]]), settings.constellation);
    $("#setting-color").value = settings.constellation_color || "#F2760B";
    $("#setting-ui-theme").value = settings.ui_theme || "classic";
    $("#setting-opacity").value = settings.ui_background_opacity ?? 82;
    $("#setting-zoom").value = settings.ui_background_zoom ?? 100;
    $("#setting-focus-x").value = Math.round((settings.ui_background_focus_x ?? .5) * 100);
    $("#setting-focus-y").value = Math.round((settings.ui_background_focus_y ?? .5) * 100);
    updateRangeLabels(); $("#background-name").textContent = settings.ui_background || "內建背景"; void applyControlCenterBackground(settings);
    $("#metric-theme").textContent = pretty(settings.theme);
  }
  function applyPreferences(preferences) { state.preferences = preferences; $("#setting-autostart").checked = !!preferences.autostart; $("#setting-reduced-motion").checked = !!preferences.reduced_motion; }
  function applyStatus(payload) { state.status = payload; const core = payload.core; $("#connection-dot").className = "dot online"; $("#connection-label").textContent = "核心已連線"; $("#core-status").textContent = "核心在線"; $("#core-status").classList.add("online"); $("#metric-version").textContent = `v${core.version}`; $("#metric-actions").textContent = core.actionCount; $("#metric-hotkey").textContent = core.hotkey || "未設定"; }
  function updateRangeLabels() { $("#opacity-output").value = `${$("#setting-opacity").value}%`; $("#zoom-output").value = `${$("#setting-zoom").value}%`; $("#focus-x-output").value = `${$("#setting-focus-x").value}%`; $("#focus-y-output").value = `${$("#setting-focus-y").value}%`; }
  function updateControlCenterBackgroundStyle(settings) {
    const root = document.documentElement; root.style.setProperty("--control-background-opacity", String((settings.ui_background_opacity ?? 82) / 100)); root.style.setProperty("--control-background-size", `${settings.ui_background_zoom ?? 100}% auto`); root.style.setProperty("--control-background-position", `${Math.round((settings.ui_background_focus_x ?? .5) * 100)}% ${Math.round((settings.ui_background_focus_y ?? .5) * 100)}%`);
  }
  async function applyControlCenterBackground(settings) {
    updateControlCenterBackgroundStyle(settings); const source = settings.ui_background || "";
    if (source === state.webBackgroundSource) return;
    state.webBackgroundSource = source;
    if (state.webBackgroundUrl) { URL.revokeObjectURL(state.webBackgroundUrl); state.webBackgroundUrl = null; }
    document.body.classList.remove("has-custom-background"); document.documentElement.style.removeProperty("--control-background-image");
    if (!source) return;
    try {
      const response = await fetch("/api/v1/settings/background", { headers: { "X-SmartAction-Token": state.token }, cache: "no-store" });
      if (!response.ok) throw new Error("背景圖片無法載入。");
      const objectUrl = URL.createObjectURL(await response.blob());
      if (state.webBackgroundSource !== source) { URL.revokeObjectURL(objectUrl); return; }
      state.webBackgroundUrl = objectUrl; document.documentElement.style.setProperty("--control-background-image", `url("${objectUrl}")`); document.body.classList.add("has-custom-background");
    } catch (error) { if (state.webBackgroundSource === source) showNotice(error.message, true); }
  }
  function previewControlCenterBackground() { if (!state.settings) return; applyControlCenterBackground({ ...state.settings, ui_background_opacity: Number($("#setting-opacity").value), ui_background_zoom: Number($("#setting-zoom").value), ui_background_focus_x: Number($("#setting-focus-x").value) / 100, ui_background_focus_y: Number($("#setting-focus-y").value) / 100 }); }

  function flattenedActions(actions, parentId = null, depth = 0, rows = []) {
    actions.forEach((action, index) => { rows.push({ action, parentId, depth, index, siblings: actions }); flattenedActions(action.sub_actions || [], action.id, depth + 1, rows); }); return rows;
  }
  function actionById(id) { return flattenedActions(state.actions).find((row) => row.action.id === id)?.action || null; }
  function setActionIcon(icon) { $("#action-icon").value = icon || ""; $("#emoji-preview").textContent = icon || "✦"; }
  function renderEmojiCatalog() {
    const catalog = $("#emoji-catalog"); const tabs = $("#emoji-category-tabs"); catalog.replaceChildren(); tabs.replaceChildren();
    emojiCatalog.forEach((group) => { const tab = rowButton(group.name, () => { emojiPickerCategory = group.name; renderEmojiCatalog(); }); tab.classList.toggle("active", group.name === emojiPickerCategory); tabs.append(tab); });
    emojiCatalog.filter((group) => group.name === emojiPickerCategory).forEach((group) => { const section = document.createElement("section"); section.className = "emoji-group"; const grid = document.createElement("div"); grid.className = "emoji-grid"; group.icons.forEach((icon) => { const button = document.createElement("button"); button.type = "button"; button.className = "emoji-choice"; button.textContent = icon; button.title = `使用 ${icon}`; button.setAttribute("aria-label", `使用 ${icon}`); button.addEventListener("click", () => chooseEmoji(icon)); grid.append(button); }); section.append(grid); catalog.append(section); });
  }
  function openEmojiPicker(action = null) { state.emojiPickerAction = action; emojiPickerCategory = "常用"; renderEmojiCatalog(); $("#emoji-picker-dialog").showModal(); }
  async function chooseEmoji(icon) { const action = state.emojiPickerAction; $("#emoji-picker-dialog").close(); if (!action) { setActionIcon(icon); $("#action-icon").focus(); return; } try { const response = await api(`/api/v1/actions/${encodeURIComponent(action.id)}`, jsonOptions("PATCH", { changes: { icon } })); renderActions(response.actions); showNotice(`已更新「${action.label}」的圖示。`); } catch (error) { showNotice(error.message, true); } }
  function renderActions(actions = state.actions) {
    state.actions = actions; const list = $("#action-list"); const rows = flattenedActions(actions); $("#action-count").textContent = `${rows.length} actions from SmartAction Core`;
    if (!rows.length) { list.textContent = "No actions are configured."; return; }
    list.replaceChildren(renderActionBranch(actions, null, 0));
  }
  function renderActionBranch(actions, parentId, depth) {
    const branch = document.createElement("div"); branch.className = depth ? "action-children" : "action-tree"; branch.dataset.parentId = parentId || "";
    actions.forEach((action, index) => {
      const item = document.createElement("div"); item.className = `action-row action-tree-row${action.type === "folder" ? " action-folder" : ""}`; item.draggable = true;
      const handle = document.createElement("span"); handle.className = "drag-handle"; handle.title = "Drag to reorder within this level"; handle.setAttribute("aria-hidden", "true"); handle.textContent = "⠿";
      const icon = document.createElement("button"); icon.type = "button"; icon.className = "action-emoji-control"; icon.textContent = action.icon || defaultActionIcons[action.type] || "✦"; icon.title = "變更 Emoji 圖示"; icon.setAttribute("aria-label", `變更「${action.label || "未命名動作"}」的 Emoji 圖示`); icon.addEventListener("click", () => openEmojiPicker(action));
      const info = document.createElement("div"); info.className = "action-info"; const hierarchy = document.createElement("span"); hierarchy.className = "action-hierarchy"; hierarchy.textContent = depth ? `子動作 · 第 ${depth} 層` : "Ring 頂層";
      const title = document.createElement("strong"); title.textContent = actionLabel(action); const detail = document.createElement("span"); detail.textContent = action.target || (action.type === "folder" ? `${(action.sub_actions || []).length} 個子動作` : "無目標"); info.append(hierarchy, title, detail);
      const controls = document.createElement("div"); controls.className = "row-controls"; const type = document.createElement("span"); type.className = "tag"; type.textContent = action.type || "folder"; controls.append(type, rowButton("編輯", () => openEditor(action.id)));
      if (action.type === "folder") controls.append(rowButton("+ 新增子動作", () => openEditor(null, action.id)));
      item.append(handle, icon, info, controls); wireActionDrag(item, action, actions, parentId, index); branch.append(item);
      if (action.sub_actions?.length) branch.append(renderActionBranch(action.sub_actions, action.id, depth + 1));
    });
    return branch;
  }
  function rowButton(text, click, disabled = false) { const button = document.createElement("button"); button.type = "button"; button.className = "button mini ghost"; button.textContent = text; button.disabled = disabled; button.addEventListener("click", click); return button; }
  function actionLabel(action) { return `${action.enabled === false ? "Disabled · " : ""}${action.label || "Untitled action"}`; }
  function wireActionDrag(item, action, siblings, parentId, index) {
    item.addEventListener("dragstart", (event) => { state.draggedAction = { id: action.id, parentId, index }; item.classList.add("dragging"); event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/plain", action.id); });
    item.addEventListener("dragend", () => { state.draggedAction = null; $$(".action-tree-row").forEach((row) => row.classList.remove("dragging", "drop-before", "drop-after")); });
    item.addEventListener("dragover", (event) => { const dragged = state.draggedAction; if (!dragged || dragged.parentId !== parentId || dragged.id === action.id) return; event.preventDefault(); item.classList.toggle("drop-before", event.clientY < item.getBoundingClientRect().top + item.offsetHeight / 2); item.classList.toggle("drop-after", !item.classList.contains("drop-before")); });
    item.addEventListener("dragleave", () => item.classList.remove("drop-before", "drop-after"));
    item.addEventListener("drop", async (event) => { const dragged = state.draggedAction; if (!dragged || dragged.parentId !== parentId || dragged.id === action.id) return; event.preventDefault(); const before = event.clientY < item.getBoundingClientRect().top + item.offsetHeight / 2; const ids = siblings.map((entry) => entry.id); const source = ids.indexOf(dragged.id); let destination = ids.indexOf(action.id); ids.splice(source, 1); if (source < destination) destination -= 1; ids.splice(destination + (before ? 0 : 1), 0, dragged.id); try { const response = await api("/api/v1/actions/reorder", jsonOptions("POST", { orderedIds: ids, parentId })); renderActions(response.actions); showNotice("Action order applied to SmartAction Core."); } catch (error) { showNotice(error.message, true); } });
  }

  function openEditor(actionId = null, parentId = null) {
    const action = actionId ? actionById(actionId) : null; state.editorParentId = parentId;
    $("#action-editor").classList.remove("hidden"); $("#editor-title").textContent = action ? `Edit: ${action.label}` : parentId ? "New child action" : "New root action";
    $("#action-id").value = action?.id || ""; $("#action-label").value = action?.label || ""; $("#action-short-label").value = action?.short_label || ""; setActionIcon(action?.icon || ""); const typeOptions = action && !actionTypes.some(([id]) => id === action.type) ? [...actionTypes, [action.type, `Custom: ${action.type}`, true]] : actionTypes; fillSelect("#action-type", typeOptions.map(([id, label]) => [id, label]), action?.type || "url"); $("#action-target").value = action?.target || ""; $("#action-enabled").checked = action?.enabled !== false;
    const parent = parentId ? actionById(parentId) : null; $("#editor-parent").textContent = action ? `ID: ${action.id}` : parent ? `Adding below folder: ${parent.label}` : "Adding at the Ring root level."; $("#delete-action").classList.toggle("hidden", !action); toggleTarget(); $("#action-label").focus();
  }
  function closeEditor() { $("#action-editor").classList.add("hidden"); state.editorParentId = null; }
  function toggleTarget() { const needsTarget = actionTypes.find(([id]) => id === $("#action-type").value)?.[2] !== false; $("#target-field").classList.toggle("dimmed", !needsTarget); $("#action-target").disabled = !needsTarget; if (!needsTarget) $("#action-target").value = ""; }
  async function saveAction(event) {
    event.preventDefault(); const id = $("#action-id").value; const action = { label: $("#action-label").value.trim(), short_label: $("#action-short-label").value.trim(), icon: $("#action-icon").value.trim(), type: $("#action-type").value, target: $("#action-target").value, enabled: $("#action-enabled").checked };
    try { const response = id ? await api(`/api/v1/actions/${encodeURIComponent(id)}`, jsonOptions("PATCH", { changes: action })) : await api("/api/v1/actions", jsonOptions("POST", { action, parentId: state.editorParentId })); renderActions(response.actions); closeEditor(); showNotice("Action saved to SmartAction Core."); } catch (error) { showNotice(error.message, true); }
  }
  async function deleteAction() { const id = $("#action-id").value; if (!id || !confirm("Delete this action and all of its child actions?")) return; try { const response = await api(`/api/v1/actions/${encodeURIComponent(id)}`, { method: "DELETE" }); renderActions(response.actions); closeEditor(); showNotice("Action deleted."); } catch (error) { showNotice(error.message, true); } }

  function initialiseModuleCoverflow() {
    const frame = $("#module-coverflow"); const cards = $$(".coverflow-card"); const pagination = $("#coverflow-pagination");
    if (!frame || !cards.length) return;
    let position = 0; let target = 0; let cardWidth = 0; let animation = null; let selected = 0; let drag = null; let suppressClick = false;
    const count = cards.length; const indexAt = (value) => ((Math.round(value) % count) + count) % count;
    const updateSelection = (index) => {
      selected = index; const active = cards[index]; $("#coverflow-title").textContent = active.dataset.title || ""; $("#coverflow-subtitle").textContent = active.dataset.subtitle || "";
      cards.forEach((card, cardIndex) => card.setAttribute("aria-current", String(cardIndex === index)));
      [...pagination.children].forEach((dot, dotIndex) => dot.setAttribute("aria-current", String(dotIndex === index)));
    };
    const paint = () => {
      if (!cardWidth) return; const pitch = cardWidth * 1.06;
      cards.forEach((card, index) => {
        let offset = ((index - position) % count + count) % count; if (offset > count / 2) offset -= count;
        const distance = Math.abs(offset); const ramp = Math.pow(distance, .58); const tilt = Math.min(43 * ramp, 80) * Math.sign(offset); const edge = Math.min(1, Math.max(0, count / 2 - distance));
        card.style.transform = `translateX(calc(-50% + ${offset * pitch}px)) translateZ(${-cardWidth * .56 * ramp}px) rotateY(${-tilt}deg)`; card.style.opacity = String(Math.max(0, 1 - .12 * distance) * edge); card.style.zIndex = String(100 - Math.round(distance));
      });
      const nextSelected = indexAt(position); if (nextSelected !== selected) updateSelection(nextSelected);
    };
    const clampTarget = (value) => value;
    const settle = (nextTarget) => {
      if (animation !== null) cancelAnimationFrame(animation); target = clampTarget(nextTarget); updateSelection(indexAt(target));
      if (state.preferences?.reduced_motion || matchMedia("(prefers-reduced-motion: reduce)").matches) { position = target; paint(); animation = null; return; }
      const step = () => { const remaining = target - position; if (Math.abs(remaining) < .0004) { position = target; paint(); animation = null; return; } position += remaining * .16; paint(); animation = requestAnimationFrame(step); }; animation = requestAnimationFrame(step);
    };
    const goTo = (index) => settle(index + Math.round((target - index) / count) * count);
    pagination.replaceChildren(...cards.map((card, index) => { const dot = document.createElement("button"); dot.type = "button"; dot.setAttribute("aria-label", `Go to ${card.dataset.title}`); dot.addEventListener("click", () => goTo(index)); return dot; }));
    cards.forEach((card) => card.addEventListener("click", (event) => { if (suppressClick) { event.preventDefault(); return; } showView(card.dataset.go, card.dataset.module); }));
    $("#coverflow-previous").addEventListener("click", () => settle(Math.round(target) - 1)); $("#coverflow-next").addEventListener("click", () => settle(Math.round(target) + 1));
    frame.addEventListener("keydown", (event) => { if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); settle(Math.round(target) + (event.key === "ArrowLeft" ? -1 : 1)); } else if (event.key === "Enter" || event.key === " ") { event.preventDefault(); cards[selected].click(); } });
    frame.addEventListener("pointerdown", (event) => { if (animation !== null) cancelAnimationFrame(animation); animation = null; frame.setPointerCapture(event.pointerId); target = position; drag = { id: event.pointerId, x: event.clientX, position, previous: position, time: performance.now(), velocity: 0, moved: false }; });
    frame.addEventListener("pointermove", (event) => { if (!drag || drag.id !== event.pointerId || !cardWidth) return; const now = performance.now(); const next = drag.position - (event.clientX - drag.x) / (cardWidth * 1.06); drag.moved ||= Math.abs(event.clientX - drag.x) > 5; drag.velocity = ((next - drag.previous) / Math.max(now - drag.time, 1)) * 1000; drag.previous = next; drag.time = now; position = next; paint(); });
    const endDrag = (event) => { if (!drag || drag.id !== event.pointerId) return; suppressClick = drag.moved; const carried = Math.max(-2, Math.min(2, drag.velocity * .18)); drag = null; settle(Math.round(position + carried)); setTimeout(() => { suppressClick = false; }, 0); };
    frame.addEventListener("pointerup", endDrag); frame.addEventListener("pointercancel", endDrag);
    const measure = () => { cardWidth = cards[0].offsetWidth; paint(); }; updateSelection(0); requestAnimationFrame(measure); if ("ResizeObserver" in window) new ResizeObserver(measure).observe(frame); else window.addEventListener("resize", measure);
  }

  function initialisePowerShellControls() { fillSelect("#ps-category-filter", [["", "All categories"], ...psCategories.map((category) => [category, category])], ""); fillSelect("#ps-category", psCategories.map((category) => [category, category]), "Custom"); }
  async function refreshPowerShell() {
    try { const category = $("#ps-category-filter").value; const response = await psRequest("list", category ? { category } : {}); state.psScripts = response.value || []; renderPowerShellScripts(); }
    catch (error) { showNotice(error.message, true); }
  }
  function renderPowerShellScripts() {
    const list = $("#ps-script-list"); $("#ps-script-count").textContent = `${state.psScripts.length} saved scripts`;
    if (!state.psScripts.length) { list.textContent = "No scripts in this category."; return; }
    list.replaceChildren(...state.psScripts.map((script) => {
      const row = document.createElement("div"); row.className = "action-row";
      const info = document.createElement("div"); const title = document.createElement("strong"); title.textContent = script.name; const detail = document.createElement("span"); detail.textContent = `${script.category} · ${script.description || "無說明"}`; info.append(title, detail);
        const controls = document.createElement("div"); controls.className = "row-controls"; const risk = document.createElement("span"); risk.className = "tag"; risk.textContent = script.risk_level || "safe"; controls.append(risk, rowButton("SOP", () => openPowerShellSop(script)), rowButton("編輯", () => openPowerShellEditor(script)), rowButton("執行", () => openPowerShellRun(script))); row.append(info, controls); return row;
    }));
  }
  function openPowerShellEditor(script = null) {
    $("#ps-editor").classList.remove("hidden"); $("#ps-editor-title").textContent = script ? `Edit: ${script.name}` : "New script"; $("#ps-script-id").value = script?.id || ""; $("#ps-name").value = script?.name || ""; $("#ps-description").value = script?.description || ""; fillSelect("#ps-category", psCategories.map((category) => [category, category]), script?.category || "Custom"); $("#ps-need-admin").checked = !!script?.need_admin; $("#ps-risk").value = script?.risk_level || "safe"; $("#ps-content").value = script?.script_content || ""; $("#ps-parameters").value = JSON.stringify(script?.parameters || [], null, 2); $("#ps-delete-script").classList.toggle("hidden", !script); $("#ps-name").focus();
  }
  function closePowerShellEditor() { $("#ps-editor").classList.add("hidden"); }
  function openPowerShellSop(script) {
    state.psSopScript = script; $("#ps-sop").classList.remove("hidden"); $("#ps-sop-title").textContent = `${script.name}：手動執行 SOP`;
    const parameterSteps = (script.parameters || []).map((parameter) => `將命令中的 {{${parameter.name || "參數名稱"}}} 替換為${parameter.required ? "必要" : "選填"}的實際值。`);
    const steps = ["開啟 Windows PowerShell。", script.need_admin ? "此腳本需要系統管理員權限，請以系統管理員身分開啟 PowerShell。" : "確認目前 PowerShell 帳號具有執行此作業所需權限。", ...parameterSteps, "依序貼上並執行下方指令。", "檢查輸出與錯誤訊息，確認作業結果。"];
    const list = $("#ps-sop-steps"); list.replaceChildren(...steps.map((step) => { const item = document.createElement("li"); item.textContent = step; return item; })); $("#ps-sop-command").textContent = script.script_content || "此腳本沒有可供手動執行的指令。"; $("#ps-sop").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  async function copyPowerShellSop() {
    const command = state.psSopScript?.script_content; if (!command) return;
    try { await navigator.clipboard.writeText(command); showNotice("PowerShell 指令已複製，可依 SOP 手動執行。"); }
    catch (_) { const input = document.createElement("textarea"); input.value = command; document.body.append(input); input.select(); document.execCommand("copy"); input.remove(); showNotice("PowerShell 指令已複製，可依 SOP 手動執行。"); }
  }
  async function savePowerShellScript(event) {
    event.preventDefault(); let parameters;
    try { parameters = JSON.parse($("#ps-parameters").value.trim() || "[]"); if (!Array.isArray(parameters)) throw new Error("Parameters must be a JSON array."); }
    catch (error) { showNotice(`Parameters JSON is invalid: ${error.message}`, true); return; }
    const script = { name: $("#ps-name").value.trim(), description: $("#ps-description").value.trim(), category: $("#ps-category").value, need_admin: $("#ps-need-admin").checked, risk_level: $("#ps-risk").value, script_content: $("#ps-content").value.trim(), parameters };
    const id = $("#ps-script-id").value;
    try { await psRequest(id ? "update" : "create", id ? { script_id: id, script } : { script }); closePowerShellEditor(); await refreshPowerShell(); showNotice("PowerShell script saved to SmartAction Core."); } catch (error) { showNotice(error.message, true); }
  }
  async function deletePowerShellScript() { const id = $("#ps-script-id").value; const name = $("#ps-name").value || "this script"; if (!id || !confirm(`Delete "${name}"?`)) return; try { await psRequest("delete", { script_id: id }); closePowerShellEditor(); await refreshPowerShell(); showNotice("PowerShell script deleted."); } catch (error) { showNotice(error.message, true); } }
  function openPowerShellRun(script) {
    state.psRunScript = script; $("#ps-run-title").textContent = `Run: ${script.name}`; const warning = script.risk_level === "dangerous" ? "Dangerous script: confirm that you understand its effects before Core executes it." : script.need_admin ? "This script may require SmartAction to be running as administrator." : "Core will execute this script with the current SmartAction process permissions."; $("#ps-run-warning").textContent = warning;
    const fields = $("#ps-parameter-fields"); fields.replaceChildren(...(script.parameters || []).map((parameter) => { const label = document.createElement("label"); label.textContent = parameter.name || "Parameter"; const input = document.createElement("input"); input.name = parameter.name || ""; input.type = parameter.type === "password" ? "password" : "text"; input.required = parameter.required === true; input.autocomplete = "off"; input.placeholder = parameter.required ? "Required" : "Optional"; label.append(input); return label; })); $("#ps-run-dialog").showModal();
  }
  async function runPowerShellScript(event) {
    event.preventDefault(); const script = state.psRunScript; if (!script) return; const values = Object.fromEntries([...$("#ps-parameter-fields").querySelectorAll("input")].map((input) => [input.name, input.value]));
    try { const result = await psRequest("run", { script_id: script.id, values, confirmed: script.risk_level === "dangerous", enforce_admin: false }, true); $("#ps-run-dialog").close(); state.psRunScript = null; showPowerShellResult(script.name, result.value || result.error || {}, !result.success); }
    catch (error) { showPowerShellResult(script.name, { friendly_error: error.message }, true); $("#ps-run-dialog").close(); state.psRunScript = null; }
  }
  function showPowerShellResult(name, value, failed) { $("#ps-run-result").classList.remove("hidden"); $("#ps-result-title").textContent = `${failed ? "Failed" : "Completed"}: ${name}`; const output = [value.stdout, value.stderr && `stderr:\n${value.stderr}`, value.friendly_error].filter(Boolean).join("\n\n") || (failed ? "The Core execution request failed." : "Script completed without output."); $("#ps-result-output").textContent = output; }

  async function workspaceRequest(operation, payload = {}, allowFailure = false) { return api("/api/v1/client-workspace/execute", { ...jsonOptions("POST", { operation, payload }), allowHttpFailure: allowFailure }); }
  function selectedWorkspaceClient() { return state.workspace.clients.find((client) => client.id === state.workspace.selectedClientId) || null; }
  async function refreshWorkspace() {
    try {
      const [clients, folders, profiles] = await Promise.all([workspaceRequest("list_clients"), workspaceRequest("list_folders"), workspaceRequest("list_profiles", {}, true)]);
      state.workspace.clients = clients.value || []; state.workspace.folders = folders.value || []; state.workspace.profiles = profiles.success ? (profiles.value || []) : [];
      if (!selectedWorkspaceClient()) state.workspace.selectedClientId = null;
      renderWorkspace(); if (state.workspace.selectedClientId) refreshWorkspaceSetup();
    } catch (error) { showNotice(error.message, true); }
  }
  function renderWorkspace() {
    const list = $("#workspace-list"); const workspace = state.workspace; $("#workspace-count").textContent = `${workspace.clients.length} clients in ${workspace.folders.length} folders`;
    const groups = [{ id: "", name: "Unassigned" }, ...workspace.folders]; list.replaceChildren(...groups.map((folder) => renderWorkspaceFolder(folder)));
    renderWorkspaceSetup();
  }
  function renderWorkspaceFolder(folder) {
    const section = document.createElement("section"); section.className = "workspace-folder"; section.dataset.folderId = folder.id;
    const header = document.createElement("div"); header.className = "workspace-folder-heading"; const title = document.createElement("strong"); title.textContent = folder.name; const count = document.createElement("span"); const clients = state.workspace.clients.filter((client) => (client.folderId || "") === folder.id); count.textContent = `${clients.length} client${clients.length === 1 ? "" : "s"}`; header.append(title, count);
    if (folder.id) { const controls = document.createElement("div"); controls.className = "row-controls"; controls.append(rowButton("Rename", () => renameWorkspaceFolder(folder)), rowButton("Delete", () => deleteWorkspaceFolder(folder))); header.append(controls); }
    const clientList = document.createElement("div"); clientList.className = "workspace-client-list"; clientList.dataset.folderId = folder.id; clientList.addEventListener("dragover", (event) => { if (!state.workspace.draggedElement) return; event.preventDefault(); clientList.classList.add("drop-target"); }); clientList.addEventListener("dragleave", () => clientList.classList.remove("drop-target")); clientList.addEventListener("drop", (event) => dropWorkspaceClient(event, clientList));
    clients.forEach((client) => clientList.append(renderWorkspaceClient(client))); section.append(header, clientList); return section;
  }
  function renderWorkspaceClient(client) {
    const card = document.createElement("article"); card.className = "workspace-client-card"; card.draggable = true; card.dataset.clientId = client.id;
    const info = document.createElement("div"); const title = document.createElement("strong"); title.textContent = client.name; const detail = document.createElement("span"); detail.textContent = [client.containerName ? `Container: ${client.containerName}` : "Standard Firefox", `${(client.urls || []).length} URLs`].join(" · "); info.append(title, detail);
    const controls = document.createElement("div"); controls.className = "row-controls"; controls.append(rowButton("Edit", () => openWorkspaceEditor(client.id)), rowButton("Launch", () => launchWorkspace(client.id)));
    card.addEventListener("click", (event) => { if (!event.target.closest("button")) { state.workspace.selectedClientId = client.id; renderWorkspace(); refreshWorkspaceSetup(); } });
    card.addEventListener("dragstart", (event) => { state.workspace.draggedElement = card; card.classList.add("dragging"); event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/plain", client.id); }); card.addEventListener("dragend", () => { state.workspace.draggedElement = null; $$(".workspace-client-card, .workspace-client-list").forEach((item) => item.classList.remove("dragging", "drop-target")); });
    card.append(info, controls); if (client.id === state.workspace.selectedClientId) card.classList.add("selected"); return card;
  }
  async function dropWorkspaceClient(event, clientList) {
    const dragged = state.workspace.draggedElement; if (!dragged) return; event.preventDefault(); clientList.classList.remove("drop-target"); const target = event.target.closest(".workspace-client-card"); if (target && target !== dragged) { const before = event.clientY < target.getBoundingClientRect().top + target.offsetHeight / 2; target[before ? "before" : "after"](dragged); } else clientList.append(dragged);
    const layout = $$(".workspace-client-list").flatMap((list) => [...list.querySelectorAll(".workspace-client-card")].map((card) => [card.dataset.clientId, list.dataset.folderId || ""]));
    try { await workspaceRequest("set_layout", { layout }); await refreshWorkspace(); showNotice("Client workspace layout applied to SmartAction Core."); } catch (error) { await refreshWorkspace(); showNotice(error.message, true); }
  }
  async function createWorkspaceFolder() { const name = prompt("Folder name:"); if (name === null) return; try { await workspaceRequest("create_folder", { name }); await refreshWorkspace(); showNotice("Folder created."); } catch (error) { showNotice(error.message, true); } }
  async function renameWorkspaceFolder(folder) { const name = prompt("Folder name:", folder.name); if (name === null) return; try { await workspaceRequest("rename_folder", { folder_id: folder.id, name }); await refreshWorkspace(); showNotice("Folder renamed."); } catch (error) { showNotice(error.message, true); } }
  async function deleteWorkspaceFolder(folder) { if (!confirm(`Delete "${folder.name}"? Its clients will move to Unassigned.`)) return; try { await workspaceRequest("delete_folder", { folder_id: folder.id }); await refreshWorkspace(); showNotice("Folder deleted; clients moved to Unassigned."); } catch (error) { showNotice(error.message, true); } }
  function exportWorkspace() { const snapshot = { version: "1.1", folders: state.workspace.folders, clients: state.workspace.clients }; const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: "application/json" }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "client-workspaces.json"; link.click(); URL.revokeObjectURL(url); showNotice("Client workspaces exported."); }
  async function importWorkspace(file) { if (!file) return; let data; try { data = JSON.parse(await file.text()); } catch (_) { showNotice("The selected workspace file is not valid JSON.", true); return; } if (!confirm("Import replaces the current Client Workspace list. Continue?")) return; try { const result = await workspaceRequest("import_data", { data }); state.workspace.selectedClientId = null; await refreshWorkspace(); $("#import-workspace-file").value = ""; showNotice(`Client workspaces imported. Backup: ${result.value?.backup_path || "created"}`); } catch (error) { showNotice(error.message, true); } }
  function addWorkspaceUrl(data = { name: "", url: "" }) { const row = document.createElement("div"); row.className = "workspace-url-row"; const name = document.createElement("input"); name.placeholder = "Label"; name.value = data.name || ""; name.dataset.urlName = "true"; const url = document.createElement("input"); url.placeholder = "https://example.com"; url.value = data.url || ""; url.dataset.urlValue = "true"; row.append(name, url, rowButton("Remove", () => row.remove())); $("#workspace-url-list").append(row); }
  function openWorkspaceEditor(clientId = null) {
    const client = clientId ? state.workspace.clients.find((item) => item.id === clientId) : null; $("#workspace-editor").classList.remove("hidden"); $("#workspace-editor-title").textContent = client ? `Edit: ${client.name}` : "New client"; $("#workspace-client-id").value = client?.id || ""; $("#workspace-client-name").value = client?.name || "";
    fillSelect("#workspace-client-folder", [["", "Unassigned"], ...state.workspace.folders.map((folder) => [folder.id, folder.name])], client?.folderId || ""); fillSelect("#workspace-client-profile", [["", "Automatic Firefox profile"], ...state.workspace.profiles.map((profile) => [profile.name, profile.name])], client?.firefoxProfile || ""); $("#workspace-client-container").value = client?.containerName || ""; $("#workspace-url-list").replaceChildren(); (client?.urls || []).forEach(addWorkspaceUrl); if (!(client?.urls || []).length) addWorkspaceUrl(); $("#delete-workspace-client").classList.toggle("hidden", !client); $("#workspace-client-name").focus();
  }
  async function createWorkspaceFirefoxProfile() { try { const result = await workspaceRequest("create_profile"); const profiles = await workspaceRequest("list_profiles", {}, true); state.workspace.profiles = profiles.success ? (profiles.value || []) : []; fillSelect("#workspace-client-profile", [["", "Automatic Firefox profile"], ...state.workspace.profiles.map((profile) => [profile.name, profile.name])], result.value?.name || ""); showNotice(`Firefox profile ready: ${result.value?.name || "SmartAction-ClientWorkspace"}.`); } catch (error) { showNotice(error.message, true); } }
  function closeWorkspaceEditor() { $("#workspace-editor").classList.add("hidden"); }
  async function saveWorkspaceClient(event) { event.preventDefault(); const id = $("#workspace-client-id").value; const existing = state.workspace.clients.find((client) => client.id === id) || {}; const urls = [...$("#workspace-url-list").querySelectorAll(".workspace-url-row")].map((row) => ({ name: row.querySelector("[data-url-name]").value.trim(), url: row.querySelector("[data-url-value]").value.trim() })).filter((url) => url.name || url.url); const client = { ...existing, name: $("#workspace-client-name").value.trim(), folderId: $("#workspace-client-folder").value, firefoxProfile: $("#workspace-client-profile").value, containerName: $("#workspace-client-container").value.trim(), urls };
    try { const result = await workspaceRequest(id ? "update_client" : "create_client", id ? { client_id: id, client } : { client }); state.workspace.selectedClientId = result.value?.id || id; closeWorkspaceEditor(); await refreshWorkspace(); showNotice("Client saved to SmartAction Core."); } catch (error) { showNotice(error.message, true); } }
  async function deleteWorkspaceClient() { const client = state.workspace.clients.find((item) => item.id === $("#workspace-client-id").value) || selectedWorkspaceClient(); if (!client || !confirm(`Delete "${client.name}"?`)) return; try { await workspaceRequest("delete_client", { client_id: client.id }); state.workspace.selectedClientId = null; closeWorkspaceEditor(); await refreshWorkspace(); showNotice("Client deleted."); } catch (error) { showNotice(error.message, true); } }
  async function launchWorkspace(clientId = state.workspace.selectedClientId) { if (!clientId) return; try { const result = await workspaceRequest("launch", { client_id: clientId }); const value = result.value || {}; showNotice(`Firefox launch requested: ${value.opened_count || 0} URL(s) opened${value.used_container_helper ? ` in ${value.container_name}` : ""}.`); } catch (error) { showNotice(error.message, true); } }
  function renderWorkspaceSetup(status = null) { const client = selectedWorkspaceClient(); const enabled = !!client; $("#workspace-setup-title").textContent = client ? client.name : "Select a client"; ["#launch-workspace", "#check-workspace-helper", "#install-workspace-helper", "#open-workspace-addons"].forEach((id) => $(id).disabled = !enabled); const pill = $("#workspace-helper-status"); const cells = $("#workspace-setup-grid"); cells.replaceChildren(); if (!client) { $("#workspace-setup-summary").textContent = "Select a client to inspect its Firefox profile and helper connection."; pill.textContent = "Not checked"; pill.classList.remove("online"); return; } const data = status || {}; $("#workspace-setup-summary").textContent = data.profile_error || (data.firefox_installed === false ? "Firefox was not found by SmartAction Core." : "Use the Core buttons below to validate or repair the existing Firefox Helper integration."); pill.textContent = data.helper_connected === true ? "Helper connected" : data.helper_connected === false ? "Helper unavailable" : "Not checked"; pill.classList.toggle("online", data.helper_connected === true); [["Firefox", data.firefox_installed === false ? "Not found" : "Available"], ["Profile", data.profile_name || "Automatic"], ["Container helper", data.container_helper_installed ? "Installed" : "Not installed"], ["Native host", data.native_host_registered ? "Registered" : "Not registered"]].forEach(([label, value]) => { const cell = document.createElement("div"); const heading = document.createElement("span"); heading.textContent = label; const text = document.createElement("strong"); text.textContent = value; cell.append(heading, text); cells.append(cell); }); }
  async function refreshWorkspaceSetup() { const client = selectedWorkspaceClient(); if (!client) return; try { const result = await workspaceRequest("setup_status", { client_id: client.id, helper_connected: state.workspace.helperConnected }); if (client.id === state.workspace.selectedClientId) renderWorkspaceSetup(result.value); } catch (error) { if (client.id === state.workspace.selectedClientId) renderWorkspaceSetup(); } }
  async function checkWorkspaceHelper() { const client = selectedWorkspaceClient(); if (!client) return; try { const result = await workspaceRequest("check_helper", { client_id: client.id, start_firefox: true }); state.workspace.helperConnected = true; const status = await workspaceRequest("setup_status", { client_id: client.id, helper_connected: true }); renderWorkspaceSetup(status.value); showNotice(`Container Helper connected${result.value?.version ? ` (v${result.value.version})` : ""}.`); } catch (error) { state.workspace.helperConnected = false; try { const status = await workspaceRequest("setup_status", { client_id: client.id, helper_connected: false }); renderWorkspaceSetup(status.value); } catch (_) { renderWorkspaceSetup(); } showNotice(error.message, true); } }
  async function installWorkspaceHelper() { const client = selectedWorkspaceClient(); if (!client) return; try { await workspaceRequest("install_helper", { client_id: client.id }); showNotice("Firefox opened the existing Helper Extension installer through SmartAction Core."); } catch (error) { showNotice(error.message, true); } }
  async function openWorkspaceAddons() { const client = selectedWorkspaceClient(); if (!client) return; try { await workspaceRequest("open_addons", { client_id: client.id }); showNotice("Firefox Add-ons opened through SmartAction Core."); } catch (error) { showNotice(error.message, true); } }
  async function repairWorkspaceSetup() { try { await workspaceRequest("repair_setup"); state.workspace.helperConnected = null; renderWorkspaceSetup(); showNotice("Native Messaging Host repair requested through SmartAction Core."); } catch (error) { showNotice(error.message, true); } }

  // Workspace presentation stays browser-only; persistence and Firefox work remain in Core.
  function renderWorkspace() {
    const list = $("#workspace-list"); const workspace = state.workspace; $("#workspace-count").textContent = `${workspace.clients.length} 位客戶、${workspace.folders.length} 個資料夾`;
    const groups = [{ id: "", name: "未分類客戶" }, ...workspace.folders]; list.replaceChildren(...groups.map((folder) => renderWorkspaceFolder(folder))); renderWorkspaceSetup();
  }
  function renderWorkspaceFolder(folder) {
    const section = document.createElement("section"); section.className = "workspace-folder"; section.dataset.folderId = folder.id;
    const header = document.createElement("div"); header.className = "workspace-folder-heading"; const title = document.createElement("strong"); title.textContent = folder.name; const count = document.createElement("span"); const clients = state.workspace.clients.filter((client) => (client.folderId || "") === folder.id); count.textContent = `${clients.length} 位客戶 · 可拖曳客戶到此資料夾`; header.append(title, count);
    const controls = document.createElement("div"); controls.className = "row-controls"; controls.append(rowButton("新增客戶", () => openWorkspaceClientInFolder(folder.id))); if (folder.id) controls.append(rowButton("重新命名", () => renameWorkspaceFolder(folder)), rowButton("刪除", () => deleteWorkspaceFolder(folder))); header.append(controls);
    const clientList = document.createElement("div"); clientList.className = "workspace-client-list"; clientList.dataset.folderId = folder.id; clientList.addEventListener("dragover", (event) => { if (!state.workspace.draggedElement) return; event.preventDefault(); clientList.classList.add("drop-target"); }); clientList.addEventListener("dragleave", () => clientList.classList.remove("drop-target")); clientList.addEventListener("drop", (event) => dropWorkspaceClient(event, clientList)); clients.forEach((client) => clientList.append(renderWorkspaceClient(client))); section.append(header, clientList); return section;
  }
  function openWorkspaceClientInFolder(folderId) { openWorkspaceEditor(); $("#workspace-client-folder").value = folderId; }
  function renderWorkspaceClient(client) {
    const card = document.createElement("article"); card.className = "workspace-client-card"; card.draggable = true; card.dataset.clientId = client.id;
    const handle = document.createElement("span"); handle.className = "workspace-drag-handle"; handle.title = "拖曳以排序或移動到資料夾"; handle.setAttribute("aria-hidden", "true"); handle.textContent = "⠿";
    const info = document.createElement("div"); const title = document.createElement("strong"); title.textContent = client.name; const detail = document.createElement("span"); detail.textContent = [client.containerName ? `容器：${client.containerName}` : "一般 Firefox", `${(client.urls || []).length} 個網址`].join(" · "); info.append(title, detail);
    const controls = document.createElement("div"); controls.className = "row-controls"; controls.append(rowButton(`網址 (${(client.urls || []).length})`, () => { state.workspace.expandedClientId = state.workspace.expandedClientId === client.id ? null : client.id; renderWorkspace(); }), rowButton("編輯", () => openWorkspaceEditor(client.id)), rowButton("啟動", () => launchWorkspace(client.id)));
    card.addEventListener("click", (event) => { if (!event.target.closest("button, a")) { state.workspace.selectedClientId = client.id; renderWorkspace(); refreshWorkspaceSetup(); } }); card.addEventListener("dragstart", (event) => { state.workspace.draggedElement = card; card.classList.add("dragging"); event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/plain", client.id); }); card.addEventListener("dragend", () => { state.workspace.draggedElement = null; $$(".workspace-client-card, .workspace-client-list").forEach((item) => item.classList.remove("dragging", "drop-target")); }); card.append(handle, info, controls);
    if (state.workspace.expandedClientId === client.id) { const urls = document.createElement("div"); urls.className = "workspace-client-urls"; if (!(client.urls || []).length) { urls.textContent = "此客戶尚未設定網址。"; } else (client.urls || []).forEach((entry) => { const link = document.createElement("a"); try { const parsed = new URL(entry.url); if (!/^https?:$/.test(parsed.protocol)) throw new Error("unsupported URL"); link.href = parsed.href; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = `${entry.name || "未命名網址"} · ${parsed.href}`; } catch (_) { link.removeAttribute("href"); link.textContent = `${entry.name || "未命名網址"} · 無效網址`; link.classList.add("invalid-url"); } urls.append(link); }); card.append(urls); }
    if (client.id === state.workspace.selectedClientId) card.classList.add("selected"); return card;
  }
  function renderWorkspaceSetup(status = null) { const client = selectedWorkspaceClient(); const enabled = !!client; $("#workspace-setup-title").textContent = client ? client.name : "請選擇客戶"; ["#launch-workspace", "#check-workspace-helper", "#install-workspace-helper", "#open-workspace-addons"].forEach((id) => $(id).disabled = !enabled); const pill = $("#workspace-helper-status"); const cells = $("#workspace-setup-grid"); cells.replaceChildren(); if (!client) { $("#workspace-setup-summary").textContent = "選擇客戶後可檢查其 Firefox 設定檔與 Helper 連線。"; pill.textContent = "尚未檢查"; pill.classList.remove("online"); return; } const data = status || {}; $("#workspace-setup-summary").textContent = data.profile_error || (data.firefox_installed === false ? "SmartAction Core 找不到 Firefox。" : "使用下方按鈕驗證或修復既有的 Firefox Helper 整合。 "); pill.textContent = data.helper_connected === true ? "Helper 已連線" : data.helper_connected === false ? "Helper 無法使用" : "尚未檢查"; pill.classList.toggle("online", data.helper_connected === true); [["Firefox", data.firefox_installed === false ? "找不到" : "可使用"], ["設定檔", data.profile_name || "自動選擇"], ["容器 Helper", data.container_helper_installed ? "已安裝" : "未安裝"], ["原生主機", data.native_host_registered ? "已註冊" : "未註冊"]].forEach(([label, value]) => { const cell = document.createElement("div"); const heading = document.createElement("span"); heading.textContent = label; const text = document.createElement("strong"); text.textContent = value; cell.append(heading, text); cells.append(cell); }); }
  async function createWorkspaceFolder() { const name = prompt("資料夾名稱："); if (name === null) return; try { await workspaceRequest("create_folder", { name }); await refreshWorkspace(); showNotice("資料夾已建立。"); } catch (error) { showNotice(error.message, true); } }
  async function renameWorkspaceFolder(folder) { const name = prompt("資料夾名稱：", folder.name); if (name === null) return; try { await workspaceRequest("rename_folder", { folder_id: folder.id, name }); await refreshWorkspace(); showNotice("資料夾已重新命名。"); } catch (error) { showNotice(error.message, true); } }
  async function deleteWorkspaceFolder(folder) { if (!confirm(`刪除「${folder.name}」？其中客戶會移至未分類客戶。`)) return; try { await workspaceRequest("delete_folder", { folder_id: folder.id }); await refreshWorkspace(); showNotice("資料夾已刪除，客戶已移至未分類客戶。"); } catch (error) { showNotice(error.message, true); } }
  function addWorkspaceUrl(data = { name: "", url: "" }) { const row = document.createElement("div"); row.className = "workspace-url-row"; const name = document.createElement("input"); name.placeholder = "網址名稱"; name.value = data.name || ""; name.dataset.urlName = "true"; const url = document.createElement("input"); url.placeholder = "https://example.com"; url.value = data.url || ""; url.dataset.urlValue = "true"; row.append(name, url, rowButton("移除", () => row.remove())); $("#workspace-url-list").append(row); }
  function openWorkspaceEditor(clientId = null) { const client = clientId ? state.workspace.clients.find((item) => item.id === clientId) : null; $("#workspace-editor").classList.remove("hidden"); $("#workspace-editor-title").textContent = client ? `編輯：${client.name}` : "新增客戶"; $("#workspace-client-id").value = client?.id || ""; $("#workspace-client-name").value = client?.name || ""; fillSelect("#workspace-client-folder", [["", "未分類客戶"], ...state.workspace.folders.map((folder) => [folder.id, folder.name])], client?.folderId || ""); fillSelect("#workspace-client-profile", [["", "自動選擇 Firefox 設定檔"], ...state.workspace.profiles.map((profile) => [profile.name, profile.name])], client?.firefoxProfile || ""); $("#workspace-client-container").value = client?.containerName || ""; $("#workspace-url-list").replaceChildren(); (client?.urls || []).forEach(addWorkspaceUrl); if (!(client?.urls || []).length) addWorkspaceUrl(); $("#delete-workspace-client").classList.toggle("hidden", !client); $("#workspace-client-name").focus(); }

  async function refresh() {
    try { const [status, settings, preferences, actions] = await Promise.all([api("/api/v1/status"), api("/api/v1/settings"), api("/api/v1/runtime-preferences"), api("/api/v1/actions")]); applyStatus(status); applySettings(settings.settings); applyPreferences(preferences.preferences); renderActions(actions.actions); clearNotice(); }
    catch (error) { $("#connection-dot").className = "dot error"; $("#connection-label").textContent = "Core unavailable"; $("#core-status").textContent = "Core offline"; showNotice(error.message, true); }
  }
  function showView(name, moduleName = "") { $$(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${name}`)); $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === name && !moduleName)); const titles = { dashboard: "儀表板", ring: "設定", actions: "動作管理", profiles: "設定檔", powershell: "PowerShell 腳本庫", workspace: "客戶工作區", future: moduleName || "即將推出" }; $("#page-title").textContent = titles[name]; window.scrollTo(0, 0); if (name === "future") $("#future-title").textContent = moduleName; if (name === "powershell") refreshPowerShell(); if (name === "workspace") refreshWorkspace(); }
  async function uploadBackground(file) { if (!file) return; if (file.size > 10 * 1024 * 1024) { showNotice("背景圖片不可超過 10 MB。", true); return; } try { const base64 = await fileToBase64(file); const response = await api("/api/v1/settings/background", jsonOptions("POST", { filename: file.name, contentBase64: base64 })); applySettings({ ...state.settings, ui_background: response.ui_background }); $("#save-state").textContent = "背景已套用到控制中心。"; showNotice("背景已由 SmartAction Core 儲存並套用。"); } catch (error) { showNotice(error.message, true); } finally { $("#background-file").value = ""; } }
  function fileToBase64(file) { return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onerror = () => reject(new Error("Could not read the selected file.")); reader.onload = () => resolve(String(reader.result).split(",", 2)[1] || ""); reader.readAsDataURL(file); }); }
  async function clearBackground() { try { const response = await api("/api/v1/settings/background", { method: "DELETE" }); applySettings(response.settings); showNotice("Custom background cleared."); } catch (error) { showNotice(error.message, true); } }
  let settingsSaveTimer = null;
  async function applySettingsAutomatically() { const saveState = $("#save-state"); settingsSaveTimer = null; saveState.textContent = "Applying to SmartAction…"; const changes = { hotkey: $("#setting-hotkey").value.trim(), theme: $("#setting-theme").value, constellation: $("#setting-constellation").value, constellation_color: $("#setting-color").value, ui_theme: $("#setting-ui-theme").value, ui_background_opacity: Number($("#setting-opacity").value), ui_background_zoom: Number($("#setting-zoom").value), ui_background_focus_x: Number($("#setting-focus-x").value) / 100, ui_background_focus_y: Number($("#setting-focus-y").value) / 100 };
    try { const [settingsResponse, preferencesResponse] = await Promise.all([api("/api/v1/settings", jsonOptions("PATCH", { changes })), api("/api/v1/runtime-preferences", jsonOptions("PATCH", { changes: { autostart: $("#setting-autostart").checked, reduced_motion: $("#setting-reduced-motion").checked } }))]); applySettings(settingsResponse.settings); applyPreferences(preferencesResponse.preferences); saveState.textContent = "Applied to SmartAction."; } catch (error) { saveState.textContent = "Could not apply changes."; showNotice(error.message, true); } }
  function queueSettingsApply() { if (settingsSaveTimer) clearTimeout(settingsSaveTimer); $("#save-state").textContent = "Changes pending…"; settingsSaveTimer = setTimeout(applySettingsAutomatically, 300); }
  async function exportProfile() { try { const response = await api("/api/v1/profiles/export"); const blob = new Blob([JSON.stringify(response.profile, null, 2)], { type: "application/json" }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = response.filename || "smartaction-profile.json"; link.click(); URL.revokeObjectURL(url); showNotice("Profile exported."); } catch (error) { showNotice(error.message, true); } }
  async function importProfile() { const file = $("#import-profile-file").files[0]; if (!file) { showNotice("Choose a SmartAction profile JSON file first.", true); return; } try { const profile = JSON.parse(await file.text()); if (!confirm("Import replaces current actions, settings, PowerShell Library, and Client Workspace data. Continue?")) return; await api("/api/v1/profiles/import", jsonOptions("POST", { profile })); $("#import-profile-file").value = ""; showNotice("Profile imported. SmartAction Core is reloading live resources."); setTimeout(refresh, 150); } catch (error) { showNotice(error instanceof SyntaxError ? "The selected file is not valid JSON." : error.message, true); } }

  $$(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view, button.dataset.module)));
  $$('[data-go]:not(.coverflow-card)').forEach((button) => button.addEventListener("click", () => showView(button.dataset.go, button.dataset.module)));
  $("#refresh-button").addEventListener("click", refresh); ["#setting-opacity", "#setting-zoom", "#setting-focus-x", "#setting-focus-y"].forEach((id) => $(id).addEventListener("input", () => { updateRangeLabels(); previewControlCenterBackground(); queueSettingsApply(); }));
  ["#setting-hotkey", "#setting-theme", "#setting-constellation", "#setting-color", "#setting-ui-theme", "#setting-autostart", "#setting-reduced-motion"].forEach((id) => $(id).addEventListener("change", queueSettingsApply)); $("#background-file").addEventListener("change", (event) => uploadBackground(event.target.files[0])); $("#clear-background").addEventListener("click", clearBackground);
  $("#new-root-action").addEventListener("click", () => openEditor()); $("#close-editor").addEventListener("click", closeEditor); $("#action-type").addEventListener("change", toggleTarget); $("#action-icon").addEventListener("input", () => setActionIcon($("#action-icon").value)); $("#open-emoji-picker").addEventListener("click", () => openEmojiPicker()); $("#close-emoji-picker").addEventListener("click", () => $("#emoji-picker-dialog").close()); $("#action-editor").addEventListener("submit", saveAction); $("#delete-action").addEventListener("click", deleteAction);
  $("#export-profile").addEventListener("click", exportProfile); $("#import-profile").addEventListener("click", importProfile);
  $("#export-workspace").addEventListener("click", exportWorkspace); $("#import-workspace-file").addEventListener("change", (event) => importWorkspace(event.target.files[0])); $("#new-workspace-folder").addEventListener("click", createWorkspaceFolder); $("#new-workspace-client").addEventListener("click", () => openWorkspaceEditor()); $("#close-workspace-editor").addEventListener("click", closeWorkspaceEditor); $("#create-workspace-profile").addEventListener("click", createWorkspaceFirefoxProfile); $("#add-workspace-url").addEventListener("click", () => addWorkspaceUrl()); $("#workspace-editor").addEventListener("submit", saveWorkspaceClient); $("#delete-workspace-client").addEventListener("click", deleteWorkspaceClient); $("#launch-workspace").addEventListener("click", () => launchWorkspace()); $("#check-workspace-helper").addEventListener("click", checkWorkspaceHelper); $("#install-workspace-helper").addEventListener("click", installWorkspaceHelper); $("#open-workspace-addons").addEventListener("click", openWorkspaceAddons); $("#repair-workspace-setup").addEventListener("click", repairWorkspaceSetup);
  initialiseModuleCoverflow(); initialisePowerShellControls(); $("#ps-category-filter").addEventListener("change", refreshPowerShell); $("#ps-new-script").addEventListener("click", () => openPowerShellEditor()); $("#ps-close-editor").addEventListener("click", closePowerShellEditor); $("#ps-editor").addEventListener("submit", savePowerShellScript); $("#ps-delete-script").addEventListener("click", deletePowerShellScript); $("#ps-close-sop").addEventListener("click", () => $("#ps-sop").classList.add("hidden")); $("#ps-copy-sop").addEventListener("click", copyPowerShellSop); $("#ps-confirm-run").addEventListener("click", runPowerShellScript); $("#ps-close-result").addEventListener("click", () => $("#ps-run-result").classList.add("hidden"));
  refresh().finally(() => {
    if (["dashboard", "ring", "actions", "profiles", "powershell", "workspace"].includes(requestedView)) showView(requestedView);
  });
})();
