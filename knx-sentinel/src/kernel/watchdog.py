import time
import logging
from typing import Dict, List, Set, Callable

logger = logging.getLogger(__name__)

class WatchdogKernel:
    """
    Monitors a set of 'heartbeat' entities.
    If an entity hasn't reported a value ('on' or 1.0) within `timeout` seconds,
    it triggers a callback (e.g., to publish a '0' via MQTT).
    """

    def __init__(self, entities: List[str], timeout: int = 70):
        self.monitored_entities: Set[str] = set(entities)
        self.timeout = timeout
        
        # Track last "on" time: {entity_id: timestamp}
        self.last_seen: Dict[str, float] = {}
        
        # Track if we are currently in ALARM state for an entity
        # to avoid spamming the "0" message every second.
        # {entity_id: bool_is_in_alarm}
        self.alarm_state: Dict[str, bool] = {}

    def process_state(self, entity_id: str, value: float):
        """
        Update the heartbeat for an entity if the value indicates 'alive' (1.0).
        """
        if entity_id not in self.monitored_entities:
            return

        # If value is > 0.5 (i.e. roughly 1.0 or 'on'), we consider it a heartbeat.
        # If value is 0.0, that might be an explicit 'death' signal, but usually
        # heartbeats are just periodic pulses of 1.
        if value > 0.5:
            self.last_seen[entity_id] = time.time()
            if self.alarm_state.get(entity_id, False):
                 logger.info(f"Watchdog: Entity {entity_id} RECOVERED.")
            self.alarm_state[entity_id] = False

    def check_timeouts(self, on_timeout: Callable[[str], None]):
        """
        Check all monitored entities. If any have timed out, call the callback.
        Should be called periodically (e.g. every 5-10s).
        """
        now = time.time()
        
        for entity in self.monitored_entities:
            # If we've never seen it, initialize to now to give it a chance to start
            if entity not in self.last_seen:
                self.last_seen[entity] = now
            
            last = self.last_seen[entity]
            if (now - last) > self.timeout:
                # TIMEOUT DETECTED
                if not self.alarm_state.get(entity, False):
                    # We are entering ALARM state
                    logger.warning(f"Watchdog: Entity {entity} TIMED OUT (> {self.timeout}s). Publishing '0'.")
                    self.alarm_state[entity] = True
                    on_timeout(entity)
