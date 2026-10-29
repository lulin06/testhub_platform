import json
from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .importers import parse_collection
from .views import ApiRequestViewSet


class CollectionImportParserTests(SimpleTestCase):
    def test_preview_route_requires_post_and_parses_multipart_upload(self):
        document = {'openapi': '3.0.0', 'paths': {'/health': {'get': {'summary': 'Health'}}}}
        view = ApiRequestViewSet.as_view({'post': 'import_preview'})
        user = SimpleNamespace(is_authenticated=True, is_anonymous=False)
        factory = APIRequestFactory()
        request = factory.post(
            '/api/api-testing/requests/import-preview/',
            {'file': SimpleUploadedFile('openapi.json', json.dumps(document).encode())},
            format='multipart',
        )
        force_authenticate(request, user=user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        imported_item = response.data['groups'][0]['items'][0]
        self.assertEqual(imported_item['method'], 'GET')
        self.assertEqual(imported_item['name'], 'Health')
        self.assertEqual(imported_item['url'], '{{baseUrl}}/health')
        self.assertEqual(imported_item['path'], '/health')

        request = factory.get('/api/api-testing/requests/import-preview/')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEqual(response.status_code, 405)

    def test_openapi_v3_resolves_server_parameters_and_json_body(self):
        document = {
            'openapi': '3.0.3',
            'servers': [{'url': 'https://api.example.test/v1'}],
            'paths': {
                '/users/{userId}': {
                    'parameters': [{'name': 'userId', 'in': 'path'}],
                    'post': {
                        'summary': 'Update user', 'tags': ['Users'],
                        'parameters': [{'name': 'expand', 'in': 'query', 'example': 'profile'}],
                        'requestBody': {'content': {'application/json': {
                            'schema': {'type': 'object', 'properties': {'name': {'type': 'string'}}},
                        }}},
                    },
                },
            },
        }

        [item] = parse_collection(json.dumps(document).encode(), 'openapi.json')

        self.assertEqual(item['url'], '{{baseUrl}}/users/{userId}')
        self.assertEqual(item['params'], {'userId': '', 'expand': 'profile'})
        self.assertEqual(item['body'], {'type': 'json', 'data': {'name': ''}})
        self.assertEqual(item['group'], 'Users')

    def test_swagger_v2_body_parameter_is_imported(self):
        document = {
            'swagger': '2.0', 'host': 'api.example.test', 'schemes': ['https'],
            'basePath': '/v1', 'consumes': ['application/json'],
            'paths': {'/users': {'post': {
                'parameters': [{'name': 'user', 'in': 'body', 'schema': {
                    'type': 'object', 'properties': {'name': {'type': 'string'}},
                }}],
            }}},
        }

        [item] = parse_collection(json.dumps(document).encode(), 'swagger.json')

        self.assertEqual(item['url'], '{{baseUrl}}/users')
        self.assertEqual(item['headers']['Content-Type'], 'application/json')
        self.assertEqual(item['body']['data'], {'name': ''})

    def test_path_template_is_imported_even_without_parameter_declarations(self):
        document = {
            'openapi': '3.0.0',
            'servers': [{'url': 'https://release.example.test/api'}],
            'paths': {'/promotions/{merchantId}/{promotionId}/detail': {'get': {}}},
        }

        [item] = parse_collection(json.dumps(document).encode(), 'openapi.json')

        self.assertEqual(item['url'], '{{baseUrl}}/promotions/{merchantId}/{promotionId}/detail')
        self.assertEqual(item['params'], {'merchantId': '', 'promotionId': ''})

    def test_postman_collection_preserves_nested_folder_and_request_values(self):
        document = {
            'info': {'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
            'item': [{'name': 'Users', 'item': [{'name': 'Create user', 'request': {
                'method': 'POST', 'url': {'raw': '{{baseUrl}}/users', 'query': [
                    {'key': 'notify', 'value': 'true'},
                ]}, 'header': [{'key': 'Content-Type', 'value': 'application/json'}],
                'body': {'mode': 'raw', 'raw': '{"name":"Ada"}'},
            }}]}],
        }

        [item] = parse_collection(json.dumps(document).encode(), 'collection.json')

        self.assertEqual(item['group'], 'Users')
        self.assertEqual(item['method'], 'POST')
        self.assertEqual(item['url'], '{{baseUrl}}/users')
        self.assertEqual(item['params'], {'notify': 'true'})
        self.assertEqual(item['body'], {'type': 'json', 'data': {'name': 'Ada'}})

    def test_postman_builds_url_when_raw_value_is_missing(self):
        document = {
            'info': {'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
            'item': [{'name': 'List users', 'request': {
                'method': 'GET', 'url': {'host': ['{{baseUrl}}'], 'path': ['v1', 'users']},
            }}],
        }

        [item] = parse_collection(json.dumps(document).encode(), 'collection.json')

        self.assertEqual(item['url'], '{{baseUrl}}/v1/users')
        self.assertEqual(item['path'], '/v1/users')

    def test_rejects_unknown_document(self):
        with self.assertRaisesMessage(ValueError, '不支持的接口定义格式'):
            parse_collection(b'{"unexpected": true}', 'unknown.json')
