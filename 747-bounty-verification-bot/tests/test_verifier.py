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

    def test_prior_payment_marker_detected(self):
        comments = [{"body":"@alice accepted — 10 RTC queued; pending_id 42", "user":{"login":"maintainer"}}]
        c = verifier.prior_payment_markers(comments, "alice", None)
        self.assertFalse(c.ok)

    def test_no_payment_marker(self):
        comments = [{"body":"@alice thanks, under review", "user":{"login":"maintainer"}}]
        c = verifier.prior_payment_markers(comments, "alice", None)
        self.assertTrue(c.ok)

    def test_liveness_rejects_non_http(self):
        c = verifier.url_liveness("file:///etc/passwd")
        self.assertFalse(c.ok)

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
    def test_word_count(self, req):
        req.return_value = (200, {}, ("<p>" + "word "*600 + "</p>").encode())
        c = verifier.article_word_count("https://dev.to/a/b")
        self.assertTrue(c.ok)

if __name__ == '__main__':
    unittest.main()
