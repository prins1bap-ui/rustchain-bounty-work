import unittest
from unittest.mock import patch

from bounty_verifier.core import (
    Check,
    Verification,
    duplicate_payment_check,
    extract_article_url,
    extract_wallet,
    is_public_http_url,
    markdown,
)


class CoreTests(unittest.TestCase):
    def test_extract_wallet(self):
        wallet = "RTC" + "a" * 40
        self.assertEqual(extract_wallet(f"Wallet: {wallet}"), wallet)
        self.assertIsNone(extract_wallet("RTC-not-a-wallet"))

    def test_article_allowlist(self):
        self.assertEqual(extract_article_url("see https://dev.to/example/post"), "https://dev.to/example/post")
        self.assertIsNone(extract_article_url("see https://example.com/post"))

    @patch("bounty_verifier.core.socket.getaddrinfo")
    def test_private_target_rejected(self, gai):
        gai.return_value = [(2, 1, 6, "", ("127.0.0.1", 443))]
        self.assertFalse(is_public_http_url("https://dev.to/test"))

    def test_duplicate_requires_claimant_and_payment_language(self):
        self.assertEqual(duplicate_payment_check(["@alice nice work"], "alice").status, "pass")
        self.assertEqual(duplicate_payment_check(["@alice approved, pending_id 42"], "alice").status, "review")
        self.assertEqual(duplicate_payment_check(["@bob paid 5 RTC"], "alice").status, "pass")

    def test_markdown_has_human_approval_boundary(self):
        c = Check("pass", "ok")
        v = Verification("alice", c, c, c, c, c)
        self.assertIn("Human approval is required", markdown(v))


if __name__ == "__main__":
    unittest.main()
