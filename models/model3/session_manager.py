from event_tracker import EventTracker

class SessionManager:
    def __init__(self, question_id):
        self.question_id = question_id
        self.tracker = EventTracker()

    def get_features(self):
        data = self.tracker.snapshot()
        data["question_id"] = self.question_id
        return data