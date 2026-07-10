const NATIVE_HOST = "smartaction_firefox_helper";
const ADDON_ID = "smartaction-container-helper@naughtytiger06.local";
const ADDON_VERSION = "1.0.3";
let polling = false;

async function findContainer(containerName) {
  const containers = await browser.contextualIdentities.query({});
  return containers.find((item) => item.name === containerName);
}

async function launchWorkspace(message) {
  const containerName = (message.containerName || "").trim();
  if (!containerName) {
    return {
      type: "launch_workspace_result",
      requestId: message.requestId,
      success: false,
      error: "containerName is required"
    };
  }

  const container = await findContainer(containerName);
  if (!container) {
    return {
      type: "launch_workspace_result",
      requestId: message.requestId,
      success: false,
      error: `Container not found: ${containerName}`
    };
  }

  let openedCount = 0;
  const urls = Array.isArray(message.urls) ? message.urls : [];
  for (const item of urls) {
    const url = String(item && item.url ? item.url : "").trim();
    if (!url) {
      continue;
    }
    await browser.tabs.create({
      url,
      cookieStoreId: container.cookieStoreId,
      active: openedCount === 0
    });
    openedCount += 1;
  }

  return {
    type: "launch_workspace_result",
    requestId: message.requestId,
    success: true,
    openedCount,
    clientName: message.clientName || ""
  };
}

function helperCheck(message) {
  return {
    type: "helper_check_result",
    requestId: message.requestId,
    success: true,
    addonId: ADDON_ID,
    version: ADDON_VERSION
  };
}

function pollNativeHost() {
  if (polling) {
    return;
  }
  polling = true;

  let port;
  try {
    port = browser.runtime.connectNative(NATIVE_HOST);
  } catch (error) {
    polling = false;
    return;
  }

  port.onMessage.addListener(async (message) => {
    if (!message || !["launch_workspace", "helper_check"].includes(message.type)) {
      return;
    }
    try {
      const result = message.type === "helper_check"
        ? helperCheck(message)
        : await launchWorkspace(message);
      port.postMessage(result);
    } catch (error) {
      port.postMessage({
        type: `${message.type}_result`,
        requestId: message.requestId,
        success: false,
        error: String(error && error.message ? error.message : error)
      });
    }
  });

  port.onDisconnect.addListener(() => {
    polling = false;
  });
}

pollNativeHost();
setInterval(pollNativeHost, 1000);
