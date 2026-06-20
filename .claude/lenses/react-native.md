<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### React Native lenses

- **Insecure data storage**: `AsyncStorage` stores data in plaintext and is readable on
  rooted/jailbroken devices and via `adb backup`; use `react-native-keychain` or
  `expo-secure-store` for tokens, credentials, and PII
- **Hardcoded secrets in the JS bundle**: React Native ships the JS bundle as a readable
  file — any string in the bundle (API keys, internal URLs, signing secrets) is trivially
  extractable with a decompiler or `strings`; secrets belong in environment variables
  resolved at build time, never in source
- **Deep link handling without validation**: `myapp://reset-password?token=X` and similar
  deep links accepted without verifying origin or sanitizing parameters; a malicious web
  page can trigger deep links targeting your app; validate all deep link payloads as
  untrusted input
- **WebView with JS bridge open to remote content**: `javaScriptEnabled` on a WebView
  loading a third-party or user-supplied URL; the `onMessage` handler trusting any origin;
  a compromised page can call into your React Native code via `postMessage`
- **Biometric auth bypassed**: `TouchID`/`FaceID`/fingerprint used as a UX gate but the
  actual authorization check is done client-side — a rooted device or hook can spoof the
  result; the server must be the authority on whether the session is authenticated
- **Metro bundler exposed on dev builds**: Metro serves the JS bundle over HTTP on the
  local network during development; a dev build shipped to testers or left on a shared
  network exposes the full source to anyone on that network
- **Expo-specific**: OTA updates via EAS Update deliver a new JS bundle that bypasses app
  store review — a compromised update server or a missing code-signing check can push
  malicious code to all installed instances silently
- **Network security / certificate pinning**: no SSL certificate pinning allows MITM
  attacks on rooted/jailbroken devices; cleartext HTTP allowed via Android
  `android:usesCleartextTraffic="true"` in the manifest or iOS `NSAllowsArbitraryLoads`
  in Info.plist; no minimum TLS version enforced; pinned certificate hashes not updated
  before certificate rotation (causes production outage)
- **App Transport Security / Network Security Config**: iOS ATS and Android NSC exception
  domains broader than necessary; `NSExceptionAllowsInsecureHTTPLoads` or
  `cleartextTrafficPermitted` with domain wildcards; exceptions added during development
  and never removed before production
- **Runtime permission handling**: sensitive permissions (camera, microphone, location,
  contacts) requested at app launch rather than at the point of first use; no rationale
  string explaining why the permission is needed; app not gracefully handling permission
  denial — crashes or shows a blank screen instead of a degraded-but-functional state
- **Debug artifacts in release builds**: `__DEV__` flag used as a security gate;
  `console.log` calls printing tokens, user data, or internal URLs left in release builds
  (readable by other apps on non-sandboxed Android via `adb logcat`); Reactotron or
  Flipper debug bridges left open in release configurations
- **Third-party SDK data collection**: analytics SDKs, crash reporters (Firebase Analytics,
  Sentry, Amplitude, Crashlytics) collecting device identifiers or PII without user
  consent; data sent to third-party servers not disclosed in the privacy policy; IDFA/GAID
  usage without the required consent flow on iOS 14+ / Android 12+
