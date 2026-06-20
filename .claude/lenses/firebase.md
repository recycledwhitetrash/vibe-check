<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Firebase / Firestore lenses

- **Security rules too permissive**: `allow read, write: if true` or `if request.auth !=
  null` without document ownership checks — any authenticated user can read or overwrite
  any other user's documents; rules must verify `request.auth.uid == resource.data.userId`
  or equivalent for every sensitive collection
- **Rules pass emulator but fail in production**: the Firebase emulator does not enforce
  all production behaviors and does not catch all rule logic errors; always test rules
  against realistic data shapes and run `firebase emulators:exec` with a test suite, not
  just interactive testing
- **Admin SDK bypasses rules entirely**: Cloud Functions and server code using the Admin
  SDK skip Firestore security rules; if a Cloud Function writes user-controlled data back
  to Firestore without its own validation, rules provide no protection for that write path
- **API key exposed in client bundle**: Firebase config (`apiKey`, `projectId`,
  `storageBucket`) is intentionally shipped to the browser — this is by design, not a
  secret — but the entire security model then depends on rules being correct; a permissive
  rule plus an exposed key equals full database access for anyone
- **Cloud Functions `onRequest` publicly callable**: HTTP-triggered Cloud Functions have
  no built-in authentication; any caller on the internet can invoke them; must check
  `context.auth` on callable functions or verify an ID token manually on HTTP functions
- **`onWrite` / `onUpdate` trigger loops**: a Cloud Function that writes to the same
  document it was triggered by will fire itself again; Firestore does not prevent this;
  always check that the new write actually changes data before writing, or use a separate
  `processing` flag
- **Firebase Storage rules separate from Firestore rules**: setting Firestore rules does
  not affect Storage; Storage rules default to deny-all after the free-tier default
  expires, but explicitly written rules may be too broad; check for public read on buckets
  containing PII or user-uploaded files
- **Real-time listeners not unsubscribed**: `onSnapshot` listeners not cleaned up on
  component unmount accumulate over navigation, consume quota, and can deliver data to
  components after the user logs out; always call the unsubscribe function in cleanup
- **Unbounded queries**: Firestore queries on client-readable collections without `.limit()`;
  a caller can fetch an entire large collection in one request with no server-side
  enforcement of result size; combined with permissive rules this is both a data
  exfiltration vector and a cost bomb
- **Firebase Authentication token lifecycle**: custom claims set via
  `admin.auth().setCustomUserClaims()` do not take effect until the client forces a token
  refresh — code that checks claims immediately after setting them sees stale values;
  `verifyIdToken()` without `{ checkRevoked: true }` accepts tokens belonging to
  disabled or deleted accounts
- **Data validation in security rules**: Firestore rules can and should validate the shape
  and types of incoming writes (`request.resource.data.keys().hasOnly([...])`,
  `request.resource.data.score is int`); missing data validation in rules allows malformed
  or oversized documents to be written that break client rendering or violate business
  invariants downstream
- **Firebase Hosting rewrites**: `firebase.json` rewrites exposing Cloud Functions at
  paths under the Hosting domain without intending to; `cleanUrls: true` and
  `trailingSlash` misconfigurations causing unexpected routing behavior or unintentionally
  exposing function endpoints at predictable URLs
