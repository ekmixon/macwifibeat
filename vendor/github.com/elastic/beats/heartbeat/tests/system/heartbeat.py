import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../libbeat/tests/system'))

from beat.beat import TestCase


class BaseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.beat_name = "heartbeat"
        cls.beat_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )

        super(BaseTest, cls).setUpClass()
