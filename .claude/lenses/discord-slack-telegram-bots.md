<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Discord / Slack / Telegram bot lenses

- **Bot token in source or git history**: the token grants full bot access; anyone with
  it can read messages, post as the bot, and modify server settings; must live in
  environment variables only — never in source, never in logs, never in error messages
- **No webhook origin verification**: Slack and Discord sign webhook payloads with an HMAC
  signature; if the signature is not verified, any caller can POST fake events to your
  endpoint and trigger commands; Telegram uses a secret token in the header — verify it
- **Command injection via user input**: the bot receives a message and passes it
  unsanitized to a shell command, SQL query, template string, or `eval()`; treat all
  content from users, channel names, and usernames as untrusted input
- **Privilege escalation via role ID**: checking `member.roles.has(ADMIN_ROLE_ID)` where
  `ADMIN_ROLE_ID` is hardcoded; role IDs are server-specific and can be reassigned; a
  different role that happens to share an ID (e.g. after server migration) gets elevated
  access unintentionally
- **Rate limit handling absent**: bot does not back off on 429 responses from the platform
  API; gets globally rate limited or temporarily banned; implement exponential backoff and
  respect `Retry-After` headers
- **Storing user IDs as authentication tokens**: Discord and Slack user IDs are public and
  visible to all server members; using a user ID to authorize an API call means any user
  who knows another user's ID can impersonate them in requests to your backend
- **DM vs channel context confusion**: bot responds to a DM with information scoped to a
  specific server (server config, other users' data) that the DM recipient should not
  see; always verify that the requesting context has access to the data being returned
- **Telegram-specific**: webhook endpoint not verifying the `X-Telegram-Bot-Api-Secret-
  Token` header — any caller can send fake updates; polling is safe for development but
  production webhooks must validate origin
- **Slash command interaction token reuse**: Discord interaction tokens are valid for 15
  minutes; if stored and replayed, or if the endpoint does not deduplicate on token, an
  attacker can re-trigger a command after the user acted; track used interaction IDs and
  reject duplicates
- **Bot OAuth scope over-granting**: bot invited with `Administrator` permission or broad
  scopes (`channels:history`, `files:read`, `users:read`) when only narrow permissions
  (e.g. `chat:write`) are needed; least-privilege applies to bot OAuth scopes — audit the
  permission manifest and request only what each feature actually uses
- **User-supplied file and URL handling**: bots that download and process files or URLs
  from users with no file type validation, no size limit, and no SSRF protection; polyglot
  files, zip bombs, and decompression bombs; SSRF via user-supplied URLs the bot fetches
  on behalf of the requester (validate scheme is `https://` and host is not RFC1918)
