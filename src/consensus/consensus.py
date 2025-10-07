"""
Consensus Component - Manual Raft Implementation
Author: HITHUSH M IT23632264

This module provides a consensus interface using a manually implemented
Raft consensus algorithm. It replaces the third-party raftos library with
a custom implementation to demonstrate understanding of distributed consensus.

Key Features:
- Manual leader election with randomized timeouts
- Heartbeat-based leader maintenance
- Term-based voting system
- Thread-safe state management

References:
- Raft Paper: https://raft.github.io/raft.pdf
- Ongaro, D., & Ousterhout, J. (2014). In Search of an Understandable Consensus Algorithm
"""

from .raft_node import RaftNode
import threading
import time
import logging

logger = logging.getLogger("Consensus")


class Consensus:
    """
    Consensus manager using manual Raft implementation
    
    Provides backward-compatible API with the previous raftos-based implementation
    so that other components (storage, failover, server) don't need changes.
    """
    
    def __init__(self, cluster_nodes):
        """
        Initialize consensus manager
        
        Args:
            cluster_nodes (list): List of node addresses in 'host:port' format
        """
        self.cluster_nodes = cluster_nodes
        self.raft_node = None
        self.node_id = None
        self.leader = None
        self.is_leader = False
        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.monitor_interval = 0.5  # Check leadership every 500ms
        
        logger.info(f"Consensus manager initialized with {len(cluster_nodes)} nodes")
        logger.info(f"Using MANUAL Raft implementation (not raftos library)")
    
    def start_consensus(self, node_id=None):
        """
        Start consensus algorithm
        
        Args:
            node_id (str, optional): This node's address. If not provided, uses first node in cluster.
        """
        # Determine this node's ID
        if node_id:
            self.node_id = node_id
        elif self.cluster_nodes:
            # Default to first node if not specified
            self.node_id = self.cluster_nodes[0]
        else:
            raise ValueError("No node_id provided and cluster_nodes is empty")
        
        logger.info(f"Starting Raft consensus for node {self.node_id}")
        
        # Create and start Raft node
        self.raft_node = RaftNode(self.node_id, self.cluster_nodes)
        self.raft_node.start()
        
        # Start leadership monitoring
        self.monitor_thread = threading.Thread(target=self._monitor_leadership, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Consensus started successfully for {self.node_id}")
        return True
    
    def _monitor_leadership(self):
        """
        Monitor leadership status within the cluster
        Updates cached leader and is_leader status
        """
        while not self.stop_event.is_set():
            try:
                if self.raft_node:
                    # Get current leader from Raft node
                    current_leader = self.raft_node.get_leader()
                    current_is_leader = self.raft_node.is_leader()
                    
                    # Log changes
                    if current_leader != self.leader:
                        self.leader = current_leader
                        logger.info(f"Leader changed to: {self.leader}")
                    
                    if current_is_leader != self.is_leader:
                        self.is_leader = current_is_leader
                        if self.is_leader:
                            logger.info(f"✓ Node {self.node_id} is now the LEADER")
                        else:
                            logger.info(f"Node {self.node_id} is now a FOLLOWER")
            
            except Exception as e:
                logger.error(f"Error monitoring leadership: {e}")
            
            # Sleep before next check
            self.stop_event.wait(self.monitor_interval)
    
    def get_leader(self):
        """
        Get the current leader node
        
        Returns:
            str or None: Current leader address or None if no leader
        """
        return self.leader
    
    def is_this_node_leader(self):
        """
        Check if this node is the current leader
        
        Returns:
            bool: True if this node is the leader, False otherwise
        """
        return self.is_leader
    
    def get_cluster_size(self):
        """
        Get the number of nodes in the cluster
        
        Returns:
            int: Number of nodes in the cluster
        """
        return len(self.cluster_nodes)
    
    def get_quorum_size(self):
        """
        Get the minimum number of nodes required for quorum
        
        Returns:
            int: Minimum number of nodes required for quorum
        """
        return (len(self.cluster_nodes) // 2) + 1
    
    def get_status(self):
        """
        Get current consensus status
        
        Returns:
            dict: Status information including leader, term, state
        """
        if self.raft_node:
            state = self.raft_node.get_state()
            return {
                'leader': self.leader,
                'is_leader': self.is_leader,
                'self_id': self.node_id,
                'term': state.get('term', 0),
                'state': state.get('state', 'unknown'),
                'quorum': self.get_quorum_size(),
                'cluster_size': self.get_cluster_size()
            }
        return {
            'leader': None,
            'is_leader': False,
            'self_id': self.node_id,
            'quorum': self.get_quorum_size(),
            'cluster_size': self.get_cluster_size()
        }
    
    def stop(self):
        """Stop consensus monitoring"""
        logger.info("Stopping consensus monitoring")
        self.stop_event.set()
        
        # Stop Raft node
        if self.raft_node:
            self.raft_node.stop()
        
        # Stop monitoring thread
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("Consensus stopped")

