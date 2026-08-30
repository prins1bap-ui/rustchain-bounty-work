import unittest
from unittest.mock import patch

import issue_comment_handler as handler


class IssueCommentHandlerTests(unittest.TestCase):
    def test_claim_keywords(self):
        self.assertTrue(handler.should_process("Claiming this bounty\nWallet: alice"))
        self.assertTrue(handler.should_process("/claim miner_id: alice"))
        self.assertFalse(handler.should_process("nice project"))

    def test_bot_loop_guard(self):
        self.assertFalse(handler.should_process(handler.BOT_MARKER + "\nClaiming"))
        self.assertFalse(handler.should_process("Claiming", "Bot"))

    @patch.object(handler, "github_json")
    @patch.object(handler, "fetch_all_comments")
    @patch.object(handler, "verify")
    def test_claim_posts_verification_once(self, verify, fetch_all_comments, github_json):
        verify.return_value.to_markdown.return_value = "OK"
        fetch_all_comments.return_value = []
        event = {
            "comment": {
                "id": 123,
                "body": "Claiming\nWallet: alice",
                "user": {"login": "alice", "type": "User"},
            },
            "issue": {"comments_url": "https://api.github.com/repos/o/r/issues/1/comments"},
        }
        self.assertEqual(handler.run(event, "token", "https://rustchain.org"), 0)
        self.assertEqual(github_json.call_args.kwargs["method"], "POST")
        self.assertIn("source-comment:123", github_json.call_args.kwargs["payload"]["body"])

    @patch.object(handler, "github_json")
    @patch.object(handler, "fetch_all_comments")
    @patch.object(handler, "verify")
    def test_retry_is_idempotent(self, verify, fetch_all_comments, github_json):
        fetch_all_comments.return_value = [{"body": "<!-- source-comment:123 -->"}]
        event = {
            "comment": {
                "id": 123,
                "body": "Claiming\nWallet: alice",
                "user": {"login": "alice", "type": "User"},
            },
            "issue": {"comments_url": "https://api.github.com/repos/o/r/issues/1/comments"},
        }
        self.assertEqual(handler.run(event, "token", "https://rustchain.org"), 0)
        github_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
