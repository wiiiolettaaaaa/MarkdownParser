import time
import resource
try:
    from prometheus_client import Gauge, Counter
    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False

class PerfMonitor:
    def __init__(self, enable_prom=False):
        self.start_time = None
        self.end_time = None
        self.start_cpu = None
        self.end_cpu = None
        self.count = 0
        self.start_wall = time.time()
        self.enable_prom = enable_prom and PROM_AVAILABLE
        if self.enable_prom:
            # define simple metrics
            self.parse_time_gauge = Gauge('mdparser_parse_seconds', 'parse time seconds')
            self.requests_counter = Counter('mdparser_requests_total', 'total parse requests')

    def start(self):
        self.start_time = time.time()
        self.start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime

    def stop(self):
        self.end_time = time.time()
        self.end_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        self.count += 1
        if self.enable_prom:
            self.parse_time_gauge.set(self.end_time - self.start_time)
            self.requests_counter.inc()

    def rps(self):
        duration = time.time() - self.start_wall
        return self.count / duration if duration > 0 else None

    def report(self):
        wall = (self.end_time - self.start_time) if self.end_time and self.start_time else None
        cpu = (self.end_cpu - self.start_cpu) if self.end_cpu and self.start_cpu else None
        return {'wall_seconds': wall, 'cpu_seconds': cpu, 'requests_total': self.count, 'rps': self.rps()}