"""
SIMPLIFIED UNIT TESTS FOR ALL MEMBERS
These tests verify the basic functionality of each component WITHOUT mocking,
focusing on actual method calls and behavior verification.
"""

import unittest
import sys
import os
import asyncio
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from failover.failover import Failover
from message_storage.storage import MessageStorage
from time_sync.timesync import TimeSync
from consensus.raft_node import RaftNode, NodeState


def print_header(text, width=80):
    """Print a formatted header"""
    print()
    print("=" * width)
    print(text.center(width))
    print("=" * width)
    print()


class TestMember1Failover(unittest.TestCase):
    """MEMBER 1: Failover Component Tests"""
    
    def setUp(self):
        self.cluster = [('127.0.0.1', 5000), ('127.0.0.1', 5001), ('127.0.0.1', 5002)]
        self.failover = Failover(self.cluster, consensus=None)
    
    def test_01_initialization(self):
        """Test 1: Failover initializes correctly"""
        self.assertEqual(len(self.failover.cluster_nodes), 3)
        self.assertIsNotNone(self.failover.healthy_nodes)
        print("  ✓ Test 1 PASSED: Failover initialization works")
    
    def test_02_get_healthy_nodes(self):
        """Test 2: Can get healthy nodes list"""
        nodes = self.failover.get_healthy_nodes()
        self.assertIsInstance(nodes, (list, set))
        print(f"  ✓ Test 2 PASSED: Get healthy nodes works ({len(nodes)} nodes)")
    
    def test_03_get_leader_no_consensus(self):
        """Test 3: Get leader returns None when no consensus"""
        leader = self.failover.get_leader()
        self.assertIsNone(leader)
        print("  ✓ Test 3 PASSED: Returns None when no consensus")


class TestMember2Storage(unittest.TestCase):
    """MEMBER 2: Message Storage Component Tests"""
    
    def setUp(self):
        self.storage = MessageStorage()
    
    def test_01_initialization(self):
        """Test 1: Storage initializes correctly"""
        self.assertIsNotNone(self.storage.messages)
        self.assertIsNotNone(self.storage.message_index)
        print("  ✓ Test 1 PASSED: Storage initialization works")
    
    def test_02_store_message(self):
        """Test 2: Can store a message"""
        import json
        msg_data = json.dumps({"content": "Hello", "sender": "Alice"})
        result = asyncio.run(self.storage.store_message("msg_001", msg_data))
        self.assertTrue(result)
        print("  ✓ Test 2 PASSED: Message storage works")
    
    def test_03_get_message(self):
        """Test 3: Can retrieve stored message"""
        import json
        msg_data = json.dumps({"content": "Test", "sender": "Bob"})
        asyncio.run(self.storage.store_message("msg_002", msg_data))
        
        result = asyncio.run(self.storage.get_message("msg_002"))
        self.assertIsNotNone(result)
        print("  ✓ Test 3 PASSED: Message retrieval works")
    
    def test_04_get_all_messages(self):
        """Test 4: Can get all messages"""
        import json
        msg1 = json.dumps({"content": "First", "sender": "Alice"})
        msg2 = json.dumps({"content": "Second", "sender": "Bob"})
        asyncio.run(self.storage.store_message("msg_003", msg1))
        asyncio.run(self.storage.store_message("msg_004", msg2))
        
        messages = asyncio.run(self.storage.get_all_messages())
        self.assertIsInstance(messages, list)
        print(f"  ✓ Test 4 PASSED: Get all messages works ({len(messages)} messages)")
    
    def test_05_delete_message(self):
        """Test 5: Can delete a message"""
        import json
        msg = json.dumps({"content": "Delete me", "sender": "Charlie"})
        asyncio.run(self.storage.store_message("msg_005", msg))
        
        result = asyncio.run(self.storage.delete_message("msg_005"))
        self.assertTrue(result)
        print("  ✓ Test 5 PASSED: Message deletion works")
    
    def test_06_get_message_count(self):
        """Test 6: Can get message count"""
        count = asyncio.run(self.storage.get_message_count())
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
        print(f"  ✓ Test 6 PASSED: Get message count works ({count} messages)")


class TestMember3TimeSync(unittest.TestCase):
    """MEMBER 3: Time Synchronization Component Tests"""
    
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


class TestMember4Consensus(unittest.TestCase):
    """MEMBER 4: Consensus & Leader Election Component Tests"""
    
    def setUp(self):
        self.node_addr = "127.0.0.1:6000"
        self.cluster = ["127.0.0.1:6000", "127.0.0.1:6001", "127.0.0.1:6002"]
        self.node = None
    
    def tearDown(self):
        if self.node:
            self.node.stop()
    
    def test_01_initialization(self):
        """Test 1: RaftNode initializes correctly"""
        self.node = RaftNode(self.node_addr, self.cluster)
        
        self.assertEqual(self.node.node_id, self.node_addr)
        self.assertEqual(len(self.node.cluster_nodes), 3)  # Fixed: cluster_nodes not cluster
        self.assertEqual(self.node.state, NodeState.FOLLOWER)
        self.assertEqual(self.node.current_term, 0)
        print("  ✓ Test 1 PASSED: RaftNode initialization works (FOLLOWER state, term 0)")
    
    def test_02_is_leader(self):
        """Test 2: is_leader() method works"""
        self.node = RaftNode(self.node_addr, self.cluster)
        
        is_leader = self.node.is_leader()
        self.assertFalse(is_leader)  # Starts as follower
        print("  ✓ Test 2 PASSED: is_leader() works (initially False)")
    
    def test_03_get_leader(self):
        """Test 3: get_leader() returns None initially"""
        self.node = RaftNode(self.node_addr, self.cluster)
        
        leader = self.node.get_leader()
        self.assertIsNone(leader)
        print("  ✓ Test 3 PASSED: get_leader() works (initially None)")
    
    def test_04_get_state(self):
        """Test 4: get_state() returns node state"""
        self.node = RaftNode(self.node_addr, self.cluster)
        
        state = self.node.get_state()
        self.assertIsInstance(state, dict)
        self.assertIn('node_id', state)  # Fixed: node_id not node_addr
        self.assertIn('state', state)
        self.assertIn('term', state)
        print(f"  ✓ Test 4 PASSED: get_state() works ({state['state']}, term {state['term']})")
    
    def test_05_get_current_term(self):
        """Test 5: get_current_term() works"""
        self.node = RaftNode(self.node_addr, self.cluster)
        
        term = self.node.get_current_term()
        self.assertEqual(term, 0)
        print(f"  ✓ Test 5 PASSED: get_current_term() works (term {term})")
    
    def test_06_start_stop(self):
        """Test 6: Node can start and stop"""
        self.node = RaftNode(self.node_addr, self.cluster)
        
        self.node.start()
        self.assertTrue(self.node.running)
        
        time.sleep(0.2)  # Let it run briefly
        
        self.node.stop()
        self.assertFalse(self.node.running)
        print("  ✓ Test 6 PASSED: Start/stop works correctly")


def run_all_tests():
    """Run all simplified tests"""
    
    print_header("SIMPLIFIED UNIT TESTS - ALL MEMBER COMPONENTS")
    print("Testing each member's component with actual APIs (no mocking)")
    print("Each member can run these tests to verify their component works!\n")
    
    test_classes = [
        ("MEMBER 1: Failover Component", TestMember1Failover),
        ("MEMBER 2: Message Storage Component", TestMember2Storage),
        ("MEMBER 3: Time Synchronization Component", TestMember3TimeSync),
        ("MEMBER 4: Consensus & Leader Election Component", TestMember4Consensus)
    ]
    
    all_results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for member_name, test_class in test_classes:
        print_header(member_name, width=80)
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Run tests with minimal output
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        # Collect statistics
        tests_run = result.testsRun
        passed = tests_run - len(result.failures) - len(result.errors)
        failed = len(result.failures) + len(result.errors)
        
        total_tests += tests_run
        total_passed += passed
        total_failed += failed
        
        all_results.append({
            'member': member_name,
            'tests': tests_run,
            'passed': passed,
            'failed': failed,
            'success': result.wasSuccessful()
        })
        
        # Print summary
        print()
        print(f"{'─' * 80}")
        print(f"  SUMMARY: {tests_run} tests, {passed} passed, {failed} failed")
        print(f"  STATUS: {'✓ SUCCESS' if result.wasSuccessful() else '✗ FAILED'}")
        print(f"{'─' * 80}\n")
    
    # Print final report
    print_header("FINAL TEST REPORT", width=80)
    
    print("┌" + "─" * 78 + "┐")
    print("│" + " COMPONENT TEST RESULTS".center(78) + "│")
    print("├" + "─" * 45 + "┬" + "─" * 8 + "┬" + "─" * 8 + "┬" + "─" * 13 + "┤")
    print("│" + " Component".ljust(45) + "│" + " Tests".center(8) + "│" + " Passed".center(8) + "│" + " Status".center(13) + "│")
    print("├" + "─" * 45 + "┼" + "─" * 8 + "┼" + "─" * 8 + "┼" + "─" * 13 + "┤")
    
    for result in all_results:
        member = result['member'][:43]
        tests = str(result['tests'])
        passed = str(result['passed'])
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        
        print("│ " + member.ljust(44) + "│" + tests.center(8) + "│" + passed.center(8) + "│" + status.center(13) + "│")
    
    print("├" + "─" * 45 + "┼" + "─" * 8 + "┼" + "─" * 8 + "┼" + "─" * 13 + "┤")
    print("│" + " TOTAL".ljust(45) + "│" + str(total_tests).center(8) + "│" + str(total_passed).center(8) + "│" + ("✓ ALL PASS" if all(r['success'] for r in all_results) else "✗ SOME FAIL").center(13) + "│")
    print("└" + "─" * 45 + "┴" + "─" * 8 + "┴" + "─" * 8 + "┴" + "─" * 13 + "┘")
    
    print()
    print(f"OVERALL: {total_passed}/{total_tests} tests passed ({100 * total_passed // total_tests if total_tests > 0 else 0}%)")
    print()
    
    if all(r['success'] for r in all_results):
        print("🎉 SUCCESS! All components work correctly!")
        print()
        print("✓ All 4 member components are functional")
        print("✓ Each member's work is independently verified")
        print("✓ Ready for integration and submission")
    else:
        print("⚠️  Some tests failed - review output above")
    
    print()
    print("=" * 80)
    print("HOW TO RUN INDIVIDUAL TESTS:")
    print("=" * 80)
    print()
    print("To test your own component, run this file and it will test all components.")
    print("All tests use actual API calls without complex mocking.")
    print()
    
    return all(r['success'] for r in all_results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
