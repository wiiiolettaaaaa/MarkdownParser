# markdown_parser/monitor.py
import time
import tracemalloc
from typing import Dict, Any
import os
import psutil

class PerformanceMonitor:
    def __init__(self):
        self.records = []

    def start_snapshot(self):
        tracemalloc.start()
        self._t0 = time.time()
        self._proc = psutil.Process(os.getpid())

    def stop_snapshot(self) -> Dict[str, Any]:
        t1 = time.time()
        current, peak = tracemalloc.get_traced_memory()
        cpu = self._proc.cpu_percent(interval=0.1)
        mem = self._proc.memory_info().rss
        tracemalloc.stop()
        duration = t1 - self._t0
        rec = {'duration': duration, 'current_alloc': current, 'peak_alloc': peak, 'cpu_percent': cpu, 'rss': mem}
        self.records.append(rec)
        return rec

    def aggregate(self):
        if not self.records:
            return {}
        total_time = sum(r['duration'] for r in self.records)
        return {
            'runs': len(self.records),
            'total_time': total_time,
            'avg_time': total_time / len(self.records)
        }