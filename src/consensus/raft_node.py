"""
Manual Raft Consensus Implementation
Author: ABEYRATHNA J G D A (IT23424432)

This module implements the Raft consensus algorithm from scratch.
Based on the Raft paper: "In Search of an Understandable Consensus Algorithm"
by Diego Ongaro and John Ousterhout (2014)

Key Features:
- Leader Election with randomized timeouts
- Heartbeat mechanism to maintain leadership
- Term-based voting to prevent split-brain
- Thread-safe state management

References:
- Raft Paper: https://raft.github.io/raft.pdf
- Raft Visualization: http://thesecretlivesofdata.com/raft/
"""

import threading
import time
import random
import socket
import json
import logging
from enum import Enum
from typing import List, Dict, Optional

logger = logging.getLogger("RaftNode")


class NodeState(Enum):
    """Raft node states"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class RaftNode:
    """
    Manual implementation of Raft consensus algorithm
    
    Implements:
    - Leader election with randomized timeouts (150-300ms)
    - Heartbeat mechanism (50ms intervals)
    - RequestVote RPC
    - AppendEntries RPC (heartbeats)
    - Term management for consistency
    """
    
    def __init__(self, node_id: str, cluster_nodes: List[str], rpc_port_offset: int = 1000):
        """
        Initialize Raft node
        
        Args:
            node_id: This node's address (e.g., "127.0.0.1:5000")
            cluster_nodes: List of all cluster node addresses
            rpc_port_offset: Offset to add to main port for RPC server (default: +1000)
        """
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        
        # RPC server port (main port + offset)
        # e.g., if node is 5000, RPC is on 6000
        main_port = int(node_id.split(':')[1])
        self.rpc_port = main_port + rpc_port_offset
        
        # Persistent state (would survive crashes in production)
        self.current_term = 0
        self.voted_for = None
        self.log = []  # List of log entries
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        self.state = NodeState.FOLLOWER
        
        # Leader state (only used when leader)
        self.next_index = {}
        self.match_index = {}
        
        # Election state
        self.election_timeout = self._random_election_timeout()
        self.last_heartbeat = time.time()
        self.votes_received = 0
        self.current_leader = None
        
        # Threading
        self.running = False
        self.lock = threading.RLock()  # Reentrant lock for nested calls
        self.election_thread = None
        self.heartbeat_thread = None
        self.rpc_server_thread = None
        self.rpc_server_socket = None
        
        logger.info(f"[RAFT] Node {self.node_id} initialized (RPC port: {self.rpc_port})")
    
    def _random_election_timeout(self) -> float:
        """
        Generate random election timeout
        
        Per Raft paper: 150-300ms recommended to prevent election conflicts
        Returns:
            float: Random timeout between 0.15 and 0.3 seconds
        """
        return random.uniform(0.15, 0.3)
    
    def start(self):
        """Start Raft consensus algorithm"""
        if self.running:
            logger.warning(f"[RAFT] Node {self.node_id} already running")
            return
        
        self.running = True
        self.last_heartbeat = time.time()
        
        # Start RPC server to handle incoming requests
        self.rpc_server_thread = threading.Thread(target=self._run_rpc_server, daemon=True)
        self.rpc_server_thread.start()
        
        # Start election timeout monitor
        self.election_thread = threading.Thread(target=self._election_timer, daemon=True)
        self.election_thread.start()
        
        logger.info(f"[RAFT] Node {self.node_id} started as FOLLOWER (term {self.current_term})")
    
    def stop(self):
        """Stop Raft consensus"""
        logger.info(f"[RAFT] Stopping node {self.node_id}")
        self.running = False
        
        # Close RPC server
        if self.rpc_server_socket:
            try:
                self.rpc_server_socket.close()
            except:
                pass
        
        # Wait for threads to finish
        threads = [self.election_thread, self.heartbeat_thread, self.rpc_server_thread]
        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=1)
        
        logger.info(f"[RAFT] Node {self.node_id} stopped")
    
    def _run_rpc_server(self):
        """
        Run RPC server to handle incoming Raft messages
        Listens for RequestVote and AppendEntries RPCs
        """
        try:
            self.rpc_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rpc_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.rpc_server_socket.bind(('0.0.0.0', self.rpc_port))
            self.rpc_server_socket.listen(5)
            self.rpc_server_socket.settimeout(1.0)  # Check running flag every second
            
            logger.info(f"[RAFT] RPC server listening on port {self.rpc_port}")
            
            while self.running:
                try:
                    client_sock, addr = self.rpc_server_socket.accept()
                    # Handle in separate thread
                    threading.Thread(
                        target=self._handle_rpc_request,
                        args=(client_sock,),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"[RAFT] RPC server error: {e}")
        
        except Exception as e:
            logger.error(f"[RAFT] Failed to start RPC server: {e}")
    
    def _handle_rpc_request(self, client_sock: socket.socket):
        """Handle incoming RPC request"""
        try:
            client_sock.settimeout(1.0)
            data = client_sock.recv(4096).decode().strip()
            
            if not data:
                return
            
            request = json.loads(data)
            rpc_type = request.get('type')
            
            response = {}
            if rpc_type == 'RequestVote':
                response = self._handle_request_vote(request)
            elif rpc_type == 'AppendEntries':
                response = self._handle_append_entries(request)
            else:
                response = {'error': 'Unknown RPC type'}
            
            client_sock.sendall((json.dumps(response) + '\n').encode())
        
        except Exception as e:
            logger.debug(f"[RAFT] Error handling RPC: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
    
    def _election_timer(self):
        """
        Monitor election timeout and trigger elections
        Core of the Raft election mechanism
        """
        while self.running:
            time.sleep(0.01)  # Check every 10ms
            
            with self.lock:
                # Leaders don't need election timeouts
                if self.state == NodeState.LEADER:
                    continue
                
                # Check if election timeout expired
                elapsed = time.time() - self.last_heartbeat
                if elapsed >= self.election_timeout:
                    logger.info(f"[RAFT] Node {self.node_id} election timeout ({elapsed:.2f}s), starting election")
                    self._start_election()
    
    def _start_election(self):
        """
        Start leader election
        
        Election process:
        1. Increment term
        2. Transition to candidate
        3. Vote for self
        4. Request votes from all other nodes
        5. If majority votes received, become leader
        """
        with self.lock:
            # Transition to candidate
            self.state = NodeState.CANDIDATE
            self.current_term += 1
            self.voted_for = self.node_id
            self.votes_received = 1  # Vote for self
            self.last_heartbeat = time.time()
            self.election_timeout = self._random_election_timeout()
            
            current_term = self.current_term
            
            logger.info(f"[RAFT] Node {self.node_id} starting election for term {current_term}")
        
        # Request votes from all other nodes (outside lock to prevent deadlock)
        for node in self.cluster_nodes:
            if node != self.node_id:
                threading.Thread(
                    target=self._request_vote,
                    args=(node, current_term),
                    daemon=True
                ).start()
    
    def _request_vote(self, target_node: str, term: int):
        """
        Send RequestVote RPC to target node
        
        Args:
            target_node: Address of node to request vote from
            term: Election term number
        """
        try:
            host, port = target_node.split(':')
            rpc_port = int(port) + 1000  # Target's RPC port
            
            # Create vote request
            request = {
                'type': 'RequestVote',
                'term': term,
                'candidate_id': self.node_id,
                'last_log_index': len(self.log) - 1,
                'last_log_term': self.log[-1]['term'] if self.log else 0
            }
            
            # Send request
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.15)  # 150ms timeout
                sock.connect((host, rpc_port))
                sock.sendall((json.dumps(request) + '\n').encode())
                
                # Receive response
                response_data = sock.recv(4096).decode().strip()
                if not response_data:
                    return
                
                response = json.loads(response_data)
                
                # Process vote response
                with self.lock:
                    # Ignore if we're no longer a candidate or term changed
                    if self.state != NodeState.CANDIDATE or self.current_term != term:
                        return
                    
                    if response.get('vote_granted'):
                        self.votes_received += 1
                        logger.info(f"[RAFT] Node {self.node_id} received vote from {target_node} "
                                  f"({self.votes_received}/{len(self.cluster_nodes)}) for term {term}")
                        
                        # Check if won election (majority)
                        quorum = len(self.cluster_nodes) // 2 + 1
                        if self.votes_received >= quorum:
                            self._become_leader()
                    
                    elif response.get('term', 0) > self.current_term:
                        # Another node has higher term, step down
                        logger.info(f"[RAFT] Node {self.node_id} found higher term {response['term']}, stepping down")
                        self._become_follower(response['term'])
        
        except Exception as e:
            logger.debug(f"[RAFT] Failed to request vote from {target_node}: {e}")
    
    def _become_leader(self):
        """
        Transition to leader state
        Only called when won election with majority votes
        """
        if self.state == NodeState.LEADER:
            return
        
        self.state = NodeState.LEADER
        self.current_leader = self.node_id
        
        # Initialize leader state
        for node in self.cluster_nodes:
            if node != self.node_id:
                self.next_index[node] = len(self.log)
                self.match_index[node] = 0
        
        logger.info(f"[RAFT] ✓ Node {self.node_id} became LEADER for term {self.current_term}")
        
        # Start sending heartbeats
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            # Stop old heartbeat thread if exists
            pass
        
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeats, daemon=True)
        self.heartbeat_thread.start()
    
    def _become_follower(self, term: int):
        """
        Transition to follower state
        
        Args:
            term: New term number
        """
        self.state = NodeState.FOLLOWER
        self.current_term = term
        self.voted_for = None
        self.last_heartbeat = time.time()
        logger.info(f"[RAFT] Node {self.node_id} became FOLLOWER (term {term})")
    
    def _send_heartbeats(self):
        """
        Send periodic heartbeats to all followers
        Heartbeats are empty AppendEntries RPCs
        """
        while self.running and self.state == NodeState.LEADER:
            # Send heartbeat to each follower
            for node in self.cluster_nodes:
                if node != self.node_id:
                    threading.Thread(
                        target=self._send_heartbeat,
                        args=(node,),
                        daemon=True
                    ).start()
            
            time.sleep(0.05)  # Send heartbeat every 50ms (well below election timeout)
    
    def _send_heartbeat(self, target_node: str):
        """
        Send heartbeat (empty AppendEntries) to follower
        
        Args:
            target_node: Address of follower node
        """
        try:
            host, port = target_node.split(':')
            rpc_port = int(port) + 1000
            
            with self.lock:
                request = {
                    'type': 'AppendEntries',
                    'term': self.current_term,
                    'leader_id': self.node_id,
                    'prev_log_index': len(self.log) - 1,
                    'prev_log_term': self.log[-1]['term'] if self.log else 0,
                    'entries': [],  # Empty = heartbeat
                    'leader_commit': self.commit_index
                }
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                sock.connect((host, rpc_port))
                sock.sendall((json.dumps(request) + '\n').encode())
                
                # Get response
                response_data = sock.recv(4096).decode().strip()
                if response_data:
                    response = json.loads(response_data)
                    
                    # Check if follower has higher term
                    with self.lock:
                        if response.get('term', 0) > self.current_term:
                            logger.info(f"[RAFT] Leader {self.node_id} found higher term, stepping down")
                            self._become_follower(response['term'])
        
        except Exception as e:
            logger.debug(f"[RAFT] Failed to send heartbeat to {target_node}: {e}")
    
    def _handle_request_vote(self, request: Dict) -> Dict:
        """
        Handle incoming RequestVote RPC
        
        Args:
            request: Vote request with term, candidate_id, log info
        
        Returns:
            dict: Response with vote_granted and current term
        """
        with self.lock:
            term = request['term']
            candidate_id = request['candidate_id']
            
            logger.debug(f"[RAFT] Node {self.node_id} received vote request from {candidate_id} (term {term})")
            
            # Reply false if term < currentTerm (§5.1)
            if term < self.current_term:
                logger.debug(f"[RAFT] Rejecting vote - old term {term} < {self.current_term}")
                return {'vote_granted': False, 'term': self.current_term}
            
            # If RPC request or response contains term T > currentTerm:
            # set currentTerm = T, convert to follower (§5.1)
            if term > self.current_term:
                logger.info(f"[RAFT] Node {self.node_id} updating term {self.current_term} -> {term}")
                self._become_follower(term)
            
            # Grant vote if:
            # 1. Haven't voted yet in this term, OR already voted for this candidate
            # 2. Candidate's log is at least as up-to-date as ours
            vote_granted = False
            if (self.voted_for is None or self.voted_for == candidate_id):
                # For simplicity, we grant vote (full implementation would check log up-to-date)
                self.voted_for = candidate_id
                self.last_heartbeat = time.time()
                self.election_timeout = self._random_election_timeout()
                vote_granted = True
                logger.info(f"[RAFT] Node {self.node_id} granted vote to {candidate_id} (term {term})")
            else:
                logger.debug(f"[RAFT] Node {self.node_id} already voted for {self.voted_for}")
            
            return {'vote_granted': vote_granted, 'term': self.current_term}
    
    def _handle_append_entries(self, request: Dict) -> Dict:
        """
        Handle incoming AppendEntries RPC (heartbeat or log replication)
        
        Args:
            request: AppendEntries request with term, leader_id, entries, etc.
        
        Returns:
            dict: Response with success status and current term
        """
        with self.lock:
            term = request['term']
            leader_id = request['leader_id']
            
            logger.debug(f"[RAFT] Node {self.node_id} received AppendEntries from {leader_id} (term {term})")
            
            # Reply false if term < currentTerm (§5.1)
            if term < self.current_term:
                logger.debug(f"[RAFT] Rejecting AppendEntries - old term {term} < {self.current_term}")
                return {'success': False, 'term': self.current_term}
            
            # Valid heartbeat/append entries from leader
            # Reset election timer
            self.last_heartbeat = time.time()
            self.election_timeout = self._random_election_timeout()
            
            # Update current leader
            if self.current_leader != leader_id:
                logger.info(f"[RAFT] Node {self.node_id} recognized leader: {leader_id}")
                self.current_leader = leader_id
            
            # If term is higher, update and become follower
            if term > self.current_term:
                self._become_follower(term)
            elif self.state != NodeState.FOLLOWER:
                # Same term but we're candidate/leader - become follower
                self.state = NodeState.FOLLOWER
                logger.info(f"[RAFT] Node {self.node_id} became FOLLOWER after receiving valid AppendEntries")
            
            return {'success': True, 'term': self.current_term}
    
    # Public API methods (used by Consensus class)
    
    def get_leader(self) -> Optional[str]:
        """
        Get current cluster leader
        
        Returns:
            str or None: Leader node address or None if no leader
        """
        with self.lock:
            return self.current_leader
    
    def is_leader(self) -> bool:
        """
        Check if this node is the current leader
        
        Returns:
            bool: True if this node is leader, False otherwise
        """
        with self.lock:
            return self.state == NodeState.LEADER
    
    def get_current_term(self) -> int:
        """
        Get current election term
        
        Returns:
            int: Current term number
        """
        with self.lock:
            return self.current_term
    
    def get_state(self) -> Dict:
        """
        Get current node state (for debugging/monitoring)
        
        Returns:
            dict: Current state information
        """
        with self.lock:
            return {
                'node_id': self.node_id,
                'state': self.state.value,
                'term': self.current_term,
                'leader': self.current_leader,
                'voted_for': self.voted_for,
                'votes_received': self.votes_received if self.state == NodeState.CANDIDATE else None,
                'cluster_size': len(self.cluster_nodes)
            }
