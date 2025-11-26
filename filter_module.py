import time
from config import BLACKLIST, RATE_LIMIT_COUNT, RATE_LIMIT_PERIOD


class Filter:
    def __init__(self):
        self.blacklist = BLACKLIST
        self.client_requests = {}

        self.RATE_LIMIT_COUNT = RATE_LIMIT_COUNT
        self.RATE_LIMIT_PERIOD = RATE_LIMIT_PERIOD

    def is_blocked(self, host):
        if not host: return False
        for domain in self.blacklist:
            if domain in host: return True
        return False

    def is_rate_limited(self, client_ip):
        current_time = time.time()
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []

        self.client_requests[client_ip] = [t for t in self.client_requests[client_ip]
                                           if current_time - t < RATE_LIMIT_PERIOD]

        if len(self.client_requests[client_ip]) >= RATE_LIMIT_COUNT:
            return True

        self.client_requests[client_ip].append(current_time)
        return False