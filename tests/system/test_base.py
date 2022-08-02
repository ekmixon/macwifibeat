from macwifibeat import BaseTest

import os


class Test(BaseTest):

    def test_base(self):
        """
        Basic test with exiting Macwifibeat normally
        """
        self.render_config_template(path=f"{os.path.abspath(self.working_dir)}/log/*")

        macwifibeat_proc = self.start_beat()
        self.wait_until(lambda: self.log_contains("macwifibeat is running"))
        exit_code = macwifibeat_proc.kill_and_wait()
        assert exit_code == 0
