# tests/test_monitor.py
import pytest
from unittest.mock import patch, MagicMock
from mdparser.markdown_parser.monitor import PerformanceMonitor

def test_start_snapshot_sets_attributes():
    monitor = PerformanceMonitor()
    with patch("tracemalloc.start") as mock_tracemalloc_start, \
         patch("psutil.Process") as mock_process:
        monitor.start_snapshot()
        mock_tracemalloc_start.assert_called_once()
        mock_process.assert_called_once()
        # Перевіримо, що обʼєкт процесу збережено
        assert monitor._proc is not None
        # Перевіримо, що _t0 збережено
        assert hasattr(monitor, "_t0")

def test_stop_snapshot_returns_dict():
    monitor = PerformanceMonitor()
    mock_proc = MagicMock()
    mock_proc.cpu_percent.return_value = 10.0
    mock_proc.memory_info.return_value.rss = 123456
    monitor._proc = mock_proc
    monitor._t0 = 0

    with patch("time.time", return_value=1.0), \
         patch("tracemalloc.get_traced_memory", return_value=(111, 222)), \
         patch("tracemalloc.stop") as mock_tracemalloc_stop:
        result = monitor.stop_snapshot()

    assert isinstance(result, dict)
    assert result['duration'] == 1.0
    assert result['current_alloc'] == 111
    assert result['peak_alloc'] == 222
    assert result['cpu_percent'] == 10.0
    assert result['rss'] == 123456
    mock_tracemalloc_stop.assert_called_once()
    # Перевіримо, що запис додано в records
    assert monitor.records[-1] == result

def test_aggregate_with_no_records():
    monitor = PerformanceMonitor()
    assert monitor.aggregate() == {}

def test_aggregate_with_records():
    monitor = PerformanceMonitor()
    monitor.records = [
        {'duration': 1.0, 'current_alloc': 0, 'peak_alloc': 0, 'cpu_percent': 0, 'rss': 0},
        {'duration': 3.0, 'current_alloc': 0, 'peak_alloc': 0, 'cpu_percent': 0, 'rss': 0}
    ]
    result = monitor.aggregate()
    assert result['runs'] == 2
    assert result['total_time'] == 4.0
    assert result['avg_time'] == 2.0