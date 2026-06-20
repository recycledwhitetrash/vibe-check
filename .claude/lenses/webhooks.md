<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Webhook lenses

- **Missing signature verification**: most providers (Stripe, GitHub, Twilio, Shopify,
  Discord) include an HMAC signature header; if it is not verified, any caller can POST
  fake events to the endpoint and trigger your business logic
- **Replay attacks**: a captured valid webhook request can be replayed later; the provider
  typically includes a timestamp in the signed payload (Stripe does); reject events where
  the timestamp is older than ~5 minutes
- **Processing before acknowledging**: the event is processed before returning a 200;
  if processing takes too long, the provider times out and retries — the event runs twice;
  respond 200 immediately, then process the event asynchronously
- **No idempotency**: providers retry on timeout or 5xx; the same event can be delivered
  more than once; use the event ID as an idempotency key and check it before processing
- **Event type not validated from verified payload**: checking `req.body.type` before
  verifying the signature means an attacker can POST `{ "type": "payment.succeeded" }` and
  trigger the success handler; always derive the event type from the verified payload
- **Returning the wrong status on unprocessable events**: returning 5xx on a malformed
  event causes the provider to retry indefinitely; returning 4xx tells the provider to
  stop; distinguish between "I failed to process this" (5xx, retry) and "this event is not
  for me" (2xx, discard) and "this event is invalid" (4xx, stop retrying)
- **SSRF via user-registered webhook URLs**: if the application allows users to register
  their own callback URLs, an attacker registers `http://169.254.169.254/latest/meta-data/`
  (AWS IMDS), internal service hostnames, or `file://` URIs; validate registered URLs
  against a blocklist of RFC1918, link-local, and loopback ranges, and restrict to
  `https://` scheme only
- **Webhook secret rotation**: no mechanism to rotate the HMAC signing secret without
  downtime; secret hardcoded in an environment variable rather than a secrets manager;
  no grace period management — old and new secrets must both be accepted during a rotation
  window, then the old one revoked
- **Delivery failure visibility**: no alerting when webhook delivery fails repeatedly;
  missed events go undetected until a user reports a data inconsistency; no dead-letter
  queue, no retry dashboard, no monitoring on the endpoint's error rate
