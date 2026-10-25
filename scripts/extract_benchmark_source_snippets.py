#!/usr/bin/env python3
from __future__ import annotations
import hashlib, io, json, re, time, urllib.request
from pathlib import Path
from pypdf import PdfReader

CORPUS=Path("architecture/extract-semantic-benchmark-corpus.v0.1.json")
MANIFEST=Path("architecture/extract-semantic-benchmark-source-manifest.v0.1.json")
QUERIES=Path("architecture/extract-semantic-benchmark-annotation-queries.v0.1.json")
OUT=Path("architecture/extract-semantic-benchmark-annotation-snippets.v0.1.json")
UA="workspace-control-extract-semantic-benchmark/0.1 (+https://github.com/adamtrott78/workspace-control)"

def fetch(url):
    last=None
    for i in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=60) as r: data=r.read()
            if not data.startswith(b"%PDF"): raise RuntimeError("not PDF")
            return data
        except Exception as e:
            last=e
            if i<3: time.sleep(2**i)
    raise RuntimeError(last)

def clean(text):
    text="".join("\uFFFD" if 0xD800<=ord(ch)<=0xDFFF else ch for ch in text)
    text=text.replace("\r\n","\n").replace("\r","\n").replace("\u00ad","")
    text=re.sub(r"[ \t]+"," ",text)
    text=re.sub(r"\n[ \t]+","\n",text)
    text=re.sub(r"[ \t]+\n","\n",text)
    text=re.sub(r"\n{3,}","\n\n",text)
    return text.strip()+"\n"

def locator(text):
    text=text.lower().replace("–","-").replace("—","-").replace("’","'").replace("“",'"').replace("”",'"')
    text=re.sub(r"-\n(?=[a-z])","",text)
    text=re.sub(r"\s+"," ",text)
    return text

def main():
    corpus=json.loads(CORPUS.read_text())
    mani=json.loads(MANIFEST.read_text())
    qs=json.loads(QUERIES.read_text())["papers"]
    mp={p["benchmark_paper_id"]:p for p in mani["papers"]}
    cp={p["benchmark_paper_id"]:p for p in corpus["acceptance_papers"]}
    out={"schema_version":1,"benchmark_id":mani["benchmark_id"],"status":"SOURCE_ONLY_SNIPPETS","papers":[]}
    for pid, patterns in qs.items():
        meta=mp[pid]; c=cp[pid]
        blob=fetch(c["source_pdf_url"])
        assert hashlib.sha256(blob).hexdigest()==meta["source_pdf_sha256"]
        reader=PdfReader(io.BytesIO(blob))
        pages=[clean(p.extract_text() or "") for p in reader.pages]
        paper={"benchmark_paper_id":pid,"source_pdf_sha256":meta["source_pdf_sha256"],"matches":[]}
        for pat in patterns:
            normpat=locator(pat)
            found=[]
            for pno,text in enumerate(pages,1):
                lt=locator(text)
                pos=lt.find(normpat)
                if pos>=0:
                    # Locator-normalized offsets are not canonical offsets; context is navigation only.
                    a=max(0,pos-360); b=min(len(lt),pos+len(normpat)+560)
                    found.append({"page_number":pno,"context":lt[a:b],"query":pat})
                    if len(found)>=3: break
            paper["matches"].append({"query":pat,"hits":found})
        out["papers"].append(paper)
    OUT.write_text(json.dumps(out,indent=2)+"\n")
    print("=== BENCHMARK_ANNOTATION_SNIPPETS_BEGIN ===")
    print(json.dumps(out,sort_keys=True))
    print("=== BENCHMARK_ANNOTATION_SNIPPETS_END ===")

if __name__=="__main__": main()
