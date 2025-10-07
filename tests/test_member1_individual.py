"""
MEMBER 1 INDIVIDUAL TEST FILE - FAILOVER COMPONENT
Author: D B Y BINUWARA (IT23184558)

Run this test to verify YOUR failover component works correctly!
Command: python tests/test_member1_individual.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from failover.failover import Failover


class TestMember1Failover(unittest.TestCase):
    """Unit tests for Member 1's Failover component"""
    
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


if __name__ == '__main__':
    print("=" * 70)
    print("MEMBER 1: FAILOVER COMPONENT - UNIT TESTS")
    print("Author: D B Y BINUWARA (IT23184558)")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMember1Failover)
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
