import json
import os
import unittest
import vcr as main_vcr
from shamrock import Shamrock, ENDPOINTS

TOKEN = os.environ.get('TREFLE_TOKEN')

vcr = main_vcr.VCR(cassette_library_dir='tests/cassettes')


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.api = Shamrock(TOKEN)

    def tearDown(self):
        pass

    def assertCommon(self, response, result, name):
        self.assertEqual(len(response), 1)
        self.assertEqual(response.requests[0].uri, 'https://trefle.io/api/{}'.format(name))
        self.assertTrue(isinstance(result, list))
        self.assertEqual(result, json.loads(response.responses[0]['body']['string']))

    def test__get_full_url(self):
        url = self.api._get_full_url('species')
        self.assertEqual(url, 'https://trefle.io/api/species')

    def test__kwargs(self):
        kwargs = self.api._kwargs('species')
        expected = {
            'url': 'https://trefle.io/api/species',
            'headers': {'Authorization': 'Bearer {}'.format(TOKEN)}
        }
        self.assertEqual(kwargs, expected)
        kwargs = self.api._kwargs('https://example.com')
        expected = {
            'url': 'https://example.com',
            'headers': {'Authorization': 'Bearer {}'.format(TOKEN)}
        }
        self.assertEqual(kwargs, expected)

    def test__get_parametrized_url(self):
        kwargs = {'url': 'https://example.com/'}
        result = self.api._get_parametrized_url(kwargs)
        self.assertEqual(result, kwargs['url'])
        kwargs['params'] = {'q': 'tomato'}
        result = self.api._get_parametrized_url(kwargs)
        self.assertEqual(result, '{}?q=tomato'.format(kwargs['url']) )

    def test__get_result(self):
        self.api.result = None
        kwargs = self.api._kwargs('species')
        with vcr.use_cassette('species.yaml', filter_headers=['Authorization']) as response:
            result = self.api._get_result(kwargs)
            self.assertCommon(response, result, 'species')
        with vcr.use_cassette('species.yaml', filter_headers=['Authorization']) as response:
            result = self.api._get_result(kwargs)
            self.assertCommon(response, result, 'species')
        kwargs = self.api._kwargs('plants')
        with vcr.use_cassette('plants.yaml', filter_headers=['Authorization']) as response:
            result = self.api._get_result(kwargs)
            self.assertCommon(response, result, 'plants')

    def test_ENDPOINTS(self):
        self.assertEqual(ENDPOINTS, (
            'kingdoms',
            'subkingdoms',
            'divisions',
            'families',
            'genuses',
            'plants',
            'species',
        ))

    def test_invalid_endpoint(self):
        invalid_endpoint = 'invalid_endpoint'
        self.assertTrue(invalid_endpoint not in ENDPOINTS)
        with self.assertRaises(AttributeError):
            getattr(self.api, invalid_endpoint)()

    def test_valid_endpoints(self):
        for endpoint in ENDPOINTS:
            with vcr.use_cassette('{}.yaml'.format(endpoint), filter_headers=['Authorization']) as response:
                result = getattr(self.api, endpoint)()
                self.assertCommon(response, result, endpoint)

    def test_valid_endpoint_one(self):
        with vcr.use_cassette('species_one.yaml', filter_headers=['Authorization']) as response:
            result = self.api.species(182512)
            self.assertEqual(len(response), 1)
            self.assertEqual(response.requests[0].uri, 'https://trefle.io/api/species/182512')
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(result, json.loads(response.responses[0]['body']['string']))

    def test_search(self):
        with vcr.use_cassette('search.yaml', filter_headers=['Authorization']) as response:
            result = self.api.search('tomato')
            self.assertEqual(len(response), 1)
            self.assertEqual(response.requests[0].uri, 'https://trefle.io/api/species?q=tomato')
            self.assertTrue(isinstance(result, list))
            self.assertEqual(result, json.loads(response.responses[0]['body']['string']))

    def test_next(self):
        with vcr.use_cassette('species.yaml', filter_headers=['Authorization']):
            self.api.species()
            self.assertIsNone(self.api.previous())
        with vcr.use_cassette('next.yaml', filter_headers=['Authorization']) as response:
            result = self.api.next()
            self.assertTrue(isinstance(result, list))
            self.assertEqual(response.requests[0].uri, 'http://trefle.io/api/species?page=2')

    def test_previous(self):
        with vcr.use_cassette('species.yaml', filter_headers=['Authorization']):
            self.api.species()
        with vcr.use_cassette('next.yaml', filter_headers=['Authorization']):
            self.api.next()
        with vcr.use_cassette('previous.yaml', filter_headers=['Authorization']) as response:
            result = self.api.previous()
            self.assertTrue(isinstance(result, list))
            self.assertEqual(response.requests[0].uri, 'http://trefle.io/api/species?page=1')
        with vcr.use_cassette('last.yaml', filter_headers=['Authorization']) as response:
            self.api.last()
            self.assertIsNone(self.api.next())

    def test_first(self):
        with vcr.use_cassette('species.yaml', filter_headers=['Authorization']):
            self.api.species()
        with vcr.use_cassette('first.yaml', filter_headers=['Authorization']) as response:
            self.api.first()

    def test_last(self):
        with vcr.use_cassette('species.yaml', filter_headers=['Authorization']):
            self.api.species()
        with vcr.use_cassette('last.yaml', filter_headers=['Authorization']):
            self.api.last()
            self.assertIsNone(self.api.next())

    def test_config(self):
        self.api = Shamrock(TOKEN, page_size=30)
        with vcr.use_cassette('species_config.yaml', filter_headers=['Authorization']) as response:
            result = self.api.species()
            self.assertEqual(len(response), 1)
            self.assertEqual(response.requests[0].uri, 'https://trefle.io/api/species?page_size=30')
            self.assertTrue(isinstance(result, list))
            self.assertEqual(result, json.loads(response.responses[0]['body']['string']))
        with vcr.use_cassette('search_config.yaml', filter_headers=['Authorization']) as response:
            result = self.api.search('tomato')
            self.assertEqual(len(response), 1)
            self.assertEqual(response.requests[0].uri, 'https://trefle.io/api/species?page_size=30&q=tomato')
            self.assertTrue(isinstance(result, list))
            self.assertEqual(result, json.loads(response.responses[0]['body']['string']))
