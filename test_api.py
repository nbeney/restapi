import unittest

import requests
from flask import json

import api


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    def send(self, method, path, data=None, status_code=requests.codes.ok):
        response = method(path, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, status_code)
        return json.loads(response.get_data())

    def get(self, path, data=None, status_code=requests.codes.ok):
        return self.send(self.app.get, path, data, status_code)

    def post(self, path, data, status_code=requests.codes.ok):
        return self.send(self.app.post, path, data, status_code)

    def put(self, path, data, status_code=requests.codes.ok):
        return self.send(self.app.put, path, data, status_code)

    def delete(self, path, data=None, status_code=requests.codes.ok):
        return self.send(self.app.delete, path, data, status_code)


RESOURCE = 'Genre'
ID = 'GenreId'
NAME = 'Name'


# RESOURCE = 'MediaType'
# ID = 'MediaTypeId'
# NAME = 'Name'


def make_path(id=None):
    return '/' + RESOURCE + ('/{}'.format(id) if id else '')


def make_data(id=None, name=None):
    data = {}
    if id is not None:
        data[ID] = id
    if name is not None:
        data[NAME] = name
    return data


class TestFlaskApi(MyTestCase):
    def test_root(self):
        got = self.get('/')
        self.assertEqual(len(got), 10)

    def test_get_list(self):
        got = self.get(make_path())[RESOURCE]
        self.assertGreaterEqual(len(got), 2)

    def test_get_single(self):
        got = self.get(make_path(1))[RESOURCE][0]
        self.assertEqual(got[ID], 1)
        self.assertEqual(got[NAME], 'Rock' if RESOURCE == 'Genre' else 'MPEG audio file')

    def test_get_missing(self):
        got = self.get(make_path(12345), status_code=requests.codes.not_found)

    def test_get_csv(self):
        response = self.app.get('/Genre', headers={'Accept': 'text/csv'})
        self.assertEqual(response.status_code, requests.codes.ok)
        csv = response.get_data().decode('utf-8')
        lines = csv.split('\n')
        self.assertEqual(lines[0], 'GenreId,Name')
        self.assertGreaterEqual(len(lines), 25)

    def test_post_single(self):
        sent = make_data(None, 'Test1')
        got = self.post(make_path(), data=[sent])[RESOURCE][0]
        self.assertTrue(ID in got)
        self.assertEqual(got[NAME], sent[NAME])
        id_ = got[ID]

        got = self.get(make_path(id_))[RESOURCE][0]
        self.assertEqual(got[ID], id_)
        self.assertEqual(got[NAME], sent[NAME])

        got = self.delete(make_path(id_))

    def test_post_many(self):
        count_before = len(self.get(make_path())[RESOURCE])

        sent = [make_data(None, 'Test#{}'.format(_)) for _ in range(5)]
        got = self.post(make_path(), data=sent)[RESOURCE]
        self.assertEqual(len(got), len(sent))

        count_after = len(self.get(make_path())[RESOURCE])
        self.assertTrue(count_after - count_before, len(sent))

        for _ in got:
            self.delete(make_path(_[ID]))

    def test_put_single(self):
        sent = make_data(None, 'Test1-1')
        got = self.post(make_path(), data=[sent])[RESOURCE][0]
        id_ = got[ID]

        sent = make_data(id_, 'Test1-2')
        got = self.put(make_path(), data=sent)[RESOURCE][0]
        self.assertEqual(got[ID], id_)
        self.assertEqual(got[NAME], sent[NAME])

        got = self.get(make_path(id_))[RESOURCE][0]
        self.assertEqual(got[ID], id_)
        self.assertEqual(got[NAME], sent[NAME])

        got = self.delete(make_path(id_))

    def test_put_missing(self):
        sent = make_data(12345, 'Test1-2')
        got = self.put(make_path(), data=sent, status_code=requests.codes.not_found)

    def test_put_invalid(self):
        sent = make_data(None, 'Test1-2')
        got = self.put(make_path(), data=sent, status_code=requests.codes.internal_server_error)

    def test_delete_single(self):
        sent = make_data(None, 'Test3')
        got = self.post(make_path(), data=[sent])[RESOURCE][0]
        id_ = got[ID]

        got = self.delete(make_path(id_))[RESOURCE][0]
        self.assertEqual(got[ID], id_)
        self.assertEqual(got[NAME], sent[NAME])

        got = self.get(make_path(id_), status_code=requests.codes.not_found)

    def test_delete_missing(self):
        data = self.delete(make_path(12345), status_code=requests.codes.not_found)


if __name__ == '__main__':
    unittest.main()
