class SlackProvider:
    def __init__(self, token: str):
        self.token = token

    async def send_message(self, channel: str, text: str):
        # Mock implementation
        return {"ok": True, "message": text}
