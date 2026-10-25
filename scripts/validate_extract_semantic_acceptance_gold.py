#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import urllib.request
from pathlib import Path

from jsonschema import Draft202012Validator
from pypdf import PdfReader

ROOT=Path(".")
SCHEMA=json.loads((ROOT/"schemas/extract_semantic_benchmark.v0.1.schema.json").read_text())
GOLD_DIR=ROOT/"architecture/sealed/extract-semantic-acceptance"
OUT=ROOT/"architecture/sealed/extract-semantic-acceptance-validation.v0.1.json"
UA="workspace-control-extract-semantic-benchmark/0.1 (+https://github.com/adamtrott78/workspace-control)"

def fetch(url: str) -> bytes:
    last=None
    for i in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=60) as r: data=r.read()
            if not data.startswith(b"%PDF"): raise RuntimeError("non-PDF response")
            return data
        except Exception as exc:
            last=exc
            if i<3: time.sleep(2**i)
    raise RuntimeError(last)

def clean(text: str) -> str:
    text="".join("\uFFFD" if 0xD800<=ord(ch)<=0xDFFF else ch for ch in text)
    text=text.replace("\r\n","\n").replace("\r","\n").replace("\u00ad","")
    text=re.sub(r"[ \t]+"," ",text)
    text=re.sub(r"\n[ \t]+","\n",text)
    text=re.sub(r"[ \t]+\n","\n",text)
    text=re.sub(r"\n{3,}","\n\n",text)
    return text.strip()+"\n"

def loc(text: str) -> str:
    text=text.lower().replace("–","-").replace("—","-").replace("’","'").replace("“",'"').replace("”",'"')
    text=re.sub(r"-\n(?=[a-z])","",text)
    return re.sub(r"\s+"," ",text)

def validate_doc(path: Path) -> dict:
    doc=json.loads(path.read_text())
    Draft202012Validator(SCHEMA).validate(doc)
    pdf=fetch(doc["paper"]["source_pdf_url"])
    got=hashlib.sha256(pdf).hexdigest()
    assert got==doc["paper"]["source_sha256"], (path,got,doc["paper"]["source_sha256"])
    reader=PdfReader(io.BytesIO(pdf))
    assert len(reader.pages)==doc["paper"]["page_count"]
    pages=[clean(p.extract_text() or "") for p in reader.pages]
    errors=[]
    ids=set()
    for ob in doc["obligations"]:
        if ob["obligation_id"] in ids: errors.append(f"duplicate obligation id {ob['obligation_id']}")
        ids.add(ob["obligation_id"])
        for q in ob["quotes"]:
            pno=q["page_number"]
            page=pages[pno-1]
            matches=[]
            for para in [x.strip() for x in page.split("\n\n") if x.strip()]:
                h=hashlib.sha256(para.encode("utf-8")).hexdigest()
                if h==q["canonical_span_sha256"]: matches.append(para)
            if len(matches)!=1:
                errors.append(f"{ob['obligation_id']}: span hash matches={len(matches)} page={pno}")
                continue
            if loc(q["anchor_excerpt"]) not in loc(matches[0]):
                errors.append(f"{ob['obligation_id']}: anchor absent from hashed span")
    if not doc["annotation_provenance"]["source_first"]: errors.append("source_first false")
    if doc["annotation_provenance"]["extract_outputs_viewed"]: errors.append("extract outputs viewed")
    states={o["adjudication_state"] for o in doc["obligations"]}
    if "PASS_A_ONLY" in states: errors.append("unadjudicated PASS_A_ONLY obligation remains")
    if states & {"REJECT_NOT_IMPORTANT","REJECT_UNSUPPORTED"}:
        errors.append("rejected obligation remains in final gold")
    canonical=json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return {
      "file":str(path),
      "paper_id":doc["paper"]["benchmark_paper_id"],
      "obligation_count":len(doc["obligations"]),
      "core_count":sum(o["importance"]=="CORE" for o in doc["obligations"]),
      "secondary_count":sum(o["importance"]=="SECONDARY" for o in doc["obligations"]),
      "adjudication_states":sorted(states),
      "canonical_json_sha256":hashlib.sha256(canonical).hexdigest(),
      "errors":errors,
    }

def main():
    files=sorted(GOLD_DIR.glob("*.json"))
    assert len(files)==8, len(files)
    results=[validate_doc(p) for p in files]
    all_errors=[e for r in results for e in r["errors"]]
    commitment_material="".join(
        f"{r['paper_id']}:{r['canonical_json_sha256']}\n"
        for r in sorted(results,key=lambda x:x["paper_id"])
    ).encode("utf-8")
    report={
      "schema_version":1,
      "status":"PASS" if not all_errors else "FAIL",
      "paper_count":len(results),
      "obligation_count":sum(r["obligation_count"] for r in results),
      "core_count":sum(r["core_count"] for r in results),
      "secondary_count":sum(r["secondary_count"] for r in results),
      "gold_commitment_sha256":hashlib.sha256(commitment_material).hexdigest(),
      "commitment_definition":"sha256(sorted paper_id:canonical_json_sha256 + LF)",
      "papers":results,
      "errors":all_errors,
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print("=== SEALED_GOLD_VALIDATION_BEGIN ===")
    print(json.dumps(report,sort_keys=True))
    print("=== SEALED_GOLD_VALIDATION_END ===")
    if all_errors: raise SystemExit(1)

if __name__=="__main__": main()
