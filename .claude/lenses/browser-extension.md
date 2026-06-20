<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Browser extension lenses

- **Over-broad manifest permissions**: `"matches": ["<all_urls>"]` or host permissions for
  all sites when only a subset is needed; `tabs`, `history`, `bookmarks`, `cookies`
  declared without necessity — each is a privacy risk and a breach vector if the extension
  is compromised
- **Content scripts trusting page content**: content scripts reading DOM values (form
  fields, page text, cookies) and forwarding them to the background; a malicious page can
  poison those values to inject data into your extension's context
- **Message passing without origin validation**: `chrome.runtime.onMessage` accepting
  messages from any sender without checking `sender.id` or `sender.origin`; content
  scripts treated as trusted when they may be running in a hostile page context
- **`chrome.storage` holding secrets in plaintext**: `storage.local` and `storage.sync`
  are readable by all extension scripts and accessible to users via DevTools; tokens and
  credentials stored here are exposed to any XSS or content script compromise
- **`externally_connectable` too broad**: allows arbitrary web pages to send messages
  directly to the extension background; should be locked to specific origins
- **`eval()` or remote code execution**: `eval()`, `new Function()`, or
  `importScripts()` with a remote URL — all violate Manifest V3 CSP and create code
  injection vectors; extension code must be self-contained and static
- **`chrome.tabs.executeScript` / `scripting.executeScript` with dynamic strings**: calling
  these with a user-controlled or externally-derived code string is equivalent to `eval()`
  with elevated privileges — only ever pass hardcoded string arguments
- **Background service worker lifecycle**: Manifest V3 service workers are terminated by
  the browser after ~30 seconds of inactivity; module-level variables are lost on
  termination; state that must persist across events must go to `chrome.storage`, not
  memory; code that assumes the service worker is always alive will silently lose state
- **Web accessible resources**: files listed in `web_accessible_resources` in
  `manifest.json` are fetchable by any web page at `chrome-extension://[id]/[file]`;
  internal config files, key material, or data files accidentally listed become accessible
  to all origins
- **Content script DOM access scope**: content scripts share the full DOM with the page
  they run in; a content script that reads `document.forms`, `document.cookie` (when
  `HttpOnly` is absent), or intercepts `input` events has privileged access to every page
  the extension matches; over-broad `matches` combined with DOM reading is a significant
  privacy risk even without an explicit bug
- **Extension update supply chain**: extensions auto-update silently; a compromised Chrome
  Web Store publisher account or a self-hosted update URL under attacker control can push
  a malicious version to all installed instances with no user approval beyond the original
  install; treat the update endpoint and publisher credentials as high-value secrets
