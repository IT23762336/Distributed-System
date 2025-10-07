"""
Message Storage Component - Manual Replication
Author: W D S S JAYATHILAKA IT23582460

This module provides distributed message storage with replication.
Previously used raftos.ReplicatedDict, now uses manual replication
with Raft consensus integration.

Key Features:
- Thread-safe message storage
- Deduplication using unique message IDs
- Time-based message retrieval
- Storage statistics

Note: Full Raft log replication would be implemented in production.
For this assignment, we demonstrate the storage interface that works
with our manual Raft consensus implementation.
"""

import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("MessageStorage")


class MessageStorage:
    """
    Distributed message storage with manual replication
    
    Provides thread-safe storage for messages with deduplication.
    Integrates with manual Raft consensus for distributed consistency.
    """
    
    def __init__(self, raft_node=None):
        """
        Initialize message storage
        
        Args:
            raft_node: Optional RaftNode instance for consensus-based replication
        """
        # Local storage (in production, would be replicated via Raft log)
        self.messages = {}  # message_id -> message_json
        self.message_index = []  # Ordered list of message IDs
        
        # Thread synchronization
        self.storage_lock = threading.RLock()
        
        # Raft node for consensus (optional)
        self.raft_node = raft_node
        
        logger.info("MessageStorage initialized with manual replication")
        if raft_node:
            logger.info(f"Storage linked to Raft node: {raft_node.node_id}")
    
    async def store_message(self, message_id: str, message_json: str) -> bool:
        """
        Store a message in distributed storage
        
        Args:
            message_id: Unique identifier for the message
            message_json: JSON string representation of the message
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            # In production, would check if this node is leader
            # if self.raft_node and not self.raft_node.is_leader():
            #     logger.warning(f"Cannot store - not leader")
            #     return False
            
            with self.storage_lock:
                # Store message
                self.messages[message_id] = message_json
                
                # Add to index if not already there (deduplication)
                if message_id not in self.message_index:
                    self.message_index.append(message_id)
                
                logger.debug(f"Message stored with ID: {message_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error storing message: {e}")
            return False
    
    async def get_message(self, message_id: str) -> Optional[str]:
        """
        Retrieve a message by its ID
        
        Args:
            message_id: Unique identifier for the message
            
        Returns:
            str or None: The message JSON string if found, None otherwise
        """
        try:
            with self.storage_lock:
                return self.messages.get(message_id)
        except Exception as e:
            logger.error(f"Error retrieving message {message_id}: {e}")
            return None
    
    async def get_all_messages(self) -> List[Tuple[str, str]]:
        """
        Retrieve all messages from storage
        
        Returns:
            list: List of (message_id, message_json) tuples
        """
        try:
            result = []
            
            with self.storage_lock:
                # Get all messages from index
                for message_id in self.message_index:
                    message = self.messages.get(message_id)
                    if message:
                        result.append((message_id, message))
                    else:
                        logger.warning(f"Message {message_id} in index but not in storage")
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving all messages: {e}")
            return []
    
    async def get_messages_since(self, timestamp: float) -> List[Tuple[str, str]]:
        """
        Retrieve messages stored after a specific timestamp
        
        Args:
            timestamp: Unix timestamp to filter messages by
            
        Returns:
            list: List of (message_id, message_json) tuples
        """
        try:
            result = []
            
            with self.storage_lock:
                # Retrieve each message by ID and filter by timestamp
                for message_id in self.message_index:
                    # Extract timestamp from message ID format "timestamp_username_type"
                    try:
                        msg_timestamp = float(message_id.split('_')[0])
                        if msg_timestamp >= timestamp:
                            message = self.messages.get(message_id)
                            if message:
                                result.append((message_id, message))
                    except (ValueError, IndexError):
                        # Skip messages with invalid IDs
                        pass
            
            # Sort by timestamp (which is the first part of the message_id)
            result.sort(key=lambda x: x[0].split('_')[0])
            return result
        except Exception as e:
            logger.error(f"Error retrieving messages since {timestamp}: {e}")
            return []
    
    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message from storage
        
        Args:
            message_id: Unique identifier for the message
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self.storage_lock:
                # Delete the message from storage
                if message_id in self.messages:
                    del self.messages[message_id]
                
                # Remove from index
                if message_id in self.message_index:
                    self.message_index.remove(message_id)
                
                logger.debug(f"Message deleted: {message_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            return False
    
    async def get_message_count(self) -> int:
        """
        Get the total number of stored messages
        
        Returns:
            int: Number of messages in storage
        """
        try:
            with self.storage_lock:
                return len(self.message_index)
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            dict: Storage statistics including message count, oldest and newest timestamps
        """
        try:
            with self.storage_lock:
                if not self.message_index:
                    return {
                        "count": 0,
                        "oldest": None,
                        "newest": None
                    }
                
                timestamps = []
                for message_id in self.message_index:
                    try:
                        timestamp = float(message_id.split('_')[0])
                        timestamps.append(timestamp)
                    except (ValueError, IndexError):
                        pass
                
                if not timestamps:
                    return {
                        "count": len(self.message_index),
                        "oldest": None,
                        "newest": None
                    }
                
                oldest = min(timestamps)
                newest = max(timestamps)
                
                return {
                    "count": len(self.message_index),
                    "oldest": datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M:%S'),
                    "newest": datetime.fromtimestamp(newest).strftime('%Y-%m-%d %H:%M:%S')
                }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "count": 0,
                "oldest": None,
                "newest": None,
                "error": str(e)
            }

