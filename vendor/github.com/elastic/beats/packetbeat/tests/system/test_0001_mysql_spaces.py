from packetbeat import BaseTest


class Test(BaseTest):

    def test_mysql_with_spaces(self):
        self.render_config_template(
            mysql_ports=[3306]
        )
        self.run_packetbeat(pcap="mysql_with_whitespaces.pcap",
                            debug_selectors=["mysql,tcp,publish"])

        objs = self.read_output()
        assert all(o["type"] == "mysql" for o in objs)
        assert len(objs) == 7
        assert all(o["port"] == 3306 for o in objs)

        assert objs[0]["method"] == "SET"
        assert objs[0]["path"] == ""
        assert objs[0]["status"] == "OK"

        assert objs[2]["method"] == "DROP"
        assert objs[2]["mysql.iserror"] is False
        assert objs[2]["status"] == "OK"

        assert objs[3]["method"] == "CREATE"
        assert objs[3]["mysql.iserror"] is False
        assert objs[3]["status"] == "OK"

        assert objs[5]["method"] == "SELECT"
        assert objs[5]["path"] == "test.test"
        assert objs[5]["status"] == "OK"
        assert objs[5]["bytes_out"] == 118

        assert all("bytes_in" in o.keys() for o in objs)
        assert all("bytes_out" in o.keys() for o in objs)
