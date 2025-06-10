"""
Event sequence number management utilities.
"""

import threading

# Global sequence counter for event ordering
_sequence_counter = 0
_sequence_lock = threading.Lock()


def get_next_sequence_number() -> int:
    """Get the next sequence number for event ordering."""
    global _sequence_counter
    with _sequence_lock:
        _sequence_counter += 1
        return _sequence_counter


def reset_sequence_counter() -> None:
    """Reset the sequence counter. Only use in tests!"""
    global _sequence_counter
    with _sequence_lock:
        _sequence_counter = 0
