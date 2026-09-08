"""
ElevateIQ — Unit Tests for SIP Dial-Plan Router
================================================
Tests E.164 normalization, regex dial-plan rule matching, priority carrier selection,
failover circuit tripping, emergency call bypass, and DTMF IVR state transitions.
"""

import unittest
from backend.services.media.sip_dial_plan_router import (
    SipDialPlanRouter,
    CarrierPriority,
    SipTrunkCarrier,
    DialPlanRule
)


class TestSipDialPlanRouter(unittest.TestCase):

    def setUp(self):
        self.router = SipDialPlanRouter()

    def test_e164_normalization(self):
        # US Local Format
        self.assertEqual(self.router.normalize_to_e164("(415) 555-2671"), "+14155552671")
        self.assertEqual(self.router.normalize_to_e164("415-555-2671"), "+14155552671")
        self.assertEqual(self.router.normalize_to_e164("14155552671"), "+14155552671")

        # International with Plus
        self.assertEqual(self.router.normalize_to_e164("+44 20 7946 0991"), "+442079460991")
        self.assertEqual(self.router.normalize_to_e164("+49 89 636 48018"), "+498963648018")

        # Empty
        self.assertEqual(self.router.normalize_to_e164(""), "")

    def test_match_dial_plan_emergency(self):
        rule, target = self.router.match_dial_plan("911")
        self.assertIsNotNone(rule)
        self.assertTrue(rule.is_emergency)
        self.assertFalse(rule.require_pin)
        self.assertEqual(rule.target_bridge, "psap_emergency_gateway")

    def test_match_dial_plan_us_tollfree(self):
        rule, target = self.router.match_dial_plan("+18005551234")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.target_bridge, "bridge_na_tollfree")
        self.assertTrue(rule.require_pin)

    def test_match_dial_plan_europe(self):
        rule, target = self.router.match_dial_plan("+442079460991")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.target_bridge, "bridge_eu_central")

    def test_carrier_priority_selection_and_failover(self):
        # Initially, Twilio (Primary) should be selected
        c1 = self.router.select_active_carrier()
        self.assertEqual(c1.carrier_id, "carrier_twilio")
        self.assertEqual(c1.active_calls, 1)

        # Release call
        self.router.release_carrier_call("carrier_twilio")
        self.assertEqual(c1.active_calls, 0)

        # Simulate 3 failures on Twilio -> should trip circuit
        for _ in range(3):
            self.router.record_carrier_failure("carrier_twilio")
        self.assertFalse(self.router.carriers["carrier_twilio"].is_active)

        # Next selection should seamlessly failover to Telnyx (Secondary)
        c2 = self.router.select_active_carrier()
        self.assertEqual(c2.carrier_id, "carrier_telnyx")
        self.assertEqual(c2.priority, CarrierPriority.SECONDARY)

    def test_ivr_dtmf_digit_accumulation(self):
        expected = "8492"

        # Digit 8
        digits, done, ok = self.router.process_ivr_dtmf_input("", "8", expected)
        self.assertEqual(digits, "8")
        self.assertFalse(done)

        # Digit 4
        digits, done, ok = self.router.process_ivr_dtmf_input(digits, "4", expected)
        self.assertEqual(digits, "84")
        self.assertFalse(done)

        # Digit 9
        digits, done, ok = self.router.process_ivr_dtmf_input(digits, "9", expected)
        self.assertEqual(digits, "849")
        self.assertFalse(done)

        # Digit 2 -> Length matches expected length 4 -> completes and validates!
        digits, done, ok = self.router.process_ivr_dtmf_input(digits, "2", expected)
        self.assertEqual(digits, "8492")
        self.assertTrue(done)
        self.assertTrue(ok)

    def test_ivr_dtmf_reset_and_hash_terminator(self):
        # Test '*' resets buffer
        digits, done, ok = self.router.process_ivr_dtmf_input("123", "*", "9999")
        self.assertEqual(digits, "")
        self.assertFalse(done)

        # Test '#' terminator completes entry
        digits, done, ok = self.router.process_ivr_dtmf_input("9999", "#", "9999")
        self.assertEqual(digits, "9999")
        self.assertTrue(done)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
