"""
MEMBER 1: FAILOVER COMPONENT UNIT TESTS
Tests the failure detection and node health monitoring system with mocked dependencies.
Author: Member 1 - Failover & Recovery Specialist
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from failover.failover import Failover
import time
import socket


class TestFailoverComponent(unittest.TestCase):
    """Unit tests for Member 1's Failover component"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.cluster_nodes = [
            ('127.0.0.1', 5000),
            ('127.0.0.1', 5001),
            ('127.0.0.1', 5002)
        ]
        
        # Create mock consensus object
        self.mock_consensus = Mock()
        self.mock_consensus.get_leader.return_value = ('127.0.0.1', 5000)
        
        # Create failover instance with mocked consensus
        self.failover = Failover(self.cluster_nodes, consensus=self.mock_consensus)
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self.failover, 'monitoring') and self.failover.monitoring:
            self.failover.stop_monitoring()
    
    def test_initialization(self):
        """Test 1: Failover component initializes correctly"""
        self.assertEqual(len(self.failover.cluster_nodes), 3)
        self.assertEqual(len(self.failover.healthy_nodes), 0)
        self.assertIsNotNone(self.failover.lock)
        self.assertFalse(self.failover.monitoring)
        print("✓ Test 1 PASSED: Failover initializes with correct cluster nodes")
    
    def test_get_healthy_nodes_empty(self):
        """Test 2: Get healthy nodes when none are marked healthy"""
        healthy = self.failover.get_healthy_nodes()
        self.assertEqual(len(healthy), 0)
        print("✓ Test 2 PASSED: Returns empty list when no nodes are healthy")
    
    @patch('socket.socket')
    def test_check_node_health_success(self, mock_socket):
        """Test 3: Health check succeeds for responsive node"""
        # Mock successful connection
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None
        
        result = self.failover._check_node_health(('127.0.0.1', 5000))
        self.assertTrue(result)
        print("✓ Test 3 PASSED: Health check succeeds for responsive node")
    
    @patch('socket.socket')
    def test_check_node_health_failure(self, mock_socket):
        """Test 4: Health check fails for unresponsive node"""
        # Mock connection failure
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = socket.error("Connection refused")
        
        result = self.failover._check_node_health(('127.0.0.1', 5000))
        self.assertFalse(result)
        print("✓ Test 4 PASSED: Health check fails for unresponsive node")
    
    @patch('socket.socket')
    def test_monitor_health_marks_nodes_healthy(self, mock_socket):
        """Test 5: Monitor correctly marks healthy nodes"""
        # Mock all nodes as healthy
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None
        
        self.failover._monitor_health()
        
        healthy_nodes = self.failover.get_healthy_nodes()
        self.assertEqual(len(healthy_nodes), 3)
        print(f"✓ Test 5 PASSED: Monitor marks all 3 nodes as healthy: {healthy_nodes}")
    
    @patch('socket.socket')
    def test_monitor_health_detects_failure(self, mock_socket):
        """Test 6: Monitor detects failed nodes"""
        # Mock first node as failed, others as healthy
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        
        def connect_side_effect(addr):
            if addr[1] == 5000:
                raise socket.error("Connection refused")
            return None
        
        mock_sock_instance.connect.side_effect = connect_side_effect
        
        self.failover._monitor_health()
        
        healthy_nodes = self.failover.get_healthy_nodes()
        self.assertEqual(len(healthy_nodes), 2)
        self.assertNotIn(('127.0.0.1', 5000), healthy_nodes)
        print(f"✓ Test 6 PASSED: Monitor detects failed node, {len(healthy_nodes)} nodes healthy")
    
    def test_get_current_leader_from_consensus(self):
        """Test 7: Get current leader calls consensus correctly"""
        leader = self.failover.get_current_leader()
        self.assertEqual(leader, ('127.0.0.1', 5000))
        self.mock_consensus.get_leader.assert_called_once()
        print(f"✓ Test 7 PASSED: Gets leader from consensus: {leader}")
    
    def test_get_current_leader_no_consensus(self):
        """Test 8: Get current leader returns None when no consensus"""
        failover_no_consensus = Failover(self.cluster_nodes, consensus=None)
        leader = failover_no_consensus.get_current_leader()
        self.assertIsNone(leader)
        print("✓ Test 8 PASSED: Returns None when no consensus module")
    
    @patch('socket.socket')
    def test_thread_safety_concurrent_access(self, mock_socket):
        """Test 9: Thread-safe access to healthy_nodes set"""
        # Mock nodes as healthy
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None
        
        # Add some nodes
        self.failover._monitor_health()
        
        # Concurrent access should not raise exceptions
        import threading
        results = []
        
        def access_healthy_nodes():
            try:
                nodes = self.failover.get_healthy_nodes()
                results.append(len(nodes))
            except Exception as e:
                results.append(str(e))
        
        threads = [threading.Thread(target=access_healthy_nodes) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should succeed
        self.assertTrue(all(isinstance(r, int) for r in results))
        print(f"✓ Test 9 PASSED: Thread-safe access works, 5 concurrent reads successful")
    
    @patch('socket.socket')
    def test_start_stop_monitoring(self, mock_socket):
        """Test 10: Start and stop monitoring threads"""
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None
        
        self.failover.start_monitoring()
        self.assertTrue(self.failover.monitoring)
        time.sleep(0.2)  # Let it run briefly
        
        self.failover.stop_monitoring()
        self.assertFalse(self.failover.monitoring)
        print("✓ Test 10 PASSED: Monitoring starts and stops correctly")


def run_tests():
    """Run all tests and display results"""
    print("=" * 70)
    print("MEMBER 1: FAILOVER COMPONENT - UNIT TEST SUITE")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFailoverComponent)
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
