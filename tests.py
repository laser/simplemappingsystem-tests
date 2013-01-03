#!/usr/bin/env python

import barrister
import logging

# disable debug logging
logging.getLogger("barrister").setLevel(logging.INFO)

# change this to point at wherever your server is running
trans = barrister.HttpTransport("http://localhost:3002/api-new")

# automatically connects to endpoint and loads IDL JSON contract
client = barrister.Client(trans)

class TestCase:
    def testCanGetUserSettings(self):
        r = client.SimpleMappingSystem.get_user_settings("test-1234")
        assert r["user_id"] == "test-1234", "%s != %s" % (r["user_id"], "test-1234",)

if __name__ == "__main__":
    obj = TestCase()
    obj.testCanGetUserSettings()
