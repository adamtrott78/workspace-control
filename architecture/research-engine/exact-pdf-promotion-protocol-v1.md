# Exact-PDF Promotion Protocol v1

Status: ACTIVE VERTICAL-SLICE PROCEDURE
Created: 2026-09-30

## Purpose

Promote selected PADataset reference papers from `OCR_DERIVED` analysis state to
exact-PDF-verified research-engine source artifacts without modifying PADataset.

This procedure validates the fidelity boundary between:

- the tracked Mathpix MMD already used for semantic cross-paper tests; and
- the exact local PDF bytes from which the analysis package was produced.

## Selected promotion set

1. `2013_scheirer_toward_open_set_recognition.pdf`
2. `2020_liu_energy_ood_detection.pdf`
3. `2024_baye_varmax_milcom.pdf`

Manifest-recorded root:

`/home/atrott/adamArchives/Adam/varMax/PADataset/papers/milcom2026/reference_notes/papers`

## Safety

This procedure is read-only with respect to PADataset.

It MUST NOT:

- switch branches;
- stage files;
- modify PDFs;
- move source PDFs;
- clean/reset/stash the repository;
- regenerate Mathpix packages.

It copies exact bytes into a temporary bundle only.

## Required receipt per PDF

Record:

- absolute source path;
- byte length;
- SHA-256;
- first five bytes / PDF magic;
- page count from `pdfinfo`.

The bundle must contain:

- the three exact PDF copies;
- `receipt.tsv`;
- `SHA256SUMS`.

## Noninteractive local command

Run:

```bash
set -euo pipefail

ROOT="/home/atrott/adamArchives/Adam/varMax/PADataset/papers/milcom2026/reference_notes/papers"
SCRATCH_ROOT="${WORKSPACE_CONTROL_SCRATCH_ROOT:-$HOME/adamArchives/Adam/.workspace-control/tmp}"
mkdir -p "$SCRATCH_ROOT"
OUT="$(mktemp -d "$SCRATCH_ROOT/research-engine-pdf-promotion.XXXXXX")"
BUNDLE="$SCRATCH_ROOT/research-engine-pdf-promotion.tar.gz"

declare -a RELS=(
  "2013_scheirer_toward_open_set_recognition/2013_scheirer_toward_open_set_recognition.pdf"
  "2020_liu_energy_ood_detection/2020_liu_energy_ood_detection.pdf"
  "2024_baye_varmax_milcom/2024_baye_varmax_milcom.pdf"
)

printf 'slug\tsource_path\tbytes\tsha256\tpdf_magic\tpages\n' > "$OUT/receipt.tsv"

for rel in "${RELS[@]}"; do
  src="$ROOT/$rel"
  test -f "$src"

  slug="$(basename "$src" .pdf)"
  dst="$OUT/$slug.pdf"
  cp --preserve=mode,timestamps "$src" "$dst"

  bytes="$(wc -c < "$dst")"
  sha="$(sha256sum "$dst" | awk '{print $1}')"
  magic="$(head -c 5 "$dst")"
  pages="$(pdfinfo "$dst" | awk -F: '/^Pages:/ {gsub(/[[:space:]]/,"",$2); print $2}')"

  test "$magic" = "%PDF-"
  test -n "$pages"

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$slug" "$src" "$bytes" "$sha" "$magic" "$pages" >> "$OUT/receipt.tsv"
done

(
  cd "$OUT"
  sha256sum ./*.pdf > SHA256SUMS
)

tar -C "$OUT" -czf "$BUNDLE" .

echo "RESEARCH_ENGINE_PDF_PROMOTION_RESULT=PASS"
echo "BUNDLE=$BUNDLE"
echo "BUNDLE_BYTES=$(wc -c < "$BUNDLE")"
echo "BUNDLE_SHA256=$(sha256sum "$BUNDLE" | awk '{print $1}')"
echo
cat "$OUT/receipt.tsv"
```

## Acceptance

The local promotion step passes only when:

- all three manifest-recorded PDFs exist;
- each copied file begins with `%PDF-`;
- page counts equal the existing manifests:
  - Scheirer: 16
  - Liu: 16
  - Baye: 6
- SHA-256 is recorded for every exact PDF;
- `SHA256SUMS` matches the bundled copies;
- the source repository remains untouched.

## Extraction-executor follow-up

After upload of the bundle:

1. verify tar SHA-256 when supplied;
2. extract into an isolated temporary directory;
3. verify `SHA256SUMS`;
4. verify page counts/magic;
5. register three exact `SourceArtifact` identities;
6. parse exact PDF text/layout;
7. compare the existing OCR-derived evidence anchors with exact-PDF text;
8. classify each anchor:
   - EXACT_MATCH;
   - NORMALIZATION_ONLY;
   - OCR_MINOR_ERROR;
   - OCR_SEMANTIC_ERROR;
   - LOCATOR_UNRESOLVED;
9. do not overwrite OCR history;
10. promote evidence to exact-PDF-backed state only where source verification
    passes.

## Vertical-slice success criterion

The promotion test succeeds when the engine can quantify the fidelity of its
existing OCR-derived semantic corpus against exact source PDFs and carry that
verification state into cross-paper synthesis.
