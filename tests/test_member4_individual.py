"""
MEMBER 4 INDIVIDUAL TEST FILE - CONSENSUS & LEADER ELECTION COMPONENT
Author: ABEYRATHNA J G D A

Run this test to verify YOUR consensus component works correctly!
Command: python tests/test_member4_individual.py
"""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from consensus.raft_node import RaftNode, NodeState


class TestMember4Consensus(unittest.TestCase):
    """Unit tests for Member 4's Consensus component"""
    
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
        self.assertEqual(len(self.node.cluster_nodes), 3)
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
        self.assertIn('node_id', state)
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


if __name__ == '__main__':
    print("=" * 70)
    print("MEMBER 4: CONSENSUS & LEADER ELECTION COMPONENT - UNIT TESTS")
    print("Author: ABEYRATHNA J G D A")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMember4Consensus)
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
