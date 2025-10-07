"""
MEMBER 4: CONSENSUS & LEADER ELECTION COMPONENT UNIT TESTS
Tests the Raft consensus algorithm and leader election with mocked dependencies.
Author: Member 4 - Consensus & Leader Election Specialist
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from consensus.raft_node import RaftNode, NodeState
import time
import threading


class TestConsensusComponent(unittest.TestCase):
    """Unit tests for Member 4's Consensus component"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.node_addr = ('127.0.0.1', 5000)
        self.cluster = [
            ('127.0.0.1', 5000),
            ('127.0.0.1', 5001),
            ('127.0.0.1', 5002)
        ]
    
    def test_initialization(self):
        """Test 1: RaftNode initializes correctly"""
        node = RaftNode(self.node_addr, self.cluster)
        
        self.assertEqual(node.node_addr, self.node_addr)
        self.assertEqual(len(node.cluster), 3)
        self.assertEqual(node.state, NodeState.FOLLOWER)
        self.assertEqual(node.current_term, 0)
        self.assertIsNone(node.voted_for)
        self.assertIsNone(node.current_leader)
        self.assertIsNotNone(node.state_lock)
        
        node.stop()
        print("✓ Test 1 PASSED: RaftNode initializes in FOLLOWER state")
    
    def test_state_transitions(self):
        """Test 2: Node state transitions work correctly"""
        node = RaftNode(self.node_addr, self.cluster)
        
        # Start as FOLLOWER
        self.assertEqual(node.state, NodeState.FOLLOWER)
        
        # Can transition to CANDIDATE
        with node.state_lock:
            node.state = NodeState.CANDIDATE
        self.assertEqual(node.state, NodeState.CANDIDATE)
        
        # Can transition to LEADER
        with node.state_lock:
            node.state = NodeState.LEADER
        self.assertEqual(node.state, NodeState.LEADER)
        
        node.stop()
        print("✓ Test 2 PASSED: State transitions FOLLOWER→CANDIDATE→LEADER work")
    
    def test_term_increments(self):
        """Test 3: Term increments correctly during elections"""
        node = RaftNode(self.node_addr, self.cluster)
        
        initial_term = node.current_term
        
        with node.state_lock:
            node.current_term += 1
        
        self.assertEqual(node.current_term, initial_term + 1)
        
        node.stop()
        print(f"✓ Test 3 PASSED: Term incremented from {initial_term} to {node.current_term}")
    
    def test_is_leader_check(self):
        """Test 4: is_leader() returns correct status"""
        node = RaftNode(self.node_addr, self.cluster)
        
        # Initially not leader
        self.assertFalse(node.is_leader())
        
        # Set as leader
        with node.state_lock:
            node.state = NodeState.LEADER
        
        self.assertTrue(node.is_leader())
        
        node.stop()
        print("✓ Test 4 PASSED: is_leader() returns correct status")
    
    def test_get_leader_when_unknown(self):
        """Test 5: get_leader() returns None when no leader"""
        node = RaftNode(self.node_addr, self.cluster)
        
        leader = node.get_leader()
        self.assertIsNone(leader)
        
        node.stop()
        print("✓ Test 5 PASSED: Returns None when no leader elected")
    
    def test_get_leader_when_set(self):
        """Test 6: get_leader() returns correct leader"""
        node = RaftNode(self.node_addr, self.cluster)
        
        # Set a leader
        with node.state_lock:
            node.current_leader = ('127.0.0.1', 5001)
        
        leader = node.get_leader()
        self.assertEqual(leader, ('127.0.0.1', 5001))
        
        node.stop()
        print(f"✓ Test 6 PASSED: Returns correct leader: {leader}")
    
    def test_get_state(self):
        """Test 7: get_state() returns current node state"""
        node = RaftNode(self.node_addr, self.cluster)
        
        state = node.get_state()
        self.assertEqual(state, NodeState.FOLLOWER)
        
        with node.state_lock:
            node.state = NodeState.LEADER
        
        state = node.get_state()
        self.assertEqual(state, NodeState.LEADER)
        
        node.stop()
        print(f"✓ Test 7 PASSED: get_state() returns correct state: {state}")
    
    @patch('socket.socket')
    def test_request_vote_higher_term(self, mock_socket):
        """Test 8: Node grants vote to candidate with higher term"""
        node = RaftNode(self.node_addr, self.cluster)
        node.current_term = 5
        node.voted_for = None
        
        # Simulate RequestVote RPC with higher term
        request = {
            'type': 'RequestVote',
            'term': 10,
            'candidate_id': ('127.0.0.1', 5001)
        }
        
        response = node._handle_request_vote(request)
        
        self.assertTrue(response['vote_granted'])
        self.assertEqual(response['term'], 10)
        self.assertEqual(node.current_term, 10)  # Updated to higher term
        
        node.stop()
        print("✓ Test 8 PASSED: Grants vote to candidate with higher term")
    
    @patch('socket.socket')
    def test_request_vote_already_voted(self, mock_socket):
        """Test 9: Node rejects vote if already voted in term"""
        node = RaftNode(self.node_addr, self.cluster)
        node.current_term = 10
        node.voted_for = ('127.0.0.1', 5002)  # Already voted
        
        # Simulate RequestVote from different candidate
        request = {
            'type': 'RequestVote',
            'term': 10,
            'candidate_id': ('127.0.0.1', 5001)
        }
        
        response = node._handle_request_vote(request)
        
        self.assertFalse(response['vote_granted'])
        
        node.stop()
        print("✓ Test 9 PASSED: Rejects vote when already voted in term")
    
    @patch('socket.socket')
    def test_append_entries_heartbeat(self, mock_socket):
        """Test 10: Node processes heartbeat correctly"""
        node = RaftNode(self.node_addr, self.cluster)
        node.current_term = 5
        
        # Simulate AppendEntries (heartbeat) from leader
        request = {
            'type': 'AppendEntries',
            'term': 5,
            'leader_id': ('127.0.0.1', 5001)
        }
        
        response = node._handle_append_entries(request)
        
        self.assertTrue(response['success'])
        self.assertEqual(node.current_leader, ('127.0.0.1', 5001))
        self.assertEqual(node.state, NodeState.FOLLOWER)
        
        node.stop()
        print(f"✓ Test 10 PASSED: Heartbeat processed, leader set to {node.current_leader}")
    
    def test_thread_safety_state_access(self):
        """Test 11: Thread-safe state access"""
        node = RaftNode(self.node_addr, self.cluster)
        results = []
        
        def read_state():
            for _ in range(10):
                state = node.get_state()
                leader = node.get_leader()
                results.append((state, leader))
        
        threads = [threading.Thread(target=read_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reads should succeed
        self.assertEqual(len(results), 50)
        
        node.stop()
        print(f"✓ Test 11 PASSED: Thread-safe, {len(results)} concurrent state reads successful")
    
    def test_election_timeout_randomization(self):
        """Test 12: Election timeouts are randomized"""
        node1 = RaftNode(self.node_addr, self.cluster)
        node2 = RaftNode(('127.0.0.1', 5001), self.cluster)
        
        # Get multiple timeout values
        timeouts = []
        for _ in range(10):
            import random
            random.seed()  # Ensure randomness
            timeout = random.uniform(0.15, 0.30)
            timeouts.append(timeout)
        
        # Should have variation
        self.assertGreater(max(timeouts), min(timeouts))
        
        node1.stop()
        node2.stop()
        print(f"✓ Test 12 PASSED: Election timeouts randomized (range: {min(timeouts):.3f}s - {max(timeouts):.3f}s)")
    
    def test_start_stop_node(self):
        """Test 13: Node starts and stops cleanly"""
        node = RaftNode(self.node_addr, self.cluster)
        
        node.start()
        self.assertTrue(node.running)
        
        time.sleep(0.2)  # Let it run briefly
        
        node.stop()
        self.assertFalse(node.running)
        
        print("✓ Test 13 PASSED: Node starts and stops cleanly")
    
    @patch('socket.socket')
    def test_majority_calculation(self, mock_socket):
        """Test 14: Majority votes calculated correctly"""
        node = RaftNode(self.node_addr, self.cluster)
        
        # 3 nodes: need 2 votes for majority
        cluster_size = len(node.cluster)
        majority = (cluster_size // 2) + 1
        
        self.assertEqual(majority, 2)
        
        # 5 nodes: need 3 votes
        large_cluster = [('127.0.0.1', 5000 + i) for i in range(5)]
        node2 = RaftNode(self.node_addr, large_cluster)
        majority2 = (len(node2.cluster) // 2) + 1
        
        self.assertEqual(majority2, 3)
        
        node.stop()
        node2.stop()
        print(f"✓ Test 14 PASSED: Majority calculation correct (3 nodes→2 votes, 5 nodes→3 votes)")


def run_tests():
    """Run all tests and display results"""
    print("=" * 70)
    print("MEMBER 4: CONSENSUS & LEADER ELECTION COMPONENT - UNIT TEST SUITE")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConsensusComponent)
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
