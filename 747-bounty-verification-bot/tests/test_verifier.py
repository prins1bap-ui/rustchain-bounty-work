import unittest
from unittest.mock import patch
import verifier

class TestVerifier(unittest.TestCase):
    def test_parse_native_wallet_and_url(self):
        w, u = verifier.parse_claim("Wallet: RTC" + "a"*40 + "\nProof: https://dev.to/x/y")
        self.assertEqual(w, "RTC" + "a"*40)
        self.assertEqual(u, "https://dev.to/x/y")

    def test_parse_miner_id(self):
        w, u = verifier.parse_claim("miner_id: demo-wallet")
        self.assertEqual(w, "demo-wallet")
        self.assertIsNone(u)

    def test_untrusted_paid_text_does_not_poison(self):
        comments = [{"body":"@alice PAID payout pending_id:42", "user":{"login":"attacker"}}]
        c = verifier.prior_payment_markers(comments, "alice", None)
        self.assertTrue(c.ok)

    def test_trusted_structured_payment_marker_detected(self):
        comments = [{"body":"@alice payout-status: paid; pending_id:42", "user":{"login":"Scottcjn"}}]
        c = verifier.prior_payment_markers(comments, "alice", None)
        self.assertFalse(c.ok)

    @patch("verifier._public_ips_for_host", return_value=True)
    def test_hostname_substring_attack_rejected(self, _):
        self.assertIsNone(verifier._validated_proof_url("https://medium.com.attacker.tld/post"))

    @patch("verifier._public_ips_for_host", return_value=True)
    def test_allowed_host_exact(self, _):
        self.assertEqual(verifier._validated_proof_url("https://dev.to/a/b"), "https://dev.to/a/b")

    @patch("verifier._request")
    def test_follow_204(self, req):
        req.return_value = (204, {}, b"")
        self.assertTrue(verifier.follows_target("alice", "Scottcjn", "t").ok)

    @patch("verifier._request")
    def test_star_pagination(self, req):
        import json
        page1 = [{"owner":{"login":"Scottcjn"}}] + [{"owner":{"login":"other"}}]*99
        page2 = [{"owner":{"login":"Scottcjn"}}]
        req.side_effect = [(200, {}, json.dumps(page1).encode()), (200, {}, json.dumps(page2).encode())]
        c, n = verifier.count_owner_stars("alice", "Scottcjn", "t")
        self.assertTrue(c.ok)
        self.assertEqual(n, 2)

    @patch("verifier._request")
    def test_wallet_json_balance(self, req):
        req.return_value = (200, {}, b'{"balance": 12.5}')
        c = verifier.wallet_exists("alice-wallet", "https://node")
        self.assertTrue(c.ok)
        self.assertIn("12.5", c.detail)

    @patch("verifier._request")
    def test_wallet_non_json_200_is_indeterminate(self, req):
        req.return_value = (200, {}, b"<html>ok</html>")
        c = verifier.wallet_exists("alice-wallet", "https://node")
        self.assertIsNone(c.ok)

    @patch("verifier._request")
    def test_wallet_json_without_wallet_signal_is_indeterminate(self, req):
        req.return_value = (200, {}, b'{"ok": true}')
        c = verifier.wallet_exists("alice-wallet", "https://node")
        self.assertIsNone(c.ok)

    def test_output_is_payout_inert(self):
        v = verifier.Verification("alice", "wallet", [], 35)
        text = v.to_markdown()
        self.assertIn("PAYOUT-INERT", text)
        self.assertNotIn("Suggested payout", text)
        self.assertIn("not RTC", text)

if __name__ == '__main__':
    unittest.main()
