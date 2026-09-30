# Course bootstrap and migration procedure

## Purpose

Integrate a course repository with shared repository-backed tutoring/workflow
mechanics while preserving project-local authority and valid existing state.

## Required inputs

Recover the exact target repository/checkpoint, root route, current shared pin if
any, local semantic owners, authorized mutation scope, and intended exact new
workspace-control checkpoint. Do not infer these from chat memory.

## Procedure

1. **Inspect exact target state.** Establish repository/ref/checkpoint and
   mutation boundary using the shared operator workflow.
2. **Recover existing local semantics.** Start at the project root and preserve
   working course/source/tutoring/mastery/artifact owners.
3. **Map missing adapter roles.** Use `templates/COURSE_TUTOR_ADAPTER.md` as a
   checklist, not boilerplate to copy.
4. **Bind compatibility explicitly.** Record the exact shared checkpoint through
   the project's local compatibility mechanism; never silently follow moving
   `main`.
5. **Validate cold start.** A fresh executor must recover representative owners
   from the root without prior chat or recursive inventory. Use
   `procedures/TUTOR_EVALUATION.md` when tutoring is in scope.
6. **Checkpoint migration.** Validate changed scope, commit/push under the child
   task's authority, verify advertised identity, and reread pushed state.

Remove builder/tutor conversational-role dependencies only when the target
project actually has them and a durable owner replaces them.

## Gates

Suspend only at a demonstrated capability, irreducible-input, authority/safety,
or explicitly required human-judgment boundary. A plan, commit, or completed
substage is not itself a stop point.
