# 9:16 capture plan

Target canvas: **1080×1920 vertical**. Keep all important text inside the center 80% safe area.

## Shot 1 — Hook (0:00–0:06)

Capture the public GitHub page for `rustchain-bounties` issue #13226. Zoom tightly enough that the title is readable:

`[BOUNTY: 7 RTC] Add an llms.txt + GEO entity profile to a RustChain ecosystem repo`

Overlay large text: **“7 RTC?”**

Then scroll just enough to expose the first body heading containing **10 RTC**. Add a second overlay: **“...or 10 RTC?”**

Do not imply either amount has been paid.

## Shot 2 — Show the mismatch (0:06–0:14)

Use a split or rapid cut:
- upper card: title snippet with `7 RTC`
- lower card: body snippet with `10 RTC`

On-screen caption: **“Same live bounty. Two reward figures.”**

## Shot 3 — Run the linter (0:14–0:29)

Record a terminal in the public `402-bounty-spec-linter` directory. Run:

```text
python bounty_spec_linter.py issue 13226
```

Frame the resulting `TITLE_BODY_REWARD_DRIFT` finding. If live network access is unavailable during capture, use the repository’s documented offline fixture command instead and label the shot **“offline regression fixture reproducing #13226”**. Never fake a live fetch.

## Shot 4 — What it checks (0:29–0:43)

Show the project README and animate four concise cards:

1. **Title ↔ body reward drift**
2. **Issue ↔ agent.json drift**
3. **Missing reward / bounty label**
4. **Stale issue-state wording**

Keep the source README visible behind the cards so the claims are traceable on screen.

## Shot 5 — Human stays in control (0:43–0:52)

Show the README safety section:

`Public GET requests only. No comments, edits, wallet actions, transfers, signatures, payments, or security testing.`

Overlay: **“Detect. Report. Human decides.”**

## Shot 6 — End card (0:52–0:58)

Plain vertical end card:

**Make the spec agree before contributors have to guess.**

Small footer:
`RustChain community tooling • @prins1bap-ui`

No music is required. If Elyan Labs adds music, use only properly licensed or owned audio.
