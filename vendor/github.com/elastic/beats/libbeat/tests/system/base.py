import os
from beat.beat import TestCase


class BaseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.beat_name = "mockbeat"
        cls.beat_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )

        cls.test_binary = f"{cls.beat_path}/libbeat.test"
        cls.beats = [
            "filebeat",
            "heartbeat",
            "metricbeat",
            "packetbeat",
            "winlogbeat",
        ]

        super(BaseTest, cls).setUpClass()
