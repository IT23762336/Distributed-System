"""
MEMBER 2 INDIVIDUAL TEST FILE - MESSAGE STORAGE COMPONENT
Author: DINUJAYA K V T (IT23398184)

Run this test to verify YOUR storage component works correctly!
Command: python tests/test_member2_individual.py
"""

import unittest
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from message_storage.storage import MessageStorage


class TestMember2Storage(unittest.TestCase):
    """Unit tests for Member 2's Message Storage component"""
    
    def setUp(self):
        self.storage = MessageStorage()
    
    def test_01_initialization(self):
        """Test 1: Storage initializes correctly"""
        self.assertIsNotNone(self.storage.messages)
        self.assertIsNotNone(self.storage.message_index)
        print("  ✓ Test 1 PASSED: Storage initialization works")
    
    def test_02_store_message(self):
        """Test 2: Can store a message"""
        msg_data = json.dumps({"content": "Hello", "sender": "Alice"})
        result = asyncio.run(self.storage.store_message("msg_001", msg_data))
        self.assertTrue(result)
        print("  ✓ Test 2 PASSED: Message storage works")
    
    def test_03_get_message(self):
        """Test 3: Can retrieve stored message"""
        msg_data = json.dumps({"content": "Test", "sender": "Bob"})
        asyncio.run(self.storage.store_message("msg_002", msg_data))
        
        result = asyncio.run(self.storage.get_message("msg_002"))
        self.assertIsNotNone(result)
        print("  ✓ Test 3 PASSED: Message retrieval works")
    
    def test_04_get_all_messages(self):
        """Test 4: Can get all messages"""
        msg1 = json.dumps({"content": "First", "sender": "Alice"})
        msg2 = json.dumps({"content": "Second", "sender": "Bob"})
        asyncio.run(self.storage.store_message("msg_003", msg1))
        asyncio.run(self.storage.store_message("msg_004", msg2))
        
        messages = asyncio.run(self.storage.get_all_messages())
        self.assertIsInstance(messages, list)
        print(f"  ✓ Test 4 PASSED: Get all messages works ({len(messages)} messages)")
    
    def test_05_delete_message(self):
        """Test 5: Can delete a message"""
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


if __name__ == '__main__':
    print("=" * 70)
    print("MEMBER 2: MESSAGE STORAGE COMPONENT - UNIT TESTS")
    print("Author: DINUJAYA K V T (IT23398184)")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMember2Storage)
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
