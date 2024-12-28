from time import time
from collections import defaultdict


class SpamProtection:
    def __init__(self, rate_limit=5, cooldown=60, max_warnings=3, warning_timeout=300):
        self.rate_limit = rate_limit  # Max messages per cooldown period
        self.cooldown = cooldown  # Cooldown period in seconds
        self.max_warnings = max_warnings  # Max warnings before ban
        self.warning_timeout = warning_timeout  # Warning reset time

        self.message_counts = defaultdict(list)  # {user: [timestamp, timestamp, ...]}
        self.warnings = defaultdict(int)  # {user: warning_count}
        self.banned_users = set()  # Set of banned user hashes
        self.warning_times = defaultdict(float)  # {user: last_warning_time}

    def check_spam(self, sender, current_time=None):
        if current_time is None:
            current_time = time()

        if sender in self.banned_users:
            return False, "You are banned for spam"

        # Clear old messages
        self.message_counts[sender] = [
            t for t in self.message_counts[sender] if current_time - t < self.cooldown
        ]

        # Check rate limit
        if len(self.message_counts[sender]) >= self.rate_limit:
            self.warnings[sender] += 1
            self.warning_times[sender] = current_time

            if self.warnings[sender] >= self.max_warnings:
                self.banned_users.add(sender)
                return False, "You have been banned for spam"

            return (
                False,
                f"Rate limit exceeded. Warning {self.warnings[sender]}/{self.max_warnings}",
            )

        # Add new message timestamp
        self.message_counts[sender].append(current_time)

        # Reset warnings if warning_timeout has passed
        if (current_time - self.warning_times.get(sender, 0)) > self.warning_timeout:
            self.warnings[sender] = 0

        return True, None

    def unban(self, sender):
        if sender in self.banned_users:
            self.banned_users.remove(sender)
            self.warnings[sender] = 0
            return True
        return False
