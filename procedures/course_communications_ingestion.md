# Course communications-ingestion procedure

## Purpose

Normalize relevant course communications into durable project-owned state with
minimal provenance, idempotent re-entry, and explicit return to the parent task.

The communication surface is an evidence adapter, not the permanent owner.

## Procedure

1. **Repository-first lookup.** Check the exact source identity in durable
   project state before rereading an external message.
2. **Retrieve only if needed.** Use an authorized adapter. A user-forwarded Gmail
   copy is valid when school Outlook is inaccessible; do not imply pseudo-real-
   time Outlook connectivity.
3. **Normalize domain facts.** Persist only course-relevant facts plus minimal
   provenance such as source identity, sender/original sender, subject, and time
   when needed.
4. **Persist and verify.** Write through the project owner, validate bounded
   scope, commit/push when authorized, verify the checkpoint, and reread.
5. **Return to parent.** Continue the parent course task from durable project
   state.

Repeated exact source identity should be a no-op when durable state is already
complete. Read/ingest authority does not grant send/reply authority.
