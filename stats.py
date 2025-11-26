import time
import threading
import datetime
from config import RATE_LIMIT_COUNT, RATE_LIMIT_PERIOD


class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = time.time()

        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.blocked = 0
        self.rate_limited = 0
        self.active_conns = 0

        self.logs = []

    def record_req(self):
        with self.lock: self.total_requests += 1

    def record_hit(self):
        with self.lock: self.cache_hits += 1

    def record_miss(self):
        with self.lock: self.cache_misses += 1

    def record_block(self):
        with self.lock: self.blocked += 1

    def record_limit(self):
        with self.lock: self.rate_limited += 1

    def update_conns(self, delta):
        with self.lock: self.active_conns += delta

    def add_log(self, ip, method, url, status, result):
        with self.lock:
            t = datetime.datetime.now().strftime("%H:%M:%S")
            self.logs.insert(0, {'t': t, 'ip': ip, 'm': method, 'u': url[:60], 's': status, 'r': result})
            if len(self.logs) > 20:
                self.logs.pop()

    def generate_html(self):
        uptime = str(datetime.timedelta(seconds=int(time.time() - self.start_time)))
        with self.lock:
            total_ops = self.cache_hits + self.cache_misses
            ratio = round((self.cache_hits / total_ops * 100), 1) if total_ops > 0 else 0

            rows = ""
            for l in self.logs:
                color = "green" if l['s'] == 200 else "red"
                if l['s'] == 304: color = "blue"
                rows += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding:8px;">{l['t']}</td>
                    <td style="padding:8px;">{l['ip']}</td>
                    <td style="padding:8px;"><b>{l['m']}</b></td>
                    <td style="padding:8px; font-family:monospace;">{l['u']}</td>
                    <td style="padding:8px; color:{color}; font-weight:bold;">{l['s']}</td>
                    <td style="padding:8px;">{l['r']}</td>
                </tr>"""

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Proxy Dashboard</title>
                <meta http-equiv="refresh" content="5">
                <style>
                    body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
                    .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }}
                    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
                    .stat-box {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px; border: 1px solid #e9ecef; }}
                    .stat-val {{ font-size: 24px; font-weight: bold; color: #333; }}
                    .stat-label {{ color: #666; font-size: 14px; }}
                    table {{ width: 100%; border-collapse: collapse; background: white; }}
                    th {{ text-align: left; padding: 10px; background: #343a40; color: white; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2 style="margin-top:0;">🚀 Proxy Server Monitor</h2>
                    <div class="grid">
                        <div class="stat-box"><div class="stat-val">{uptime}</div><div class="stat-label">Uptime</div></div>
                        <div class="stat-box"><div class="stat-val">{self.total_requests}</div><div class="stat-label">Total Requests</div></div>
                        <div class="stat-box"><div class="stat-val">{self.active_conns}</div><div class="stat-label">Active Threads</div></div>
                        <div class="stat-box"><div class="stat-val" style="color:green">{self.cache_hits}</div><div class="stat-label">Cache Hits</div></div>
                        <div class="stat-box"><div class="stat-val" style="color:orange">{self.cache_misses}</div><div class="stat-label">Cache Misses</div></div>
                        <div class="stat-box"><div class="stat-val" style="color:red">{self.blocked}</div><div class="stat-label">Blocked</div></div>
                    </div>
                    <p style="text-align:center; color:#888; margin-bottom:0;">Cache Efficiency: {ratio}% | Rate Limit: {RATE_LIMIT_COUNT}/{RATE_LIMIT_PERIOD}s</p>
                </div>

                <div class="card">
                    <h3>Recent Activity</h3>
                    <table>
                        <thead><tr><th>Time</th><th>IP</th><th>Method</th><th>URL</th><th>Status</th><th>Result</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
            </body>
            </html>
            """
            return html