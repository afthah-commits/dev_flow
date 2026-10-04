class CalendarProvider:
    def __init__(self, token: str):
        self.token = token

    async def create_event(self, summary: str, start_time: str, end_time: str):
        # Mock implementation
        return {"ok": True, "event_id": "mock_event_id"}
