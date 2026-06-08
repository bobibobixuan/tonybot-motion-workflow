export function t(key, params) {
  let value = window._i18nData;
  for (const part of key.split(".")) {
    if (value == null || typeof value !== "object") return key;
    value = value[part];
  }
  if (value === undefined) return key;
  if (params && typeof value === "string") {
    for (const [paramKey, paramValue] of Object.entries(params)) {
      value = value.replace(`{${paramKey}}`, paramValue);
    }
  }
  return value;
}

export function applyI18nToDOM(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.getAttribute("data-i18n");
    if (!key) return;
    const value = t(key);
    if (value && value !== key) element.textContent = value;
  });

  root.querySelectorAll("[data-i18n-title]").forEach((element) => {
    const key = element.getAttribute("data-i18n-title");
    if (!key) return;
    const value = t(key);
    if (value && value !== key) element.title = value;
  });
}

export async function initI18n() {
  const preferredLang = (navigator.language || "").startsWith("zh") ? "zh-CN" : "en-US";
  if (preferredLang !== "zh-CN") {
    try {
      const response = await fetch("i18n/en-US.json");
      if (response.ok) {
        window._i18nData = await response.json();
        window._i18nLang = "en-US";
      }
    } catch (error) {
      console.warn("i18n fallback to zh-CN:", error);
    }
  }
  window.t = t;
  applyI18nToDOM();
  return window._i18nLang || "zh-CN";
}
