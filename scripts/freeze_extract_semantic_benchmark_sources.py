#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from pypdf import PdfReader

CORPUS_PATH = Path("architecture/extract-semantic-benchmark-corpus.v0.1.json")
OUT_PATH = Path("architecture/extract-semantic-benchmark-source-manifest.v0.1.json")

USER_AGENT = "workspace-control-extract-semantic-benchmark/0.1 (+https://github.com/adamtrott78/workspace-control)"


def fetch(url: str, attempts: int = 4) -> bytes:
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if not data.startswith(b"%PDF"):
                raise RuntimeError(f"non-PDF payload from {url}: prefix={data[:20]!r}")
            return data
        except Exception as exc:
            last = exc
            if i + 1 < attempts:
                time.sleep(2 ** i)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def canonicalize_page_text(text: str) -> str:
    # pypdf can expose unpaired UTF-16 surrogate code points from malformed
    # ToUnicode maps. Replace those deterministically before UTF-8 hashing.
    text = "".join("\uFFFD" if 0xD800 <= ord(ch) <= 0xDFFF else ch for ch in text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def paper_manifest(paper: dict) -> dict:
    url = paper["source_pdf_url"]
    blob = fetch(url)
    pdf_sha = hashlib.sha256(blob).hexdigest()
    reader = PdfReader(io.BytesIO(blob))
    page_hashes = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        canonical = canonicalize_page_text(text)
        page_hashes.append({
            "page_number": i,
            "canonical_text_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "canonical_text_chars": len(canonical),
        })
    return {
        "benchmark_paper_id": paper["benchmark_paper_id"],
        "split": paper["split"],
        "arxiv_id": paper["arxiv_id"],
        "version": paper["version"],
        "title": paper["title"],
        "source_pdf_url": url,
        "source_pdf_sha256": pdf_sha,
        "source_pdf_bytes": len(blob),
        "page_count": len(reader.pages),
        "page_text_hash_algorithm": "sha256(canonicalized_pypdf_extract_text_utf8)",
        "page_text_canonicalization": "CRLF/CR->LF; collapse horizontal whitespace; trim line-edge whitespace; collapse 3+ newlines to 2; strip; append LF",
        "pages": page_hashes,
    }


def main() -> int:
    corpus = json.loads(CORPUS_PATH.read_text())
    papers = corpus["pilot_papers"] + corpus["acceptance_papers"]
    manifest = {
        "schema_version": 1,
        "benchmark_id": corpus["benchmark_id"],
        "status": "SOURCE_IDENTITIES_FROZEN",
        "source_freeze_tool": {
            "python": sys.version.split()[0],
            "pypdf": __import__("pypdf").__version__,
        },
        "papers": [paper_manifest(p) for p in papers],
    }
    OUT_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print("=== EXTRACT_SEMANTIC_BENCHMARK_SOURCE_MANIFEST_BEGIN ===")
    print(json.dumps(manifest, sort_keys=True))
    print("=== EXTRACT_SEMANTIC_BENCHMARK_SOURCE_MANIFEST_END ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
