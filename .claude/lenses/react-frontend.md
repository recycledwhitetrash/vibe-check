<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Web / frontend lenses — React, Next.js, browser apps

- **Frontend / UX integrity**: dead-end error states, unhandled loading states, optimistic
  updates that don't reconcile on failure, forms that submit invalid or partial state, no
  error boundary, keyboard/focus traps that strand non-mouse users
- **Accessibility**: keyboard-only flows broken, screen reader markup missing or wrong,
  interactive elements without accessible labels, focus management on dialogs and modals
- **API & contract (client side)**: assumptions about response shape that will break on API
  change, no handling for unexpected fields or missing fields, request size not capped on
  client, auth token handling (storage, refresh, expiry)
- **XSS vectors**: `dangerouslySetInnerHTML` with any value derived from user input or
  external data; `href` / `src` / `action` attributes set from user-controlled strings
  without blocking `javascript:` URLs (`javascript:alert(1)` is a valid href); `eval()` or
  `new Function()` called with any dynamic content; third-party scripts loaded from
  user-supplied URLs
- **React hooks bugs**: `useEffect` missing cleanup for timers, subscriptions, and fetch
  calls — fires state updates on unmounted components and leaks memory; stale closure from
  an incomplete dependency array — the effect reads an old value of a variable that has
  since changed; async race condition where multiple concurrent calls compete to set state
  and the last-to-resolve wins regardless of which was last-started (fix: abort controller
  or sequence counter); object or array literal created inline in JSX props or a
  `useEffect` dependency array — new reference every render, causes infinite loop
- **Auth — client-side gaps**: route guard that only hides the UI but the underlying API
  route has no auth check — bypassed by calling the API directly; auth tokens stored in
  `localStorage` or `sessionStorage` are readable by any XSS payload — prefer httpOnly
  cookies for session tokens; token refresh race condition when multiple parallel requests
  all receive 401 simultaneously and each independently attempts a refresh (token rotation
  invalidates the others); JWT decoded on the client and claims trusted without
  server-side verification — the client can't verify the signature
- **Environment variable leakage**: `NEXT_PUBLIC_` or `REACT_APP_` prefixed variables are
  inlined into the browser bundle at build time — any secret assigned to them is shipped to
  every user; source maps deployed to production expose full original source code to anyone
  who opens devtools
- **Next.js data exposure**: `getServerSideProps` / `getStaticProps` returning objects with
  sensitive fields (user records, internal config, tokens) — the full return value is
  serialized into `__NEXT_DATA__` in the page HTML and visible to anyone who views source;
  API routes under `pages/api/` or `app/api/` missing authentication checks; server actions
  without authorization (any authenticated user can invoke them, not just the intended
  role); `next.config.js` rewrites that proxy internal services without adding an auth
  header; no security headers set (`Content-Security-Policy`, `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy`) — Next.js does not set these by default
- **Form security**: client-side validation with no equivalent server-side check — disabled
  JavaScript or a direct API call bypasses it entirely; sensitive form data submitted via
  GET method appears in browser history, server access logs, and the `Referer` header sent
  to third parties; file input with no size or type check on the client before upload begins
- **Content Security Policy**: CSP header absent, or set with `unsafe-inline` or
  `unsafe-eval` in `script-src` — without a restrictive CSP a successful XSS can load
  arbitrary external scripts and exfiltrate data; `report-uri` or `report-to` absent so
  violations are never observed
- **Subresource Integrity (SRI)**: third-party scripts and stylesheets loaded from CDNs
  without an `integrity="sha384-..."` attribute; a compromised CDN, a BGP hijack, or a
  CDN provider incident silently serves malicious content to all users
- **Clickjacking**: no `X-Frame-Options: DENY` header and no `frame-ancestors 'none'` in
  CSP; the page is embeddable in an attacker's iframe and user clicks on sensitive actions
  (confirm payment, approve OAuth, delete account) are intercepted
- **Cookie security flags**: session cookies or auth cookies set without `Secure` (sent
  over HTTP), `HttpOnly` (readable by JS), or `SameSite=Lax`/`Strict` (CSRF vector);
  applies to cookies set in Next.js API routes, server actions, and `Set-Cookie` response
  headers
- **React Server Component data boundary**: RSC props passed across the `"use client"`
  boundary are serialized into the browser bundle; sensitive server-side data (DB records,
  internal config, access tokens) included in those props crosses the trust boundary and
  is visible to the user in the page source or network tab
- **Accessibility gaps**: color contrast ratio below 4.5:1 on body text or 3:1 on large
  text; CSS animations or transitions that do not respect `prefers-reduced-motion: reduce`;
  layout that breaks or clips content at narrow viewport widths, trapping users
- **Bundle size and rendering performance**: new production dependencies that are
  known-heavy (moment.js, full lodash, jQuery) when a lighter alternative or native API
  exists; barrel imports (`import { x } from 'library'`) instead of deep imports
  (`import x from 'library/specific'`) that block tree-shaking and inflate the bundle;
  `React.memo`, `useMemo`, or `useCallback` absent on components or computed values
  passed as props where reference instability causes unnecessary child re-renders;
  sequential `await fetch()` calls that could be `Promise.all` (fetch waterfall);
  layout thrashing — reading DOM geometry (`.offsetHeight`, `.getBoundingClientRect()`)
  then writing layout properties inside the same loop; below-fold images missing
  `loading="lazy"`
