import socket
import sys
from config import HOST, PORT, MAX_CONN
from logger import Logger
from filter_module import Filter
from cache import Cache
from stats import Stats
from proxy_handler import ProxyHandler

def main():
    logger = Logger()
    filter_obj = Filter()
    cache = Cache()
    stats = Stats()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_CONN)
        print(f"         Proxy Running on {HOST}:{PORT}")
        print("         Visit http://proxy-stats for Dashboard")
    except Exception as e:
        print(f"[!] Bind Error: {e}")
        sys.exit(1)

    try:
        while True:
            client, addr = server_socket.accept()
            handler = ProxyHandler(client, addr, logger, cache, filter_obj, stats)
            handler.daemon = True
            handler.start()
    except KeyboardInterrupt:
        print("\n          Stopping...")
        server_socket.close()

if __name__ == "__main__":
    main()