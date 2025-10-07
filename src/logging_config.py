"""
Custom Logging Configuration for Demo
Filters out verbose connection logs and highlights important events

Usage:
    from logging_config import setup_demo_logging
    setup_demo_logging()  # Call this once at startup
"""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Add colors to console output for better visibility"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[37m',       # White
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    # Highlight important events in GREEN
    IMPORTANT_KEYWORDS = [
        'LEADER', 'ELECTED', 'ELECTION', 'FAILED', 'RECOVERED', 
        'FAILOVER', 'CRASHED', 'REJOINED', 'MAJORITY', 'QUORUM'
    ]
    
    def format(self, record):
        # Check if this is an important message
        msg_upper = record.getMessage().upper()
        is_important = any(keyword in msg_upper for keyword in self.IMPORTANT_KEYWORDS)
        
        # Add color based on level or importance
        if is_important:
            color = '\033[32m'  # GREEN for important events
            prefix = '>>> '  # Simple prefix (no emojis for Windows compatibility)
        else:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            prefix = ''
        
        # Format the message
        formatted = super().format(record)
        
        return f"{color}{prefix}{formatted}{self.COLORS['RESET']}"


class ImportantOnlyFilter(logging.Filter):
    """Filter that only shows important messages in demo mode"""
    
    IMPORTANT_KEYWORDS = [
        # Leadership events
        'LEADER', 'ELECTED', 'ELECTION', 'BECAME', 'CANDIDATE', 'FOLLOWER',
        
        # Failure events
        'FAILED', 'CRASHED', 'DOWN', 'LOST', 'TIMEOUT', 'DISCONNECTED',
        
        # Recovery events
        'RECOVERED', 'REJOINED', 'RESTORED', 'SYNCED', 'RECONNECTED',
        
        # Consensus events
        'TERM', 'VOTE', 'HEARTBEAT TIMEOUT', 'QUORUM', 'MAJORITY',
        
        # Message events
        'MESSAGE STORED', 'MESSAGE REPLICATED', 'REPLICATION COMPLETE',
        
        # Cluster events
        'CLUSTER', 'NODE', 'FAILOVER', 'HEALTH CHECK FAILED',
        
        # Client events
        'CLIENT CONNECTED', 'CLIENT DISCONNECTED',
        
        # Startup/Shutdown
        'STARTING', 'STOPPING', 'INITIALIZED'
    ]
    
    # Suppress these boring messages
    SUPPRESS_PATTERNS = [
        'connection from',
        'connection closed',
        'sending heartbeat',
        'received heartbeat',
        'health check to',
        'still connected',
        'tcp connection'
    ]
    
    def filter(self, record):
        msg = record.getMessage().upper()
        
        # Suppress boring messages
        msg_lower = record.getMessage().lower()
        if any(pattern in msg_lower for pattern in self.SUPPRESS_PATTERNS):
            return False
        
        # Allow important messages
        if any(keyword in msg for keyword in self.IMPORTANT_KEYWORDS):
            return True
        
        # Allow WARNING and above always
        if record.levelno >= logging.WARNING:
            return True
        
        # Suppress everything else
        return False


def setup_demo_logging(verbose=False):
    """
    Setup logging for demo with clean, focused output
    
    Args:
        verbose (bool): If True, show all logs. If False, filter to important only.
    """
    
    # Remove existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s [%(name)-15s] %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add filter for demo mode
    if not verbose:
        console_handler.addFilter(ImportantOnlyFilter())
    
    # Configure root logger
    root.setLevel(logging.INFO)
    root.addHandler(console_handler)
    
    # Optional: Create a separate file for full logs
    file_handler = logging.FileHandler('full_system.log', mode='a')
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root.addHandler(file_handler)
    
    print("=" * 70)
    if verbose:
        print("VERBOSE MODE: Showing all logs")
    else:
        print("DEMO MODE: Showing only important events (full logs in full_system.log)")
    print("=" * 70)
    print()


def setup_standard_logging():
    """Setup standard logging (current behavior)"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
