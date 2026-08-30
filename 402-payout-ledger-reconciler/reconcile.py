from __future__ import annotations
import argparse, json, re, urllib.request
from dataclasses import dataclass, asdict
from typing import Iterable

ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+)\|\s*@?([^|]+)\|\s*`?([^|`]+)`?\s*\|\s*([0-9.]+)\s*\|\s*([^|]+)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|$")

@dataclass
class Entry:
    date: str; bounty_ref: str; user: str; wallet: str; amount_rtc: float
    status: str; pending_id: str; tx_hash: str; notes: str

def parse_ledger(markdown: str) -> list[Entry]:
    out=[]
    for line in markdown.splitlines():
        m=ROW_RE.match(line.strip())
        if not m: continue
        date,bref,user,wallet,amt,status,pid,tx,notes=[x.strip() for x in m.groups()]
        out.append(Entry(date,bref,user,wallet,float(amt),status,pid.strip('` '),tx.strip('` '),notes))
    return out

def audit(entries: Iterable[Entry]) -> dict:
    entries=list(entries); findings=[]; seen_pending={}; seen_tx={}
    for e in entries:
        s=e.status.lower()
        if s in {'pending','confirmed'} and not e.pending_id:
            findings.append({'kind':'missing_pending_id','entry':asdict(e)})
        if s == 'confirmed' and not e.tx_hash:
            findings.append({'kind':'missing_tx_hash','entry':asdict(e)})
        if e.pending_id:
            if e.pending_id in seen_pending and seen_pending[e.pending_id] != (e.wallet,e.amount_rtc):
                findings.append({'kind':'pending_id_collision','pending_id':e.pending_id,'entries':[seen_pending[e.pending_id],(e.wallet,e.amount_rtc)]})
            seen_pending[e.pending_id]=(e.wallet,e.amount_rtc)
        if e.tx_hash:
            if e.tx_hash in seen_tx and seen_tx[e.tx_hash] != (e.wallet,e.amount_rtc):
                findings.append({'kind':'tx_hash_collision','tx_hash':e.tx_hash,'entries':[seen_tx[e.tx_hash],(e.wallet,e.amount_rtc)]})
            seen_tx[e.tx_hash]=(e.wallet,e.amount_rtc)
    totals={}
    for e in entries: totals[e.status]=round(totals.get(e.status,0)+e.amount_rtc,8)
    return {'entries':len(entries),'totals_rtc_by_status':totals,'findings':findings}

def fetch_text(url: str) -> str:
    req=urllib.request.Request(url,headers={'User-Agent':'rustchain-ledger-reconciler/0.1'})
    with urllib.request.urlopen(req, timeout=20) as r: return r.read().decode('utf-8')

def main():
    p=argparse.ArgumentParser(description='Read-only RustChain payout-ledger reconciler')
    p.add_argument('source', help='local markdown file or https URL'); p.add_argument('--json', action='store_true'); a=p.parse_args()
    text=fetch_text(a.source) if a.source.startswith('http') else open(a.source,encoding='utf-8').read()
    report=audit(parse_ledger(text))
    if a.json: print(json.dumps(report,indent=2,sort_keys=True))
    else:
        print(f"entries: {report['entries']}")
        for k,v in sorted(report['totals_rtc_by_status'].items()): print(f"{k}: {v} RTC")
        print(f"findings: {len(report['findings'])}")
        for f in report['findings']: print('-',f['kind'])
if __name__=='__main__': main()
