<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Native app lenses (iOS, Android, desktop)

- **OS permission model**: does the app request only the permissions it needs? does it
  handle permission denial gracefully?
- **Credential and key storage**: secrets in source, hardcoded in binary, or stored in
  OS keychain / secure enclave? what happens if device is compromised?
- **IPC & inter-process auth**: if the app communicates via sockets, named pipes, or
  shared memory — who else can connect? is the channel authenticated?
- **Memory safety**: buffer overflows from untrusted input, use-after-free, uninitialized
  memory read; applies to C/C++/Rust unsafe blocks and any FFI boundary
- **Resource leaks**: file handles, sockets, database connections, and locks released on
  all code paths including error paths and cancellation
- **Concurrency**: mutex misuse (double-lock, priority inversion, lock inversion);
  `volatile` absent on shared memory; race on lazy initialization
- **Certificate pinning**: no SSL certificate pinning allows MITM attacks on
  rooted/jailbroken devices or on a compromised network; pinned certificate hashes or
  public keys not updated before certificate rotation causes a production outage for all
  installed versions
- **Screenshot and screen recording protection**: sensitive screens (auth codes, financial
  data, health records) not setting `FLAG_SECURE` on Android — content visible in the
  recent apps switcher and screenshotted by accessibility services; iOS equivalent
  (`allowScreenshots = false` or obscuring the window on `UIApplicationUserDidTakeScreenshotNotification`)
  absent
- **Clipboard data exposure**: sensitive values (passwords, tokens, account numbers)
  written to the system clipboard without clearing after a short timeout; clipboard
  content readable by all apps on Android < 10 and in some iOS accessibility contexts;
  password manager autofill writes to clipboard and leaves it there indefinitely
- **Jailbreak and root detection**: apps handling financial data, DRM-protected content,
  or protected health information not detecting rooted/jailbroken devices; at minimum,
  alert the user and disable high-risk features when root/jailbreak is detected
- **App signing and integrity**: APK or IPA signed with a debug keystore in production
  builds; no integrity attestation (Google Play Integrity API, Apple DeviceCheck) for
  apps that must verify they haven't been repackaged or tampered with (e.g. license
  enforcement, anti-cheat, financial apps)
- **Deep link validation**: Android `intent-filter` with `android:exported="true"` and no
  host or path restriction — any app can send an intent to this component with arbitrary
  data; iOS universal link `apple-app-site-association` file not served over HTTPS or not
  restrictive enough, allowing any path to be claimed
