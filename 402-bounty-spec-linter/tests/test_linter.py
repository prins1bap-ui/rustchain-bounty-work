import unittest
from bounty_spec_linter import lint_issue, reward_from_text, featured_reward

class Tests(unittest.TestCase):
    def test_exact(self):
        r=reward_from_text("[BOUNTY] X (25 RTC)","title")
        self.assertEqual((r.minimum,r.maximum),(25,25))
    def test_range(self):
        r=reward_from_text("Reward: 10-25 RTC","body")
        self.assertEqual((r.minimum,r.maximum),(10,25))
    def test_title_body_drift(self):
        issue={"number":13226,"title":"[BOUNTY] GEO (7 RTC)","body":"Reward: 10 RTC","state":"open","labels":[{"name":"bounty"}]}
        self.assertIn("TITLE_BODY_REWARD_DRIFT",{f.code for f in lint_issue(issue)})
    def test_clean(self):
        issue={"number":9,"title":"[BOUNTY] Docs (5 RTC)","body":"Reward: 5 RTC","state":"open","labels":[{"name":"bounty"}]}
        self.assertEqual(lint_issue(issue),[])
    def test_missing(self):
        issue={"number":10,"title":"Do work","body":"No payment","state":"open","labels":[]}
        self.assertEqual({f.code for f in lint_issue(issue)},{"MISSING_BOUNTY_LABEL","MISSING_REWARD"})
    def test_manifest_drift(self):
        issue={"number":2864,"title":"[BOUNTY] Action (25 RTC)","body":"Reward: 25 RTC","state":"open","labels":[{"name":"bounty"}]}
        m={"featured_bounties":[{"id":2864,"payout_rtc":20}]}
        self.assertIn("AGENT_MANIFEST_REWARD_DRIFT",{f.code for f in lint_issue(issue,m)})
    def test_manifest_range(self):
        r=featured_reward({"payout_rtc_min":10,"payout_rtc_max":30})
        self.assertEqual((r.minimum,r.maximum),(10,30))

if __name__=="__main__": unittest.main()
