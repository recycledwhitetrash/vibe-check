<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Stripe / payment integration lenses

- **Amount calculated on the client**: the server receives a price, quantity, or total
  from the client and trusts it; a caller can POST any amount; the server must calculate
  or verify the charge amount from its own data (product catalog, order record), never from
  a client-supplied value
- **Webhook signature not verified**: use `stripe.webhooks.constructEvent()` — not manual
  HMAC comparison or checking `req.body.type` before verification; see Webhook lenses
- **Subscription status checked client-side**: `user.subscription === 'active'` checked
  in client code or from a client-readable field; the authoritative check must be
  server-side against Stripe's API or a server-owned field synced via webhook
- **No idempotency key on charge creation**: duplicate network requests or user double-
  clicks create duplicate charges; pass a unique `idempotencyKey` on every
  `paymentIntents.create` and `charges.create` call
- **Test mode keys in production**: `sk_test_` keys process no real money; if a test key
  reaches a production environment, payments silently fail or appear to succeed without
  charging anyone
- **PCI scope expansion**: logging card numbers or CVVs anywhere; passing raw card data
  through your server when using Stripe Elements (which is designed to keep card data off
  your server and reduce PCI scope); storing card details outside of Stripe's vault
- **Incomplete webhook event handling**: acting on `payment_intent.succeeded` but not
  handling `payment_intent.payment_failed`, disputes, refunds, and subscription
  cancellations — orders get stuck in wrong states silently; map every event type your
  integration depends on
- **`livemode` not checked**: Stripe test events can be sent to production webhook
  endpoints; always verify `event.livemode` matches the expected environment before
  fulfilling orders or granting access
- **Free trial and coupon abuse**: trial eligibility checked by email only — create a new
  address, get another trial; coupon codes applied without validating the coupon is still
  active, not past its `redeem_by` date, not past its `max_redemptions` limit, and not
  restricted to specific products or customers
- **Currency and decimal handling**: Stripe amounts are in the smallest currency unit
  (cents for USD, pence for GBP) but whole units for zero-decimal currencies (JPY, KRW);
  mixing up the multiplier — `amount: 1000` means $10.00 USD but ¥1000 JPY — causes
  order-of-magnitude errors in charge amounts; always document and assert the currency
  unit alongside every amount field
- **Metered billing atomicity**: `subscriptionItems.createUsageRecord()` failures that are
  silently swallowed leave billing state inconsistent; usage records reported for the wrong
  subscription item ID are ignored without an error; no reconciliation between what your
  system recorded as usage and what Stripe actually billed
- **Checkout Session expiry**: Sessions expire after 24 hours; code that attempts to
  retrieve or complete an expired session receives a `resource_missing` error; no graceful
  handling (redirect back to cart, re-create session) leaves the user stuck at a dead URL
