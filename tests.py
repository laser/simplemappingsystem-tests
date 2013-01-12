#!/usr/bin/env python

import barrister
import logging

# disable debug logging
logging.getLogger("barrister").setLevel(logging.INFO)

# change this to point at wherever your server is running
trans = barrister.HttpTransport("http://localhost:3002/api")

# automatically connects to endpoint and loads IDL JSON contract
client = barrister.Client(trans)

svc = client.SimpleMappingSystem

class TestCase:
    def __init__(self):
        self.pid = None
        self.uid = "test-1234"

    def setUp(self):
        r = svc.add_project(self.uid, "test-project")
        self.pid = r["project_id"]

    def tearDown(self):
        r = svc.get_projects(self.uid)
        for project in r:
            svc.delete_project(self.uid, project["project_id"])

    def testUserSettingsLifecycle(self):
        r = svc.get_user_settings(self.uid)
        assert r["user_id"] == self.uid

        svc.update_user_settings(self.uid, "EN_US", "DECIMAL", "IMPERIAL", "HYBRID")

        r = svc.get_user_settings(self.uid)
        assert r["user_id"] == self.uid
        assert r["default_language"] == "EN_US"
        assert r["default_gps_format"] == "DECIMAL"
        assert r["default_measurement_system"] == "IMPERIAL"
        assert r["default_google_map_type"] == "HYBRID"

    def testProjectLifecycle(self):
        r = svc.get_projects(self.uid)
        assert len(r) == 1

        r = svc.add_project(self.uid, "project-a")
        tmp_project_id = r["project_id"]
        assert "project_id" in r
        assert r["name"] == "project-a"

        r = svc.get_projects(self.uid)
        assert len(r) == 2

        svc.delete_project(self.uid, tmp_project_id)
        r = svc.get_projects(self.uid)
        assert len(r) == 1

    def testFieldLifeCycle(self):
        # basic "core" fields will be created along
        # with the project
        r = svc.get_position_fields(self.uid, self.pid, False, [])
        assert len(set([f["name"] for f in r]).intersection({"core_icon", "core_latitude", "core_longitude"})) == 3

        # add an additional field and stash the id
        r = svc.add_position_field(self.uid, self.pid, "STRING", "favorite_color")
        tmp_position_field_id = r["position_field_id"]

        # should now have four fields
        r = svc.get_position_fields(self.uid, self.pid, False, [])
        assert len(set([f["name"] for f in r]).intersection({"core_icon", "core_latitude", "core_longitude", "favorite_color"})) == 4

        # delete the custom one we created
        svc.delete_position_field(self.uid, tmp_position_field_id)

        # back to 3
        r = svc.get_position_fields(self.uid, self.pid, False, [])
        assert len(set([f["name"] for f in r]).intersection({"core_icon", "core_latitude", "core_longitude"})) == 3

    def testPositionLifecycle(self):
        # should have no position properties yet
        r = svc.search_positions(self.uid, self.pid, "")
        assert len(r) == 0

        # add a position to project, including a property
        # for the field just created
        r = svc.add_position(self.uid, self.pid, [{
            "name": "core_latitude",
            "value": "45"
        }])
        temp_position_id_a = r["position_id"]

        # should return back a position now
        r = svc.search_positions(self.uid, self.pid, "")
        assert r[0]["position_properties"][0]["name"] == "core_latitude"
        assert r[0]["position_properties"][0]["value"] == "45"

        # update the position, adding some properties and
        # updating the one previously-added
        svc.update_position(self.uid, temp_position_id_a, [{
            "name": "core_latitude",
            "value": "14"
        }, {
            "name": "core_longitude",
            "value": "16"
        }])

        # batch-add one more position (and properties)
        r = svc.add_positions(self.uid, self.pid, [{"position_properties":[{"name": "core_latitude", "value": "60"}, {"name": "core_longitude", "value": "60"}]}])
        temp_position_id_b = r[0]["position_id"]

        # should now have the one position we added
        r = svc.search_positions(self.uid, self.pid, "")
        assert len(r) == 2
        assert len(set([p["name"] for p in r[0]["position_properties"]]).intersection({"core_longitude", "core_latitude"})) == 2

        # delete positions we've added
        svc.delete_position(self.uid, temp_position_id_a)
        svc.delete_position(self.uid, temp_position_id_b)

        # should now be back to zero
        r = svc.search_positions(self.uid, self.pid, "")
        assert len(r) == 0

    def testProjectAccessLifecycle(self):
        # creating a project adds project access
        r = svc.add_project(self.uid, "test-project-access")
        new_project_id = r["project_id"]
        r = svc.get_project_access(self.uid, new_project_id)
        assert len(r) == 1
        assert r[0]["user_id"] == self.uid
        assert r[0]["access_type"] == "OWNER"
        owner_project_access_id = r[0]["project_access_id"]

        # add a public access row
        svc.add_project_access(self.uid, new_project_id, "PUBLIC", "EN_US", "METRIC", "DECIMAL", "HYBRID", "", [])
        svc.add_project_access(self.uid, new_project_id, "READONLY", "ES_LA", "METRIC", "DECIMAL", "HYBRID", "Welcome to the system", ["text@example.com"])

        # load the project_access for the project again and verify
        r2 = svc.get_project_access(self.uid, new_project_id)
        assert len(r2) == 3
        
        # delete the public and invited-user
        access_ids = filter(lambda x: x != owner_project_access_id, set(p["project_access_id"] for p in r2))
        for id in access_ids:
            svc.delete_project_access(self.uid, id)
        
        r = svc.get_project_access(self.uid, new_project_id)
        assert len(r) == 1
        
        
