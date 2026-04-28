import requests


class SlackNotifier:
    def __init__(self, webhook):
        self.webhook = webhook

    def send(self, message):
        if not self.webhook or "PUT_YOUR" in self.webhook:
            return

        try:
            requests.post(self.webhook, json={"text": message}, timeout=5)
        except Exception:
            pass
