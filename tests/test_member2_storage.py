"""
MEMBER 2: MESSAGE STORAGE COMPONENT UNIT TESTS
Tests the distributed message storage and replication system with mocked dependencies.
Author: Member 2 - Storage & Replication Specialist
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from message_storage.storage import MessageStorage
import asyncio
import threading


class TestMessageStorageComponent(unittest.TestCase):
    """Unit tests for Member 2's Message Storage component"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        # Create mock RaftNode
        self.mock_raft = Mock()
        self.mock_raft.is_leader.return_value = True
        self.mock_raft.get_leader.return_value = ('127.0.0.1', 5000)
        
        # Create storage instance with mocked Raft
        self.storage = MessageStorage(raft_node=self.mock_raft)
    
    def test_initialization(self):
        """Test 1: Storage component initializes correctly"""
        self.assertIsNotNone(self.storage.messages)
        self.assertIsNotNone(self.storage.message_index)
        self.assertIsNotNone(self.storage.lock)
        self.assertEqual(len(self.storage.messages), 0)
        self.assertEqual(len(self.storage.message_index), 0)
        print("✓ Test 1 PASSED: Storage initializes with empty data structures")
    
    def test_store_message_success(self):
        """Test 2: Store message successfully"""
        result = asyncio.run(self.storage.store_message("msg_001", "Hello World", "Alice"))
        self.assertTrue(result)
        
        # Verify message stored
        self.assertIn("msg_001", self.storage.messages)
        self.assertEqual(self.storage.messages["msg_001"]["content"], "Hello World")
        self.assertEqual(self.storage.messages["msg_001"]["sender"], "Alice")
        print("✓ Test 2 PASSED: Message stored successfully")
    
    def test_store_multiple_messages(self):
        """Test 3: Store multiple messages and verify order"""
        messages = [
            ("msg_001", "First message", "Alice"),
            ("msg_002", "Second message", "Bob"),
            ("msg_003", "Third message", "Charlie")
        ]
        
        for msg_id, content, sender in messages:
            asyncio.run(self.storage.store_message(msg_id, content, sender))
        
        self.assertEqual(len(self.storage.messages), 3)
        self.assertEqual(len(self.storage.message_index), 3)
        
        # Verify order
        self.assertEqual(self.storage.message_index[0], "msg_001")
        self.assertEqual(self.storage.message_index[1], "msg_002")
        self.assertEqual(self.storage.message_index[2], "msg_003")
        print("✓ Test 3 PASSED: Multiple messages stored in correct order")
    
    def test_retrieve_message_success(self):
        """Test 4: Retrieve existing message"""
        asyncio.run(self.storage.store_message("msg_001", "Test message", "Alice"))
        
        message = asyncio.run(self.storage.retrieve_message("msg_001"))
        self.assertIsNotNone(message)
        self.assertEqual(message["content"], "Test message")
        self.assertEqual(message["sender"], "Alice")
        self.assertIn("timestamp", message)
        print("✓ Test 4 PASSED: Message retrieved successfully")
    
    def test_retrieve_nonexistent_message(self):
        """Test 5: Retrieve non-existent message returns None"""
        message = asyncio.run(self.storage.retrieve_message("nonexistent"))
        self.assertIsNone(message)
        print("✓ Test 5 PASSED: Non-existent message returns None")
    
    def test_get_all_messages(self):
        """Test 6: Get all messages in order"""
        messages = [
            ("msg_001", "First", "Alice"),
            ("msg_002", "Second", "Bob"),
            ("msg_003", "Third", "Charlie")
        ]
        
        for msg_id, content, sender in messages:
            asyncio.run(self.storage.store_message(msg_id, content, sender))
        
        all_messages = asyncio.run(self.storage.get_all_messages())
        self.assertEqual(len(all_messages), 3)
        self.assertEqual(all_messages[0]["content"], "First")
        self.assertEqual(all_messages[1]["content"], "Second")
        self.assertEqual(all_messages[2]["content"], "Third")
        print("✓ Test 6 PASSED: All messages retrieved in correct order")
    
    def test_get_all_messages_empty(self):
        """Test 7: Get all messages when storage is empty"""
        all_messages = asyncio.run(self.storage.get_all_messages())
        self.assertEqual(len(all_messages), 0)
        self.assertIsInstance(all_messages, list)
        print("✓ Test 7 PASSED: Empty storage returns empty list")
    
    def test_delete_message_success(self):
        """Test 8: Delete existing message"""
        asyncio.run(self.storage.store_message("msg_001", "To be deleted", "Alice"))
        
        result = asyncio.run(self.storage.delete_message("msg_001"))
        self.assertTrue(result)
        self.assertNotIn("msg_001", self.storage.messages)
        self.assertNotIn("msg_001", self.storage.message_index)
        print("✓ Test 8 PASSED: Message deleted successfully")
    
    def test_delete_nonexistent_message(self):
        """Test 9: Delete non-existent message returns False"""
        result = asyncio.run(self.storage.delete_message("nonexistent"))
        self.assertFalse(result)
        print("✓ Test 9 PASSED: Deleting non-existent message returns False")
    
    def test_thread_safety_concurrent_writes(self):
        """Test 10: Thread-safe concurrent message storage"""
        results = []
        
        def store_messages(start_id):
            for i in range(5):
                msg_id = f"msg_{start_id}_{i}"
                result = asyncio.run(self.storage.store_message(msg_id, f"Message {i}", f"User{start_id}"))
                results.append(result)
        
        threads = [threading.Thread(target=store_messages, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All operations should succeed
        self.assertTrue(all(results))
        self.assertEqual(len(self.storage.messages), 15)  # 3 threads * 5 messages
        print(f"✓ Test 10 PASSED: Thread-safe storage, {len(self.storage.messages)} messages stored concurrently")
    
    def test_message_metadata(self):
        """Test 11: Messages contain correct metadata"""
        asyncio.run(self.storage.store_message("msg_001", "Test", "Alice"))
        
        message = asyncio.run(self.storage.retrieve_message("msg_001"))
        self.assertIn("message_id", message)
        self.assertIn("content", message)
        self.assertIn("sender", message)
        self.assertIn("timestamp", message)
        self.assertEqual(message["message_id"], "msg_001")
        print("✓ Test 11 PASSED: Message contains all required metadata")
    
    def test_update_existing_message(self):
        """Test 12: Update existing message (overwrite)"""
        asyncio.run(self.storage.store_message("msg_001", "Original", "Alice"))
        asyncio.run(self.storage.store_message("msg_001", "Updated", "Alice"))
        
        message = asyncio.run(self.storage.retrieve_message("msg_001"))
        self.assertEqual(message["content"], "Updated")
        # Should not duplicate in index
        self.assertEqual(self.storage.message_index.count("msg_001"), 1)
        print("✓ Test 12 PASSED: Message update works correctly")


def run_tests():
    """Run all tests and display results"""
    print("=" * 70)
    print("MEMBER 2: MESSAGE STORAGE COMPONENT - UNIT TEST SUITE")
    print("=" * 70)
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMessageStorageComponent)
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
