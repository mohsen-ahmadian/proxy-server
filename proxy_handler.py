import socket
import threading
import select
from config import BUFFER_SIZE, SOCKET_TIMEOUT


class ProxyHandler(threading.Thread):
    def __init__(self, client_socket, client_addr, logger, cache, filter_obj, stats):
        super().__init__()
        self.client_socket = client_socket
        self.client_addr = client_addr
        self.client_ip = client_addr[0]
        self.logger = logger
        self.cache = cache
        self.filter = filter_obj
        self.stats = stats

    def run(self):
        self.stats.update_conns(1)
        try:
            self.client_socket.settimeout(SOCKET_TIMEOUT)
            try:
                request = self.client_socket.recv(BUFFER_SIZE)
            except:
                return

            if not request: return

            first_line_end = request.find(b'\n')
            if first_line_end == -1: return
            first_line = request[:first_line_end].decode('utf-8', errors='ignore').strip()

            try:
                method, url, _ = first_line.split(' ')
            except:
                return

            if "proxy-stats" in url:
                self.handle_stats_page()
                return

            self.stats.record_req()

            host, port = self.extract_host_port(request, url, method)

            if self.filter.is_rate_limited(self.client_ip):
                self.send_error(429, "Too Many Requests")
                self.logger.log(self.client_ip, method, url, 429, "RATE_LIMIT")
                self.stats.record_limit()
                self.stats.add_log(self.client_ip, method, url, 429, "RATE_LIMIT")
                return

            if self.filter.is_blocked(host):
                self.send_error(403, "Forbidden")
                self.logger.log(self.client_ip, method, url, 403, "BLOCKED")
                self.stats.record_block()
                self.stats.add_log(self.client_ip, method, url, 403, "BLOCKED")
                return

            if method == 'CONNECT':
                self.handle_https_tunnel(host, port)
                self.logger.log(self.client_ip, method, host, 200, "TUNNEL_OK")
                self.stats.add_log(self.client_ip, method, host, 200, "TUNNEL_OK")

            else:
                self.handle_http_request(method, url, host, port, request)

        except Exception as e:
            self.logger.log(self.client_ip, "ERROR", "-", 500, str(e))
        finally:
            self.stats.update_conns(-1)
            self.client_socket.close()

    def extract_host_port(self, request, url, method):
        host = None
        port = 80
        lines = request.decode('utf-8', errors='ignore').split('\r\n')
        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
                break
        if not host:
            if "://" in url:
                host = url.split("://")[1].split("/")[0]
            else:
                host = url.split("/")[0]
        if ":" in host:
            try:
                host, port_str = host.rsplit(":", 1)
                port = int(port_str)
            except:
                pass
        elif method == 'CONNECT':
            port = 443
        return host, port

    def handle_stats_page(self):
        html = self.stats.generate_html()
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html.encode('utf-8'))}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{html}"
        )
        self.client_socket.send(response.encode('utf-8'))

    def handle_https_tunnel(self, host, port):
        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            self.client_socket.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            inputs = [self.client_socket, remote]
            while True:
                readable, _, _ = select.select(inputs, [], [], 60)
                if not readable: break
                for sock in readable:
                    other = remote if sock is self.client_socket else self.client_socket
                    data = sock.recv(BUFFER_SIZE)
                    if not data:
                        remote.close()
                        return
                    other.send(data)
        except:
            pass

    def handle_http_request(self, method, url, host, port, request):
        cached_entry = self.cache.get(url)

        if cached_entry:
            is_fresh = self.check_conditional(host, port, url, cached_entry)
            if is_fresh:
                self.client_socket.send(cached_entry['data'])
                self.logger.log(self.client_ip, method, url, 200, "CACHE_HIT")
                self.stats.record_hit()
                self.stats.add_log(self.client_ip, method, url, 304, "CACHE_HIT")
                return
            else:
                self.logger.log(self.client_ip, method, url, 200, "CACHE_EXPIRED")

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            remote.send(request)

            data = b""
            while True:
                chunk = remote.recv(BUFFER_SIZE)
                if not chunk: break
                data += chunk
                self.client_socket.send(chunk)

            headers = self.parse_headers(data)
            self.cache.save(url, data, headers)

            self.logger.log(self.client_ip, method, url, 200, "CACHE_MISS")
            self.stats.record_miss()
            self.stats.add_log(self.client_ip, method, url, 200, "CACHE_MISS")

            remote.close()
        except Exception as e:
            self.send_error(502, str(e))

    def check_conditional(self, host, port, url, cached_entry):
        etag = cached_entry['headers'].get('ETag')
        lmod = cached_entry['headers'].get('Last-Modified')
        if not etag and not lmod: return False

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            path = url.replace(f"http://{host}", "") if f"http://{host}" in url else url

            req = f"HEAD {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n"
            if etag: req += f"If-None-Match: {etag}\r\n"
            if lmod: req += f"If-Modified-Since: {lmod}\r\n"
            req += "\r\n"

            remote.send(req.encode())
            resp = remote.recv(BUFFER_SIZE)
            remote.close()

            if b"304 Not Modified" in resp: return True
            return False
        except:
            return False

    def parse_headers(self, data):
        h = {}
        try:
            head = data.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
            for l in head.split('\r\n')[1:]:
                if ": " in l:
                    k, v = l.split(": ", 1)
                    h[k] = v
        except:
            pass
        return h

    def send_error(self, code, msg):
        resp = f"HTTP/1.1 {code} {msg}\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n{msg}"
        try:
            self.client_socket.send(resp.encode())
        except:
            pass