import pytest
import main


class TestClass:
    def test_bit_rate(self):
        assert main.get_bit_rate_name_str(102400) == ".1"
        assert main.get_bit_rate_name_str(11 * 1024 * 1024) == "9"
        assert main.get_bit_rate_name_str(7 * 1024 * 1024) == "7"
        assert main.get_bit_rate_name_str(7 * 1024 * 1024 / 10) == ".7"

    def test_get_fps_name_str(self):
        assert main.get_fps_name_str(30, 1) == "30"
        assert main.get_fps_name_str(18, 1) == "18"
        assert main.get_fps_name_str(180, 1) == "a8"
        assert main.get_fps_name_str(280, 1) == "b8"
        assert main.get_fps_name_str(360, 1) == "c6"

    def test_get_width_height_name_str(self):
        assert main.get_width_height_name_str(3840, 2160) == "4K"
        assert main.get_width_height_name_str(2560, 1440) == "2K"
        assert main.get_width_height_name_str(1920, 1080) == "1080p"
        assert main.get_width_height_name_str(1280, 720) == "720p"
        assert main.get_width_height_name_str(1366, 768) == "768p"

        assert main.get_width_height_name_str(3842, 2160) == "4K"
        assert main.get_width_height_name_str(2562, 1440) == "2K"
        assert main.get_width_height_name_str(1922, 1080) == "1080p"
        assert main.get_width_height_name_str(1282, 720) == "720p"
        assert main.get_width_height_name_str(1368, 768) == "768p"

        assert main.get_width_height_name_str(709, 480) == "709*480"