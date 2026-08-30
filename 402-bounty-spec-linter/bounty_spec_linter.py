#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, urllib.parse, urllib.request
from dataclasses import dataclass, asdict

DEFAULT_REPO = "Scottcjn/rustchain-bounties"
DEFAULT_AGENT_URL = "https://raw.githubusercontent.com/Scottcjn/rustchain-bounties/main/agent.json"
RANGE_RE = re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*RTC\b")
EXACT_RE = re.compile(r"(?i)\b(?:reward|payout|amount)\s*[:=-]\s*(\d+(?:\.\d+)?)\s*RTC\b")
ANY_RE = re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*RTC\b")

@dataclass(frozen=True)
class Reward:
    minimum: float
    maximum: float
    source: str
    def display(self):
        def f(x): return str(int(x)) if float(x).is_integer() else str(x)
        return f(self.minimum) if self.minimum == self.maximum else f"{f(self.minimum)}-{f(self.maximum)}"

@dataclass
class Finding:
    code: str
    severity: str
    message: str
    evidence: dict

def reward_from_text(text, source):
    if not text: return None
    m = RANGE_RE.search(text)
    if m:
        a,b = map(float,m.groups())
        return Reward(min(a,b),max(a,b),source)
    for pat in (EXACT_RE, ANY_RE):
        m = pat.search(text)
        if m:
            v=float(m.group(1)); return Reward(v,v,source)
    return None

def featured_reward(entry):
    if "payout_rtc" in entry:
        v=float(entry["payout_rtc"]); return Reward(v,v,"agent.json")
    if "payout_rtc_min" in entry or "payout_rtc_max" in entry:
        a=float(entry.get("payout_rtc_min",entry.get("payout_rtc_max")))
        b=float(entry.get("payout_rtc_max",entry.get("payout_rtc_min")))
        return Reward(min(a,b),max(a,b),"agent.json")
    return None

def same(a,b):
    return a.minimum==b.minimum and a.maximum==b.maximum

def labels(issue):
    out=[]
    for x in issue.get("labels",[]):
        out.append(x if isinstance(x,str) else x.get("name",""))
    return out

def lint_issue(issue, manifest=None):
    fs=[]; title=issue.get("title",""); body=issue.get("body",""); n=issue.get("number")
    tr=reward_from_text(title,"title"); br=reward_from_text(body,"body")
    if "bounty" not in {x.lower() for x in labels(issue)}:
        fs.append(Finding("MISSING_BOUNTY_LABEL","warning","Issue lacks `bounty` label.",{"issue":n}))
    if tr is None and br is None:
        fs.append(Finding("MISSING_REWARD","error","No RTC reward parsed from title or body.",{"issue":n}))
    if tr and br and not same(tr,br):
        fs.append(Finding("TITLE_BODY_REWARD_DRIFT","error",f"Title says {tr.display()} RTC while body says {br.display()} RTC.",{"issue":n,"title_reward_rtc":tr.display(),"body_reward_rtc":br.display()}))
    if issue.get("state")=="closed" and "open" in body.lower()[:600]:
        fs.append(Finding("STATE_TEXT_DRIFT","warning","Issue is closed but early body text still says open.",{"issue":n}))
    if manifest and n is not None:
        entries={int(x["id"]):x for x in manifest.get("featured_bounties",[]) if str(x.get("id","")).isdigit()}
        e=entries.get(int(n))
        if e:
            mr=featured_reward(e); ir=br or tr
            if mr and ir and not same(mr,ir):
                fs.append(Finding("AGENT_MANIFEST_REWARD_DRIFT","error",f"Issue says {ir.display()} RTC while agent.json says {mr.display()} RTC.",{"issue":n,"issue_reward_rtc":ir.display(),"agent_reward_rtc":mr.display()}))
    return fs

def get_json(url):
    req=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","User-Agent":"rustchain-bounty-spec-linter/0.1"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read().decode())

def load(path):
    with open(path,encoding="utf-8") as f: return json.load(f)

def report(issue, fs):
    return {"issue":issue.get("number"),"title":issue.get("title"),"state":issue.get("state"),"url":issue.get("html_url"),"findings":[asdict(f) for f in fs],"finding_count":len(fs),"error_count":sum(f.severity=="error" for f in fs)}

def main():
    p=argparse.ArgumentParser(description="Lint RustChain bounty specs and detect reward drift.")
    p.add_argument("--repo",default=DEFAULT_REPO); p.add_argument("--agent-json"); p.add_argument("--format",choices=("human","json"),default="human")
    sub=p.add_subparsers(dest="cmd",required=True)
    i=sub.add_parser("issue"); i.add_argument("number",type=int); i.add_argument("--issue-json")
    s=sub.add_parser("scan"); s.add_argument("--limit",type=int,default=100)
    a=p.parse_args()
    manifest=load(a.agent_json) if a.agent_json else get_json(DEFAULT_AGENT_URL)
    if a.cmd=="issue":
        issue=load(a.issue_json) if a.issue_json else get_json(f"https://api.github.com/repos/{a.repo}/issues/{a.number}")
        reps=[report(issue,lint_issue(issue,manifest))]
    else:
        q=urllib.parse.urlencode({"state":"open","labels":"bounty","per_page":min(max(a.limit,1),100)})
        issues=[x for x in get_json(f"https://api.github.com/repos/{a.repo}/issues?{q}") if "pull_request" not in x][:a.limit]
        reps=[report(x,lint_issue(x,manifest)) for x in issues]
        reps.sort(key=lambda r:r["error_count"],reverse=True)
    if a.format=="json": print(json.dumps(reps[0] if a.cmd=="issue" else reps,indent=2))
    else:
        for r in reps:
            if r["finding_count"]:
                print(f"#{r['issue']} {r['title']}")
                for f in r["findings"]: print(f"[{f['severity'].upper()}] {f['code']}: {f['message']}")
                print()
    return 2 if any(r["error_count"] for r in reps) else 0

if __name__=="__main__":
    raise SystemExit(main())
