from collections import deque
from typing import List, Optional

class BufferManager:
    """
    Optimized buffer manager using collections.deque for sliding window operations.
    Provides O(1) appends and pops.
    """
    def __init__(self, maxlen: int = 60):
        """
        Initialize the buffer.
        :param maxlen: Maximum size of the buffer (default 60 for 1-minute of 1s samples)
        """
        self._buffer = deque(maxlen=maxlen)

    def add(self, value: float) -> None:
        """Add a new value to the buffer, automatically evicting old ones."""
        self._buffer.append(value)

    def get_all(self) -> List[float]:
        """Return all current values in the buffer."""
        return list(self._buffer)

    def is_full(self) -> bool:
        """Check if buffer has reached capacity."""
        return len(self._buffer) == self._buffer.maxlen

    def clear(self) -> None:
        """Empty the buffer."""
        self._buffer.clear()

    @property
    def size(self) -> int:
        return len(self._buffer)
