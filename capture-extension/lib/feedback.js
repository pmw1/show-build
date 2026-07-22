// User feedback: toolbar-badge flashes and system notifications.

export function flashBadge(text, color = '#2e7d32', clearAfterMs = 3000) {
  chrome.action.setBadgeBackgroundColor({ color });
  chrome.action.setBadgeText({ text });
  if (clearAfterMs) {
    setTimeout(() => chrome.action.setBadgeText({ text: '' }), clearAfterMs);
  }
}

export function showQueueBadge(count) {
  if (count > 0) {
    chrome.action.setBadgeBackgroundColor({ color: '#e65100' });
    chrome.action.setBadgeText({ text: String(count) });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
}

export function notify(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icons/icon128.png'),
    title,
    message,
  });
}
