from typing import List, Set
import fnmatch

class FilterManager:
    """
    Manages the list of entities to be monitored.
    Filters incoming state_changed events to reject high-volume noise.
    """
    def __init__(self, target_entities: List[str] = None):
        self.target_patterns: Set[str] = set(target_entities) if target_entities else set()
        self.exact_matches: Set[str] = set()
        self.glob_patterns: Set[str] = set()
        
        self._compile_patterns()

    def _compile_patterns(self):
        """Separate exact matches from glob patterns for optimization."""
        self.exact_matches.clear()
        self.glob_patterns.clear()
        
        for p in self.target_patterns:
            if '*' in p or '?' in p or '[' in p:
                self.glob_patterns.add(p)
            else:
                self.exact_matches.add(p)

    def update_targets(self, new_targets: List[str]):
        """Update the list of monitored entities."""
        self.target_patterns = set(new_targets)
        self._compile_patterns()

    def should_process(self, entity_id: str) -> bool:
        """
        Determine if an entity should be processed.
        O(1) lookups for exact matches.
        O(N) for glob patterns (where N is number of patterns).
        """
        if not entity_id:
            return False

        # Fast path: exact match
        if entity_id in self.exact_matches:
            return True

        # Slow path: glob patterns
        for pattern in self.glob_patterns:
            if fnmatch.fnmatch(entity_id, pattern):
                return True
                
        return False
