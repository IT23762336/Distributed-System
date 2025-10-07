"""
MEMBER 3 INDIVIDUAL TEST FILE - TIME SYNCHRONIZATION COMPONENT
Author: Member 3 - Time Synchronization Specialist

Run this test to verify YOUR time sync component works correctly!
Command: python tests/test_member3_individual.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from time_sync.timesync import TimeSync


class TestMember3TimeSync(unittest.TestCase):
    """Unit tests for Member 3's Time Synchronization component"""
    
    def setUp(self):
        self.timesync = TimeSync()
    
    def tearDown(self):
        if hasattr(self.timesync, 'stop_event'):
            self.timesync.stop_event.set()
    
    def test_01_initialization(self):
        """Test 1: TimeSync initializes correctly"""
        self.assertIsNotNone(self.timesync.client)
        self.assertEqual(self.timesync.offset, 0)
        self.assertIsNotNone(self.timesync.ntp_servers)
        print(f"  ✓ Test 1 PASSED: TimeSync initialization works ({len(self.timesync.ntp_servers)} NTP servers)")
    
    def test_02_get_synced_time(self):
        """Test 2: Can get synchronized time"""
        sync_time = self.timesync.get_synced_time()
        self.assertIsInstance(sync_time, float)
        self.assertGreater(sync_time, 1609459200)  # After 2021
        print(f"  ✓ Test 2 PASSED: Get synced time works ({sync_time:.2f})")
    
    def test_03_get_synced_time_str(self):
        """Test 3: Can get time as string"""
        time_str = self.timesync.get_synced_time_str()
        self.assertIsInstance(time_str, str)
        self.assertTrue(len(time_str) > 10)
        print(f"  ✓ Test 3 PASSED: Get time string works ({time_str})")
    
    def test_04_offset_starts_at_zero(self):
        """Test 4: Offset starts at zero"""
        self.assertEqual(self.timesync.offset, 0)
        print("  ✓ Test 4 PASSED: Initial offset is zero")


if __name__ == '__main__':
    print("=" * 70)
    print("MEMBER 3: TIME SYNCHRONIZATION COMPONENT - UNIT TESTS")
    print("Author: Member 3 - Time Synchronization Specialist")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMember3TimeSync)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("TEST SUMMARY:")
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failed: {len(result.failures) + len(result.errors)}")
    if result.wasSuccessful():
        print("  Status: ✅ ALL TESTS PASSED!")
    else:
        print("  Status: ❌ SOME TESTS FAILED")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)
