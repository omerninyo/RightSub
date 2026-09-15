import pytest
from importlib import import_module

adjust_module = import_module("06_adjust_fps_or_offset")
sync_module = import_module("02_web_search_and_sync")

class TestTimingAndSyncMath:
    def test_parse_and_format_time_roundtrip(self):
        t_str = "01:23:45,678"
        ms = adjust_module.parse_time(t_str)
        formatted = adjust_module.format_time(ms)
        assert formatted == t_str

    def test_offset_addition_and_subtraction(self):
        t_ms = adjust_module.parse_time("00:01:00,000") # 60,000 ms
        offset_positive = adjust_module.format_time(t_ms + 1500)
        assert offset_positive == "00:01:01,500"
        
        offset_negative = adjust_module.format_time(t_ms - 2000)
        assert offset_negative == "00:00:58,000"

    def test_fps_conversion_ratio(self):
        # 23.976 to 25.0 FPS stretches time by ratio 23.976 / 25.0 = 0.95904
        t_ms = 100000 # 100 seconds
        ratio = 23.976 / 25.0
        target_ms = int(t_ms * ratio)
        assert target_ms == 95904

    def test_zero_time_clamping(self):
        # Negative ms should be clamped to 00:00:00,000
        formatted = adjust_module.format_time(-500)
        assert formatted == "00:00:00,000"
