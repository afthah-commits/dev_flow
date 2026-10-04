class EmailProvider:
    def __init__(self, config: dict):
        self.config = config

    async def send_email(self, to: str, subject: str, body: str):
        # Mock implementation
        return {"ok": True}
