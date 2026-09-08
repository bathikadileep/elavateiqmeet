"""
ElevateIQ — Extended SFU Worker Pool & Router Capabilities Test Suite
====================================================================
Tests SFU Media Worker Pool singleton, process PID monitoring, transport allocation,
and router capability negotiation.
"""

import unittest
from backend.sfu.worker import get_sfu_worker_pool
from backend.sfu.router import SFURouter


class ExtendedSFUTestSuite(unittest.TestCase):

    def test_sfu_worker_pool_singleton(self):
        """Test SFU worker pool stats and process monitor."""
        pool = get_sfu_worker_pool()
        self.assertIsNotNone(pool)

        stats = pool.get_system_stats()
        self.assertIn("worker_pid", stats)
        self.assertIn("num_workers", stats)

    def test_sfu_router_capabilities(self):
        """Test SFU Router transport creation and capabilities."""
        pool = get_sfu_worker_pool()
        caps = pool.get_router_capabilities()
        self.assertIn("codecs", caps)

        router = SFURouter("test-room-sfu-101")
        transport = router.create_web_rtc_transport("sendrecv")
        self.assertIsNotNone(transport.id)


if __name__ == "__main__":
    unittest.main()
