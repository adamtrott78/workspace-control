<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/research-engine-local-document-pipeline-v1.json`

## State
- Task: `research-engine-local-document-pipeline-v1`
- Stage: `residual_escalation_and_local_semantic_fallbacks`
- research-engine remote canonical: `7a26e648ec409c96a3f9b7c8620f566658700894`
- research-engine Lambda/local last verified: `0bded264aa4bb021450b9d62c66555843155ead8` clean
- research daemon: keep inactive/dead PID 0
- sustained research: disabled
- STANDARD Codex authoritative-PDF EXTRACT/VERIFY remains production semantic baseline

## Current PaddleOCR-VL status
The causal-mask-compatible direct Transformers path finally reached **actual
generation**. The model/processor preflight completed successfully and the
runner entered:

`RUN EXACTLY THREE TARGETED VLM INFERENCES VIA DECLARED TRANSFORMERS INTERFACE`

The first call then remained inside generation for more than five minutes.

This is now classified as a benchmark-harness pacing defect, not another setup
failure and not VLM quality evidence.

Reason:
- PaddleOCR-VL-1.6's own generation configuration uses `use_cache=false`;
- the prior harness also used `use_cache=false`, correctly preserving that;
- however, the harness allowed `max_new_tokens=2048`;
- the official direct-Transformers PaddleOCR-VL-1.6 example uses a 512-token
  generation cap.

The long 2048-token run should be interrupted with `Ctrl+C` if it is still
active and discarded as benchmark evidence.

## Bounded generation hotfix
research-engine PR #77 merged as
`7a26e648ec409c96a3f9b7c8620f566658700894`.

- PR-head CI `37237786417`: PASS
- canonical-main CI `37237908217`: PASS

The corrected benchmark:
- keeps the exact same pinned local model and causal-mask compatibility shim;
- keeps `use_cache=false`;
- caps generation at `max_new_tokens=512`;
- emits flushed `VLM_CALL_START` before every generation;
- emits flushed `VLM_CALL_COMPLETE` with elapsed seconds after every
  generation.

No dependency, model file, model weight, prompt, crop, inference count,
quality threshold, resource ceiling, daemon policy, Qwen/Codex boundary,
production routing, or scientific-state behavior changed.

## Next safe action
If the old 2048-token process is still active, interrupt it with `Ctrl+C`.

Keep sustained research disabled and `research-engine-daemon.service`
inactive/dead. Treat remote
`main@7a26e648ec409c96a3f9b7c8620f566658700894` as canonical and Lambda/local
`main@0bded264aa4bb021450b9d62c66555843155ead8` as the last verified clean
state.

On Lambda:
1. require branch `main` and clean checkout;
2. fetch origin and require `origin/main` exactly
   `7a26e648ec409c96a3f9b7c8620f566658700894`;
3. fast-forward only to that commit;
4. rerun `bash deploy/run-paddleocr-vl-residual-benchmark.sh`;
5. return the new `OUTPUT_ROOT` plus
   `paddleocr-vl-benchmark-report.json`, or the first hard error.

The next run should visibly print `VLM_CALL_START` / `VLM_CALL_COMPLETE`
events, so a long model call is no longer silent.

Do not start the daemon, invoke Qwen3.5-4B or Codex, change production routing,
or materialize scientific state.

## Fresh-chat initialization
@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/research-engine-local-document-pipeline-v1.json`

Start from the normal workspace-control root route. Treat the authoritative
capsule, synchronized Markdown handoff, exact Git/runtime state, and referenced
research-engine evidence as the complete handoff. Do not rely on previous chat
state. Follow the capsule's exact `next_safe_action`.
