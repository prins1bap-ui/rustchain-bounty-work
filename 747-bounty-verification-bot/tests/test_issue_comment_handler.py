import datetime as dt
import unittest
from unittest.mock import patch

import issue_comment_handler as handler


def event(body="Claiming\nWallet: alice", action="created"):
    return {
        "action": action,
        "comment": {
            "id": 123,
            "body": body,
            "created_at": "2026-09-08T20:00:00Z",
            "user": {"login": "alice", "type": "User"},
        },
        "issue": {"comments_url": "https://api.github.com/repos/o/r/issues/1/comments"},
    }


class IssueCommentHandlerTests(unittest.TestCase):
    def test_claim_keywords(self):
        self.assertTrue(handler.should_process("Claiming this bounty\nWallet: alice"))
        self.assertFalse(handler.should_process("nice project"))

    def test_bot_loop_guard(self):
        self.assertFalse(handler.should_process(handler.BOT_MARKER + "\nClaiming"))
        self.assertFalse(handler.should_process("Claiming", "Bot"))

    @patch.object(handler, "github_json")
    @patch.object(handler, "fetch_all_comments")
    @patch.object(handler, "verify")
    def test_claim_posts_payout_inert_verification_once(self, verify, fetch_all_comments, github_json):
        verify.return_value.to_markdown.return_value = "OK"
        fetch_all_comments.return_value = []
        self.assertEqual(handler.run(event(), "token", "https://rustchain.org"), 0)
        self.assertEqual(github_json.call_args.kwargs["method"], "POST")
        body = github_json.call_args.kwargs["payload"]["body"]
        self.assertIn("rtc-payout-ignore:true", body)
        self.assertIn("source-comment:123;sha256:", body)
        self.assertIn("verifier-user:alice", body)

    @patch.object(handler, "github_json")
    @patch.object(handler, "fetch_all_comments")
    @patch.object(handler, "verify")
    def test_same_revision_is_idempotent(self, verify, fetch_all_comments, github_json):
        marker = handler._source_marker("123", "Claiming\nWallet: alice")
        fetch_all_comments.return_value = [{"body": marker}]
        self.assertEqual(handler.run(event(), "token", "https://rustchain.org"), 0)
        github_json.assert_not_called()
        verify.assert_not_called()

    def test_user_throttle(self):
        now = dt.datetime(2026, 9, 8, 20, 10, tzinfo=dt.timezone.utc)
        history = [{
            "body": handler.BOT_MARKER + "\n" + handler._user_marker("alice"),
            "created_at": "2026-09-08T20:00:00Z"
        }]
        self.assertIsNotNone(handler.throttle_reason(history, "alice", now))

    def test_issue_burst_throttle(self):
        now = dt.datetime(2026, 9, 8, 20, 10, tzinfo=dt.timezone.utc)
        history = [{"body": handler.BOT_MARKER, "created_at": "2026-09-08T20:00:00Z"}
                   for _ in range(handler.ISSUE_BURST_LIMIT)]
        self.assertIsNotNone(handler.throttle_reason(history, "bob", now))

    @patch.object(handler, "github_json")
    @patch.object(handler, "fetch_all_comments")
    @patch.object(handler, "verify")
    def test_edited_action_supported(self, verify, fetch_all_comments, github_json):
        verify.return_value.to_markdown.return_value = "OK"
        fetch_all_comments.return_value = []
        self.assertEqual(handler.run(event(action="edited"), "token", "https://rustchain.org"), 0)
        github_json.assert_called_once()

    def test_malformed_event_fails(self):
        with self.assertRaises(ValueError):
            handler.run({"action":"created","comment":{"body":"Claiming"}}, "token", "node")

if __name__ == "__main__":
    unittest.main()
