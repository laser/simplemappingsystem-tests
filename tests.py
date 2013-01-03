class TestCase:
    def setup(self):
        x = 2

    def teardown(self):
        x = 1

    def test(self):
        assert 1 == 1

if __name__ == "__main__":
    obj = TestCase()
    obj.setup()
    obj.test()
    obj.teardown()
