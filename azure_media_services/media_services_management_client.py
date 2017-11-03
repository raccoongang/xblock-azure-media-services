# -*- coding: utf-8 -*-
import re

from msrestazure.azure_active_directory import ServicePrincipalCredentials
import requests


class MediaServicesManagementClient(object):

    def __init__(self, settings_azure):
        """
        Create a MediaServicesManagementClient instance.

        :param settings_azure: (dict) initialization parameters
        """
        self.rest_api_endpoint = settings_azure.pop('rest_api_endpoint')
        host = re.findall('[https|http]://(\w+.+)/api/', self.rest_api_endpoint, re.M)
        self.host = host[0] if host else None
        self.credentials = ServicePrincipalCredentials(**settings_azure)

    def get_list_locators_on_demand_origin(self):
        url = '{}Locators?$filter=Type eq 2'.format(self.rest_api_endpoint)
        headers = self.get_headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            locators = response.json().get('value', [])
            return locators
        else:
            response.raise_for_status()

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'DataServiceVersion': '1.0',
            'MaxDataServiceVersion': '3.0',
            'Accept': 'application/json',
            'Accept-Charset': 'UTF-8',
            'x-ms-version': '2.15',
            'Host': self.host,
            'Authorization': '{} {}'.format(self.credentials.token['token_type'],
                                            self.credentials.token['access_token'])
        }

    def get_files_for_asset(self, asset_id):
        url = "{}Assets('{}')/Files".format(self.rest_api_endpoint, asset_id)
        headers = self.get_headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            files = response.json().get('value', [])
            return files
        else:
            response.raise_for_status()

    def get_locator_sas_for_asset(self, asset_id):
        url = "{}Assets('{}')/Locators?$filter=Type eq 1".format(self.rest_api_endpoint, asset_id)
        headers = self.get_headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            locators = response.json().get('value', [])
            return locators[0] if locators else None
        else:
            response.raise_for_status()
