<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Django lenses

- **ORM safety**: `.raw()`, `.extra()`, and `RawSQL()` with string-formatted user input — are
  all values passed via `params=`? `QuerySet.filter()` used where `.get()` would raise
  `DoesNotExist` unhandled; `.get_or_create()` race condition under concurrent requests;
  `bulk_create()` / `bulk_update()` bypassing `save()` signals and validators — are those
  signals load-bearing? missing `select_for_update()` on rows that must not be double-spent
- **N+1 queries**: `select_related()` / `prefetch_related()` absent on foreign keys accessed
  in loops or templates; serializers iterating over querysets without prefetch; Django admin
  list views with callable fields hitting the DB per row
- **Auth and permissions**: view missing `@login_required` or `LoginRequiredMixin`; class-based
  view `get_queryset()` not filtering by `request.user` — any authenticated user can request
  any object by ID; object-level permission check (`has_object_permission`, `django-guardian`)
  absent where row-level isolation is required; `request.user.is_staff` used as an
  authorization check without also checking `is_active`
- **CSRF**: `@csrf_exempt` on a state-changing view; AJAX requests not sending
  `X-CSRFToken`; `CsrfViewMiddleware` removed from `MIDDLEWARE`; cookie flags —
  `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE` not set
- **Redirect safety**: `next` parameter in login/logout redirects accepted without validating
  the host — open redirect to attacker-controlled URL; `redirect(request.GET.get('next'))`
  without `url_has_allowed_host_and_scheme()` check
- **Template XSS**: `{{ var|safe }}` suppresses autoescaping — is the value actually safe?
  `mark_safe()` called on any string derived from user input or external data; custom template
  tags that return unescaped HTML; `Template(user_input)` — Django template injection gives
  arbitrary attribute access on context objects
- **File upload**: `FileField` / `ImageField` with no content-type or extension validation;
  upload path containing user-controlled segments (path traversal); no file size limit before
  writing; uploaded files served from a path under `MEDIA_URL` without access control
- **Settings hardening**: `DEBUG = True` shipped to production (leaks full tracebacks and SQL
  queries); `ALLOWED_HOSTS = ['*']` or empty in production; `SECRET_KEY` hardcoded in
  `settings.py` or committed to git; `SecurityMiddleware` not first in `MIDDLEWARE` (HTTPS
  redirect and HSTS won't apply); `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`,
  `SECURE_BROWSER_XSS_FILTER` not set; `CORS_ALLOW_ALL_ORIGINS = True` with credentials
- **Django REST Framework** (if `rest_framework` is installed): `permission_classes` not set
  or set to `AllowAny` on a view that mutates data; `DEFAULT_PERMISSION_CLASSES` in settings
  too permissive for the API surface; serializer missing `read_only_fields` on fields the
  caller must not write (e.g., `owner`, `created_at`, `is_staff`); `ModelSerializer` with
  `fields = '__all__'` — exposes internal fields; `throttle_classes` absent on
  unauthenticated endpoints; `validated_data` bypassed — logic reading from `request.data`
  directly after a failed `is_valid()` check
- **Signals and middleware**: `post_save` signal handler calling `.save()` without
  `update_fields` — triggers infinite signal loop; signal handler that raises silently
  (Django swallows signal exceptions by default); custom middleware mutating `request` in
  a way that breaks downstream middleware ordering assumptions
- **Mass assignment**: `ModelForm` without an explicit `fields` list or `exclude` — a
  caller can POST any field name and overwrite sensitive model attributes (`is_staff`,
  `owner_id`, `subscription_tier`); `ModelForm(request.POST, instance=obj)` without
  restricting which fields can change is particularly dangerous for update endpoints
- **Django admin exposure**: admin panel at the default `/admin/` URL with no IP
  allowlist, no MFA, and no custom URL slug; `ModelAdmin.list_display` with callables or
  related model accessors hitting the DB once per row (N+1 on every admin list page);
  `raw_id_fields` or `autocomplete_fields` returning objects owned by other users
- **URL parameter injection**: `request.GET.get('order')` passed directly to
  `.order_by()` — attacker names any column, enabling information disclosure via error
  messages or query timing differences; `request.GET` values interpolated into queryset
  filters or template context without sanitization
- **Session security**: session fixation — `request.session.cycle_key()` not called after
  successful login, allowing a pre-login session ID set by an attacker to be reused
  post-login; Django sessions pickled by default — a compromised session store combined
  with a known `SECRET_KEY` gives RCE via pickle deserialization on session load
- **Celery / async task security**: task `kwargs` containing PII or credentials logged by
  Celery workers and visible in log aggregation tools; task results stored in Redis or DB
  without TTL accumulate indefinitely and may contain sensitive data; no rate limiting on
  task dispatch — a single user action triggers unbounded task fan-out; task arguments
  visible in Flower, Celery Beat logs, or monitoring UIs without access control
