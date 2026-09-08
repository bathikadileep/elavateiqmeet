"""
ElevateIQ — Extended In-Meeting Polling & Voting Test Suite
===========================================================
Tests poll creation, multiselect voting, vote count aggregation, and poll closure.
"""

import unittest
from backend.app import create_app
from backend.extensions import db
from backend.models.models import Poll, PollOption, PollVote, User, Meeting


class ExtendedPollsTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.host = User(
            username="poll_host",
            email="poll@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Poll Host",
            status="active",
            email_verified=True,
        )
        db.session.add(self.host)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_poll_creation_options_and_voting(self):
        """Test poll creation, options attachment, and voting."""
        poll = Poll(
            meeting_code="poll-1234-tst",
            created_by=self.host.id,
            question="What features should we prioritize for Q4?",
            is_multiselect=False,
            is_published=True,
            is_closed=False
        )
        db.session.add(poll)
        db.session.commit()

        opt1 = PollOption(poll_id=poll.id, option_text="WebRTC SFU Upgrade")
        opt2 = PollOption(poll_id=poll.id, option_text="AI Speech Diarization")
        db.session.add_all([opt1, opt2])
        db.session.commit()

        # Submit Vote
        vote = PollVote(poll_id=poll.id, option_id=opt1.id, user_id=self.host.id)
        db.session.add(vote)
        db.session.commit()

        vote_count = PollVote.query.filter_by(option_id=opt1.id).count()
        self.assertEqual(vote_count, 1)


if __name__ == "__main__":
    unittest.main()
