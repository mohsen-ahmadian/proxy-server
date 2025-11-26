import datetime
import threading
from config import LOG_FILE


class Logger:
    def __init__(self):
        self.lock = threading.Lock()
        with open(LOG_FILE, "w", encoding='utf-8') as f:
            f.write(f"--- Log Started: {datetime.datetime.now()} ---\n")

    def log(self, client_ip, method, url, status_code, result):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {client_ip} | {method:<7} | {status_code} | {result:<15} | {url}"

        with self.lock:
            print(log_entry)
            try:
                with open(LOG_FILE, "a", encoding='utf-8') as f:
                    f.write(log_entry + "\n")
            except:
                pass