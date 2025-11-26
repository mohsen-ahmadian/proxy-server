
HOST = '127.0.0.1'
PORT = 8080
MAX_CONN = 100
BUFFER_SIZE = 8192
SOCKET_TIMEOUT = 15

CACHE_ENABLED = True
MAX_CACHE_ENTRIES = 100

LOG_FILE = "proxy_log.txt"

BLACKLIST = [
    "blocked.com",
    "bad-site.org",
    "ads.example.com"
]

RATE_LIMIT_COUNT = 50
RATE_LIMIT_PERIOD = 60