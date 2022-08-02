import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../libbeat/tests/system'))

from beat.beat import TestCase


class BaseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.beat_name = "filebeat"
        cls.beat_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )


        super(BaseTest, cls).setUpClass()

    def get_registry(self):
        # Returns content of the registry file
        dotFilebeat = f'{self.working_dir}/registry'
        self.wait_until(cond=lambda: os.path.isfile(dotFilebeat))

        with open(dotFilebeat) as file:
            return json.load(file)

    def get_registry_entry_by_path(self, path):
        """
        Fetches the registry file and checks if an entry for the given path exists
        If the path exists, the state for the given path is returned
        If a path exists multiple times (which is possible because of file rotation)
        the most recent version is returned
        """
        registry = self.get_registry()

        tmp_entry = None

        # Checks all entries and returns the most recent one
        for entry in registry:
            if entry["source"] == path and (
                tmp_entry != None
                and tmp_entry["timestamp"] < entry["timestamp"]
                or tmp_entry is None
            ):
                tmp_entry = entry

        return tmp_entry
