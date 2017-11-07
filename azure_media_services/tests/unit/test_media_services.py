import unittest

import mock
from requests import HTTPError

from azure_media_services.media_services_management_client import MediaServicesManagementClient


class MediaServicesManagementClientTests(unittest.TestCase):

    @mock.patch('azure_media_services.media_services_management_client.ServicePrincipalCredentials')
    def make_one(self, service_principal_credentials):
        parameters = {
            'client_id': 'client_id',
            'secret': 'client_secret',
            'tenant': 'tenant',
            'resource': 'https://rest.media.azure.net',
            'rest_api_endpoint': 'https://rest_api_endpoint/api/'
        }
        media_services = MediaServicesManagementClient(parameters)
        media_services.credentials = mock.Mock(token={'token_type': 'token_type', 'access_token': 'access_token'})
        return media_services

    @mock.patch('azure_media_services.media_services_management_client.MediaServicesManagementClient.get_headers',
                return_value={})
    @mock.patch('azure_media_services.media_services_management_client.requests.get',
                return_value=mock.Mock(status_code=400, raise_for_status=mock.Mock(side_effect=HTTPError)))
    def raise_for_status(self, requests_get, headers, func, func_args=None):
        media_services = self.make_one()
        with self.assertRaises(HTTPError):
            if func_args:
                getattr(media_services, func)(func_args)
            else:
                getattr(media_services, func)()

    def test_get_headers(self):
        media_services = self.make_one()
        headers = media_services.get_headers()
        expected_headers = {
            'Content-Type': 'application/json',
            'DataServiceVersion': '1.0',
            'MaxDataServiceVersion': '3.0',
            'Accept': 'application/json',
            'Accept-Charset': 'UTF-8',
            'x-ms-version': '2.15',
            'Host': 'rest_api_endpoint',
            'Authorization': 'token_type access_token'
        }
        self.assertEqual(headers, expected_headers)

    @mock.patch('azure_media_services.media_services_management_client.MediaServicesManagementClient.get_headers',
                return_value={})
    @mock.patch('azure_media_services.media_services_management_client.requests.get',
                return_value=mock.Mock(status_code=200,
                                       json=mock.Mock(return_value={'value': ['locator1', 'locator2']})))
    def test_get_list_locators_on_demand_origin(self, requests_get, headers):
        media_services = self.make_one()
        locators = media_services.get_list_locators_on_demand_origin()
        requests_get.assert_called_once_with('https://rest_api_endpoint/api/Locators?$filter=Type eq 2', headers={})
        self.assertEqual(locators, ['locator1', 'locator2'])

    def test_raise_for_status_get_list_locators_on_demand_origin(self):
        self.raise_for_status(func='get_list_locators_on_demand_origin')

    @mock.patch('azure_media_services.media_services_management_client.MediaServicesManagementClient.get_headers',
                return_value={})
    @mock.patch('azure_media_services.media_services_management_client.requests.get',
                return_value=mock.Mock(status_code=200,
                                       json=mock.Mock(return_value={'value': ['locator']})))
    def test_get_locator_sas_for_asset(self, requests_get, headers):
        media_services = self.make_one()
        asset_id = 'asset_id'
        locator = media_services.get_locator_sas_for_asset(asset_id)
        requests_get.assert_called_once_with(
            "https://rest_api_endpoint/api/Assets('{}')/Locators?$filter=Type eq 1".format(asset_id),
            headers={}
        )
        self.assertEqual(locator, 'locator')

    def test_raise_for_status_get_locator_sas_for_asset(self):
        self.raise_for_status(func='get_locator_sas_for_asset', func_args='asset_id')

    @mock.patch('azure_media_services.media_services_management_client.MediaServicesManagementClient.get_headers',
                return_value={})
    @mock.patch('azure_media_services.media_services_management_client.requests.get',
                return_value=mock.Mock(status_code=200,
                                       json=mock.Mock(return_value={'value': ['file1', 'file2']})))
    def test_get_files_for_asset(self, requests_get, headers):
        media_services = self.make_one()
        asset_id = 'asset_id'
        files = media_services.get_files_for_asset(asset_id)
        requests_get.assert_called_once_with(
            "https://rest_api_endpoint/api/Assets('{}')/Files".format(asset_id),
            headers={}
        )
        self.assertEqual(files, ['file1', 'file2'])

    def test_raise_for_status_get_files_for_asset(self):
        self.raise_for_status(func='get_files_for_asset', func_args='asset_id')
