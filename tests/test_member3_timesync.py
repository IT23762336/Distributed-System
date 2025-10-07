"""
MEMBER 3: TIME SYNCHRONIZATION COMPONENT UNIT TESTS
Tests the distributed time synchronization system with mocked NTP dependencies.
Author: Member 3 - Time Synchronization Specialist
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from time_sync.timesync import TimeSync
import time
import threading


class TestTimeSyncComponent(unittest.TestCase):
    """Unit tests for Member 3's Time Synchronization component"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.ntp_servers = [
            'pool.ntp.org',
            'time.google.com',
            'time.windows.com'
        ]
        self.timesync = TimeSync(ntp_servers=self.ntp_servers)
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self.timesync, 'sync_thread') and self.timesync.sync_thread:
            self.timesync.stop_sync()
    
    def test_initialization(self):
        """Test 1: TimeSync component initializes correctly"""
        self.assertEqual(len(self.timesync.ntp_servers), 3)
        self.assertEqual(self.timesync.offset, 0.0)
        self.assertFalse(self.timesync.is_syncing)
        self.assertIsNotNone(self.timesync.lock)
        print("✓ Test 1 PASSED: TimeSync initializes with correct NTP servers")
    
    @patch('ntplib.NTPClient')
    def test_sync_with_ntp_success(self, mock_ntp_client):
        """Test 2: Successful NTP synchronization"""
        # Mock NTP response
        mock_response = Mock()
        mock_response.offset = 0.123456  # 123ms offset
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_ntp_client.return_value = mock_client_instance
        
        success = self.timesync.sync_with_ntp()
        self.assertTrue(success)
        self.assertEqual(self.timesync.offset, 0.123456)
        print(f"✓ Test 2 PASSED: NTP sync successful, offset: {self.timesync.offset}s")
    
    @patch('ntplib.NTPClient')
    def test_sync_with_ntp_failure_fallback(self, mock_ntp_client):
        """Test 3: NTP sync falls back to next server on failure"""
        mock_client_instance = Mock()
        # First server fails, second succeeds
        mock_response = Mock()
        mock_response.offset = 0.05
        mock_client_instance.request.side_effect = [
            Exception("Network error"),  # First server fails
            mock_response  # Second server succeeds
        ]
        mock_ntp_client.return_value = mock_client_instance
        
        success = self.timesync.sync_with_ntp()
        self.assertTrue(success)
        self.assertEqual(mock_client_instance.request.call_count, 2)
        print("✓ Test 3 PASSED: Fallback to secondary NTP server works")
    
    @patch('ntplib.NTPClient')
    def test_sync_with_ntp_all_servers_fail(self, mock_ntp_client):
        """Test 4: Sync fails when all NTP servers are unreachable"""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = Exception("All servers down")
        mock_ntp_client.return_value = mock_client_instance
        
        success = self.timesync.sync_with_ntp()
        self.assertFalse(success)
        print("✓ Test 4 PASSED: Sync fails gracefully when all servers unreachable")
    
    def test_get_synchronized_time_no_sync(self):
        """Test 5: Get time without synchronization (uses local time)"""
        sync_time = self.timesync.get_synchronized_time()
        local_time = time.time()
        
        # Should be very close (within 1 second)
        self.assertAlmostEqual(sync_time, local_time, delta=1.0)
        print(f"✓ Test 5 PASSED: Returns local time when no sync (offset=0)")
    
    @patch('ntplib.NTPClient')
    def test_get_synchronized_time_with_offset(self, mock_ntp_client):
        """Test 6: Get time with NTP offset applied"""
        # Mock NTP sync with 2-second offset
        mock_response = Mock()
        mock_response.offset = 2.0
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_ntp_client.return_value = mock_client_instance
        
        self.timesync.sync_with_ntp()
        
        sync_time = self.timesync.get_synchronized_time()
        local_time = time.time()
        
        # Synchronized time should be local time + offset
        self.assertAlmostEqual(sync_time, local_time + 2.0, delta=0.5)
        print(f"✓ Test 6 PASSED: Time offset applied correctly ({self.timesync.offset}s)")
    
    def test_get_offset(self):
        """Test 7: Get current time offset"""
        self.timesync.offset = 1.5
        offset = self.timesync.get_offset()
        self.assertEqual(offset, 1.5)
        print(f"✓ Test 7 PASSED: Get offset returns correct value: {offset}s")
    
    @patch('ntplib.NTPClient')
    def test_start_stop_periodic_sync(self, mock_ntp_client):
        """Test 8: Start and stop periodic synchronization"""
        # Mock NTP response
        mock_response = Mock()
        mock_response.offset = 0.1
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_ntp_client.return_value = mock_client_instance
        
        self.timesync.start_periodic_sync(interval=0.5)  # 500ms interval
        self.assertTrue(self.timesync.is_syncing)
        
        time.sleep(0.7)  # Let it sync at least once
        
        self.timesync.stop_sync()
        self.assertFalse(self.timesync.is_syncing)
        
        # Verify sync was called
        self.assertGreater(mock_client_instance.request.call_count, 0)
        print(f"✓ Test 8 PASSED: Periodic sync started and stopped, synced {mock_client_instance.request.call_count} times")
    
    def test_thread_safety_concurrent_reads(self):
        """Test 9: Thread-safe concurrent time reads"""
        self.timesync.offset = 1.0
        results = []
        
        def read_time():
            for _ in range(10):
                t = self.timesync.get_synchronized_time()
                results.append(t)
        
        threads = [threading.Thread(target=read_time) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reads should succeed
        self.assertEqual(len(results), 50)  # 5 threads * 10 reads
        self.assertTrue(all(isinstance(t, float) for t in results))
        print(f"✓ Test 9 PASSED: Thread-safe, {len(results)} concurrent reads successful")
    
    @patch('ntplib.NTPClient')
    def test_offset_precision(self, mock_ntp_client):
        """Test 10: Time offset maintains precision"""
        # Mock NTP with precise offset
        mock_response = Mock()
        mock_response.offset = 0.123456789
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_ntp_client.return_value = mock_client_instance
        
        self.timesync.sync_with_ntp()
        
        # Offset should preserve precision
        self.assertAlmostEqual(self.timesync.offset, 0.123456789, places=6)
        print(f"✓ Test 10 PASSED: Offset precision maintained: {self.timesync.offset}s")
    
    @patch('ntplib.NTPClient')
    def test_multiple_syncs_update_offset(self, mock_ntp_client):
        """Test 11: Multiple syncs update offset correctly"""
        mock_client_instance = Mock()
        
        # First sync: 1.0s offset
        mock_response1 = Mock()
        mock_response1.offset = 1.0
        
        # Second sync: 0.5s offset
        mock_response2 = Mock()
        mock_response2.offset = 0.5
        
        mock_client_instance.request.side_effect = [mock_response1, mock_response2]
        mock_ntp_client.return_value = mock_client_instance
        
        self.timesync.sync_with_ntp()
        self.assertEqual(self.timesync.offset, 1.0)
        
        self.timesync.sync_with_ntp()
        self.assertEqual(self.timesync.offset, 0.5)
        
        print("✓ Test 11 PASSED: Multiple syncs update offset correctly")
    
    def test_get_synchronized_time_format(self):
        """Test 12: Synchronized time is in correct format (Unix timestamp)"""
        sync_time = self.timesync.get_synchronized_time()
        
        # Should be a float representing Unix timestamp
        self.assertIsInstance(sync_time, float)
        self.assertGreater(sync_time, 1609459200)  # After 2021-01-01
        self.assertLess(sync_time, 2000000000)  # Before 2033-05-18
        print(f"✓ Test 12 PASSED: Time format correct (Unix timestamp): {sync_time}")


def run_tests():
    """Run all tests and display results"""
    print("=" * 70)
    print("MEMBER 3: TIME SYNCHRONIZATION COMPONENT - UNIT TEST SUITE")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimeSyncComponent)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("TEST SUMMARY:")
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
