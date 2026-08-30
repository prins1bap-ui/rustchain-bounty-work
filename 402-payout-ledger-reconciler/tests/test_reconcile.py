import unittest
from reconcile import parse_ledger,audit

HEADER='''| Date (UTC) | Bounty Ref | GitHub User | Wallet | Amount RTC | Status | Pending ID | Tx Hash | Notes |\n|---|---|---|---|---:|---|---:|---|---|'''

class TestLedger(unittest.TestCase):
    def test_parse(self):
        md=HEADER+'\n| 2026-08-30 | #402 | @alice | `RTCa` | 50 | Pending | 99 | `abc` | ok |'
        e=parse_ledger(md); self.assertEqual(len(e),1); self.assertEqual(e[0].amount_rtc,50)
    def test_missing_pending(self):
        md=HEADER+'\n| 2026-08-30 | #402 | @alice | `RTCa` | 50 | Pending |  |  | missing |'
        kinds=[x['kind'] for x in audit(parse_ledger(md))['findings']]; self.assertIn('missing_pending_id',kinds)
    def test_confirmed_missing_tx(self):
        md=HEADER+'\n| 2026-08-30 | #402 | @alice | `RTCa` | 50 | Confirmed | 99 |  | missing |'
        kinds=[x['kind'] for x in audit(parse_ledger(md))['findings']]; self.assertIn('missing_tx_hash',kinds)
    def test_collision(self):
        md=HEADER+'\n| 2026-08-30 | #1 | @a | `RTCa` | 5 | Pending | 99 | a | x |\n| 2026-08-30 | #2 | @b | `RTCb` | 7 | Pending | 99 | b | y |'
        kinds=[x['kind'] for x in audit(parse_ledger(md))['findings']]; self.assertIn('pending_id_collision',kinds)
    def test_totals(self):
        md=HEADER+'\n| 2026-08-30 | #1 | @a | `RTCa` | 5 | Queued |  |  | x |\n| 2026-08-30 | #2 | @b | `RTCb` | 7 | Queued |  |  | y |'
        self.assertEqual(audit(parse_ledger(md))['totals_rtc_by_status']['Queued'],12)

if __name__=='__main__': unittest.main()
