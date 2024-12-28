from time import time
from collections import defaultdict


class SpamProtection:
    def __init__(
        self, storage, rate_limit=5, cooldown=60, max_warnings=3, warning_timeout=300
    ):
        self.storage = storage
        self.rate_limit = rate_limit
        self.cooldown = cooldown
        self.max_warnings = max_warnings
        self.warning_timeout = warning_timeout
        self.load_data()

    def load_data(self):
        self.message_counts = self.storage.get("spam:message_counts", defaultdict(list))
        self.warnings = self.storage.get("spam:warnings", defaultdict(int))
        self.banned_users = set(self.storage.get("spam:banned_users", []))
        self.warning_times = self.storage.get("spam:warning_times", defaultdict(float))

    def save_data(self):
        self.storage.set("spam:message_counts", dict(self.message_counts))
        self.storage.set("spam:warnings", dict(self.warnings))
        self.storage.set("spam:banned_users", list(self.banned_users))
        self.storage.set("spam:warning_times", dict(self.warning_times))

    def check_spam(self, sender):
        if sender in self.banned_users:
            return False, "You are banned from using this bot."

        current_time = time()

        # Clean old messages
        self.message_counts[sender] = [
            t for t in self.message_counts[sender] if current_time - t <= self.cooldown
        ]

        # Check rate limit
        if len(self.message_counts[sender]) >= self.rate_limit:
            self.warnings[sender] += 1
            self.warning_times[sender] = current_time

            if self.warnings[sender] >= self.max_warnings:
                self.banned_users.add(sender)
                self.save_data()
                return False, "You have been banned for spamming."

            self.save_data()
            return (
                False,
                f"Rate limit exceeded. Warning {self.warnings[sender]}/{self.max_warnings}",
            )

        # Add new message timestamp
        self.message_counts[sender].append(current_time)

        # Reset warnings if warning_timeout has passed
        if (current_time - self.warning_times.get(sender, 0)) > self.warning_timeout:
            self.warnings[sender] = 0

        self.save_data()
        return True, None

    def unban(self, sender):
        if sender in self.banned_users:
            self.banned_users.remove(sender)
            self.warnings[sender] = 0
            return True
        return False
