# ADR-5 Transactional outbox and a MailSender port

Status: proposed (S5, 2026-10-28)

## Context
Each message is sent once per event, retried 3 times over 1 hour, logged, and never blocks or undoes a booking (R46, AC13.6, AC13.7). The base lists TTCommon EMAIL* tables but specifies no mail service (Q53 open in substance).

## Options
1. Send in the request or job thread directly - a mail outage slows or fails bookings; duplicates on retry.
2. `@Async` send after commit - lost on crash, no retry history.
3. Outbox table written in the same transaction as the state change (unique event key), sent by a dispatch job through a `MailSender` port.

## Decision
Option 3. `notification` listens to booking events BEFORE_COMMIT and inserts `ntf_notifications` rows (type, event key unique per tenant, recipient employee id, payload ids, status PENDING/SENT/FAILED, attempts, next attempt). `NotificationDispatchJob` resolves the email from `people` at send time, renders the template from `messages.properties` and sends through `MailSender`. Retries at +20, +40, +60 minutes, then FAILED with `addError`. The adapter is TTCommon mail if it exists, else Spring Mail over a BTP destination (new dependency, Q64). The sender must accept at least 300 mails a minute (PF-5; the product owner confirms the number at G3), proven in load test T5. Dispatch sends in priority order (reminders by deadline, then release mails, then the rest) at the configured rate `DESKBOOK_MAIL_MAX_PER_MINUTE`; with a slower sender the reminder job starts earlier (05-architecture 6.5).

## Consequences
- Exactly once per event key, survives outages, gives the admin a log (R1 page).
- One more table with high write volume; purge SENT rows after 90 days (data-architect).
- The mail adapter choice is open and blocks NT-1 until answered. A personal or shared mailbox (about 30 a minute) does not qualify; with such a sender the fallback moves reminders earlier and delays release mails.
