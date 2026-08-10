# Re-audit vs. prompt assumptions (verified against HEAD 7162e9b)

Checked before writing any code. Several "gaps" in the task description are already
closed in the current code — acting on the actual code, as instructed.

## Prompt 1 — Outbox
| Claim in prompt | Reality at HEAD |
|---|---|
| `mark_published/mark_retry/mark_failed` dead code | **Gone.** `OutboxMessage` no longer has them. Model is write-only + retention. |
| `OUTBOX_PENDING_MESSAGES`/`OUTBOX_FAILED_MESSAGES` misleading | **Gone.** `metrics.py` now only has `OUTBOX_EVENTS_WRITTEN` + `OUTBOX_CLEANUP_DELETED`. |
| No cleanup job | **Exists.** `app/core/outbox/task.py::OutboxCleanupTask`, registered in `app/core/tasks.py::register_tasks`, cron from `OUTBOX_CLEANUP_INTERVAL_SECONDS`. |
| No replication-slot alerting | **Exists.** `monitoring/prometheus/alerts.yml` has 4 rules for `outbox_slot` (inactive/lag 512MiB/lag 4GiB/WAL size); `postgres-exporter` runs with `--collector.replication_slot --collector.wal`. |
| Direct Kafka publishes bypassing outbox | **None found.** `send_event`/`send_data` only defined in the broker ABC + Kafka impl, never called from module code. |

=> Variant A (retention-based cleanup) is already the implemented choice. **Remaining: no tests at all** for outbox
(`grep -rl outbox tests/` = empty) and the design choice is undocumented.

## Prompt 2 — Profile projection
Fully implemented as described (model, consumer, idempotency guard, `source_updated_at` guard, backfill task
registered in `register_chat_tasks`). **Remaining:** zero contract tests, no deletion decision, no ADR.

## Prompt 3 — Projection in responses
- REST: done (`_message_load_options()` eager-loads `Message.profile` + reply_to/forwarded_from profiles).
- WS `ws.history`: **parity is actually fine** — `subscribe.py`/`resume.py` call
  `message_repository.get_chat_messages_after_seq()`, which uses the *same* `_message_load_options()`,
  then `message_service.attach_download_urls()` which resolves avatar URLs. Prompt's suspicion was wrong.
- Push events: still thin (variant A). Choosing **variant B** for `new_message`.
- `api-docs.md`: `profile` field genuinely undocumented. Real doc/code divergence.

## Prompt 4 — Voice / video notes
| Claim | Reality |
|---|---|
| VOICE/VIDEO_NOTE skip `file_size` check | **Fixed already.** `MAX_VOICE_SIZE`/`MAX_VIDEO_NOTE_SIZE` enforced in `request_upload.py`. |
| Not counted toward per-message limits | **Fixed already.** `exclusive_count` in both `request_upload.py` and `Message.validate_attachments()`. |
| No "exactly one, not mixed" rule | **Fixed already.** Enforced in `validate_attachments()` incl. `message_type` match. |
| No duration limit | **REAL GAP.** `MAX_VOICE_DURATION_SECONDS`, `MAX_VIDEO_NOTE_DURATION_SECONDS`, `MAX_VIDEO_NOTE_RESOLUTION_PX` exist in config with **0 usages** outside config.py. `set_duration()`/`set_resolution()` are never called by app code either. |
| Docs missing | **REAL GAP.** 0 occurrences of "voice" in api-docs.md. |

## Prompt 5 — Reactions
| Claim | Reality |
|---|---|
| `reaction_updated` not mapped to a WS type | **CONFIRMED GAP.** Absent from `WSEventType` and `CHAT_EVENT_TO_WS_TYPE`. |
| No fan-out debounce | **CONFIRMED GAP.** |
| TOCTOU on `MAX_REACTIONS_PER_MESSAGE` | **CONFIRMED.** check-then-insert with no lock in `SetReactionCommandHandler`. |
| Docs missing | **CONFIRMED.** 0 occurrences of "reaction" in api-docs.md. |
| Hot-row counter | Real, but prompt forbids changing architecture without load-test data. |

## Environment limits
- Sandbox has **no Docker** and no root → testcontainers-backed integration/e2e tests **cannot be executed here**.
  Unit tests run against a real Python 3.14.7 venv with the project's full dependency set.

