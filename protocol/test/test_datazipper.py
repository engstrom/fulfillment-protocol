#!/usr/bin/python

import os
import unittest
from datazipper import DataZipper

class MockS3Object(object):
    def __init__(self, bucket, key):
        self.bucket = bucket
        self.key = key.replace("/", "_")
        self.filename = self._filename()

    def _filename(self):
        return "test/{}_{}.outons3butnotreally".format(self.bucket, self.key)

    def put(self, Body = None):
        self._reset()
        return open(self.filename, "w").write(Body)

    def get(self):
        return {"Body" : open(self.filename, "r")}

    def _reset(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

class MockS3(object):

    def Object(self, bucket, key):
        return MockS3Object(bucket, key)

class TestDataZipper(unittest.TestCase):

    def setUp(self):
        DataZipper.s3 = MockS3()

    def test_simple(self):
        self.assertEquals(DataZipper.deliver("Hello", 5000), "Hello")

    def test_zip(self):
        with open('test/bigTestData.json', 'r') as big_json_file:
            big_json = big_json_file.read()

            delivered = DataZipper.deliver(big_json, 30000)
            self.assertTrue(delivered.startswith('FF-ZIP:72686:eJy9vWt3W0eSJfp9fgVWzYeeu1ZlMd+P+dSUL'))

            received = DataZipper.receive(delivered)
            self.assertTrue(len(received) == 72686)

            self.assertTrue(received == big_json)

    def test_url(self):
        with open('test/biggerTestData.json', 'r') as bigger_json_file:
            bigger_json = bigger_json_file.read()

            delivered = DataZipper.deliver(bigger_json, 30000)
            self.assertTrue(delivered == "FF-URL:e5cc1ab85e5de887d3e20e8f04a2ea55:s3://balihoo.dev.fulfillment/retain_30_180/zipped-ff/e5cc1ab85e5de887d3e20e8f04a2ea55.ff")

            received = DataZipper.receive(delivered)
            self.assertTrue(len(received) == 394710)

            self.assertTrue(received == bigger_json)

if __name__ == '__main__':
    unittest.main()
