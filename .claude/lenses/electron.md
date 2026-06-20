<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Electron lenses

- **`nodeIntegration: true` in renderer**: any XSS in the renderer process has full
  Node.js access — filesystem, shell execution, network sockets; this is the single most
  critical Electron misconfiguration; `nodeIntegration` must be `false` for any window
  that loads remote or user-supplied content
- **`contextIsolation: false`**: exposes Node.js globals and `require` in the renderer's
  web context; use `contextBridge.exposeInMainWorld()` to expose only specific, validated
  functions to the renderer — never the raw Node API
- **Remote content in an unsandboxed renderer**: loading a third-party URL in a
  `BrowserWindow` without `sandbox: true` and a `partition`; a compromised page in the
  renderer can call preload APIs and escalate to main process privileges
- **`shell.openExternal()` with user-controlled URL**: opens the URL in the default
  browser or OS application handler; a `javascript:`, `file:`, or custom protocol URL can
  execute code or open local files; validate the protocol is `http:` or `https:` before
  calling
- **`ipcMain` handlers without input validation**: renderer sends an IPC message and the
  main process executes it without checking the sender or validating the payload; a
  compromised renderer (XSS, malicious content) gains main-process capabilities through
  every unguarded handler
- **Auto-updater without code signing**: update fetched over HTTP or from an unverified
  source; an attacker who can intercept the update or control the update server can push
  malicious code to all installed instances; Electron's built-in updater requires
  code-signed releases and HTTPS
- **`webContents.executeJavaScript()` with any dynamic string**: equivalent to `eval()`
  in the renderer with the caller's privileges; only ever pass hardcoded string literals —
  never user input, network data, or variables
- **Protocol handler registration**: `app.setAsDefaultProtocolClient('myapp')` registers
  the app to receive `myapp://` deep links from the browser; incoming URLs are passed by
  the OS as command-line arguments; validate and sanitize every parameter before use, and
  never pass them to `shell.exec()` or `ipcMain` handlers directly
- **Child window `webPreferences` inheritance**: windows opened via `window.open()` from
  a renderer inherit the parent's `webPreferences` (including `nodeIntegration`) unless
  `webContents.setWindowOpenHandler()` explicitly overrides them with safe defaults; a
  third-party page that opens a popup inherits the same Node.js access as the main window
- **`allowRunningInsecureContent`**: allows an HTTPS page to load HTTP subresources; if
  `nodeIntegration` is also enabled, a network MITM substituting a malicious HTTP resource
  is a remote code execution path; should always be `false`
- **Native Node module supply chain**: native `.node` addons loaded in Electron are
  compiled binaries; pre-built binaries downloaded from npm are not compiled from source
  and are not reproducible; a compromised addon publisher can push malicious native code
  that runs at OS level with no sandbox
- **Renderer process crash handling**: `webContents.on('render-process-gone')` not
  handled; the app continues presenting a frozen or blank UI after a renderer crash without
  telling the user or attempting recovery; the main process should detect the crash and
  either reload the window or show an error state
