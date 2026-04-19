import time

class EventTracker:
    def __init__(self):
        self.start_time = time.time()
        self.last_activity_time = time.time()

        self.idle_time = 0.0
        self.rewrite_count = 0
        self.backspace_count = 0
        self.skipped = 0

    def _update_idle(self):
        now = time.time()
        idle_gap = now - self.last_activity_time

        # silence threshold (tunable)
        if idle_gap > 1.5:
            self.idle_time += idle_gap

        self.last_activity_time = now

    def key_press(self, key):
        self._update_idle()

        if key == "BACKSPACE":
            self.backspace_count += 1

    def rewrite(self):
        self._update_idle()
        self.rewrite_count += 1

    def skip(self):
        self._update_idle()
        self.skipped = 1

    def snapshot(self):
        return {
            "time_taken": time.time() - self.start_time,
            "idle_time": self.idle_time,
            "rewrite_count": self.rewrite_count,
            "backspace_count": self.backspace_count,
            "skipped": self.skipped
        }