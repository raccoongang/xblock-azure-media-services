import json
import unittest

from azure_media_services import AMSXBlock
from azure_media_services.utils import LANGUAGES

import mock

from xblock.field_data import DictFieldData


class AMSXBlockTests(unittest.TestCase):

    def make_one(self, **kw):
        """
        Create a XBlock AMS for testing purpose.
        """
        field_data = DictFieldData(kw)
        block = AMSXBlock(mock.Mock(), field_data, mock.Mock())
        block.location = mock.Mock(org='name_org')
        return block

    def test_default_fields_xblock(self):
        block = self.make_one()
        self.assertEqual(block.display_name, "Azure Media Services Video Player")
        self.assertEqual(block.video_url, '')
        self.assertEqual(block.verification_key, '')
        self.assertEqual(block.protection_type, '')
        self.assertEqual(block.token_issuer, 'http://openedx.microsoft.com/')
        self.assertEqual(block.token_scope, 'urn:xblock-azure-media-services')
        self.assertEqual(block.captions, [])
        self.assertEqual(block.transcripts_enabled, False)
        self.assertEqual(block.download_url, None)

    @mock.patch('azure_media_services.AMSXBlock.get_media_services')
    @mock.patch('azure_media_services.AMSXBlock.get_settings_azure', return_value=None)
    @mock.patch('azure_media_services.ams.loader.load_unicode', side_effect=('public/css/studio.css',
                                                                             'static/js/studio_edit.js'))
    @mock.patch('azure_media_services.ams.loader.render_django_template')
    @mock.patch('azure_media_services.ams.Fragment')
    def test_studio_view(self, fragment, render_django_template, load_unicode, get_settings_azure, get_media_services):
        """
        Test studio view is displayed correctly.
        """
        block = self.make_one()
        frag = block.studio_view({})

        get_media_services.assert_not_called()
        render_django_template.assert_called_once()

        template_arg = render_django_template.call_args[0][0]
        self.assertEqual(template_arg, 'templates/studio_edit.html')

        context = render_django_template.call_args[0][1]
        self.assertEqual(context['is_settings_azure'], False)
        self.assertEqual(context['list_stream_videos'], [])
        self.assertEqual(len(context['fields']), 9)
        self.assertEqual(context['languages'], LANGUAGES)

        frag.add_javascript.assert_called_once_with('static/js/studio_edit.js')
        frag.add_css.assert_called_once_with("public/css/studio.css")
        frag.initialize_js.assert_called_once_with("StudioEditableXBlockMixin")

    def test_get_settings_azure_for_organization(self):
        with mock.patch('azure_media_services.models.SettingsAzureOrganization.objects.filter',
                        return_value=mock.Mock(first=mock.Mock(
                            return_value=mock.Mock(organization='name_org',
                                                   client_id='client_id',
                                                   client_secret='client_secret',
                                                   tenant='tenant',
                                                   rest_api_endpoint='rest_api_endpoint')))):
            block = self.make_one()
            parameters = block.get_settings_azure()

            expected_parameters = {
                'client_id': 'client_id',
                'secret': 'client_secret',
                'tenant': 'tenant',
                'resource': 'https://rest.media.azure.net',
                'rest_api_endpoint': 'rest_api_endpoint'
            }
            self.assertEqual(parameters, expected_parameters)

    def test_get_settings_azure_for_platform(self):
        with mock.patch('azure_media_services.models.SettingsAzureOrganization.objects.filter',
                        return_value=mock.Mock(first=mock.Mock(return_value=None))):
            with mock.patch.dict('azure_media_services.ams.settings.FEATURES', {
                'AZURE_CLIENT_ID': 'client_id',
                'AZURE_CLIENT_SECRET': 'client_secret',
                'AZURE_TENANT': 'tenant',
                'AZURE_REST_API_ENDPOINT': 'rest_api_endpoint'
            }):
                block = self.make_one()
                parameters = block.get_settings_azure()

                expected_parameters = {
                    'client_id': 'client_id',
                    'secret': 'client_secret',
                    'tenant': 'tenant',
                    'resource': 'https://rest.media.azure.net',
                    'rest_api_endpoint': 'rest_api_endpoint'
                }
                self.assertEqual(parameters, expected_parameters)

    def test_when_not_set_settings_azure(self):
        with mock.patch('azure_media_services.models.SettingsAzureOrganization.objects.filter',
                        return_value=mock.Mock(first=mock.Mock(return_value=None))):
            with mock.patch.dict('azure_media_services.ams.settings.FEATURES', {}):
                block = self.make_one()
                parameters = block.get_settings_azure()
                self.assertEqual(parameters, None)

    @mock.patch('azure_media_services.ams.MediaServicesManagementClient')
    def test_get_media_services(self, media_services_management_client):
        block = self.make_one()
        media_services = block.get_media_services({})
        media_services_management_client.assert_called_once_with({})
        self.assertEqual(media_services, media_services_management_client())

    @mock.patch('azure_media_services.ams.AMSXBlock.get_media_services', return_value=mock.Mock(
        get_list_locators_on_demand_origin=mock.Mock(return_value=[{'AssetId': 'asset_id'}]),
        get_files_for_asset=mock.Mock(return_value=['file1', 'file2'])
    ))
    @mock.patch('azure_media_services.AMSXBlock.get_info_stream_video', return_value='info_stream_video')
    def test_get_list_stream_videos(self, get_info_stream_video, media_services):
        block = self.make_one()
        list_stream_videos = list(block.get_list_stream_videos({}))

        media_services.assert_called_once_with({})
        media_services().get_list_locators_on_demand_origin.assert_called_once_with()
        media_services().get_files_for_asset.assert_called_once_with('asset_id')
        get_info_stream_video.assert_called_once_with(['file1', 'file2'], {'AssetId': 'asset_id'})
        self.assertEqual(list_stream_videos, ['info_stream_video'])

    def test_get_info_stream_video(self):
        block = self.make_one()
        files = [
            {
                "Name": "fileNameIsmc.ismc",
                "MimeType": "application/octet-stream"
            },
            {
                "Name": "fileNameIsm.ism",
                "MimeType": "application/octet-stream"
            },
            {
                "Name": "fileName_320x180_320.mp4",
                "MimeType": "video/mp4"
            }]
        locator = {
            "Path": "http://account.streaming.mediaservices.windows.net/locator_id/",
            "AssetId": "asset_id"
        }
        info_stream_video = block.get_info_stream_video(files, locator)
        expected_info_stream_video = {
            'url_smooth_streaming': '//account.streaming.mediaservices.windows.net/locator_id/fileNameIsm.ism/manifest',
            'name_file': 'fileNameIsm.ism',
            'asset_id': 'asset_id',
        }

        self.assertDictEqual(info_stream_video, expected_info_stream_video)

    @mock.patch('azure_media_services.AMSXBlock.get_settings_azure', return_value={'settings_azure': 'settings_azure'})
    @mock.patch('azure_media_services.AMSXBlock.get_media_services', return_value=mock.Mock(
        get_locator_sas_for_asset=mock.Mock(return_value='locator'),
        get_files_for_asset=mock.Mock(return_value=['file1', 'file2'])
    ))
    @mock.patch('azure_media_services.AMSXBlock.get_captions_info_and_download_video_url',
                return_value=(['info_caption'], 'download_video_url'))
    def test_get_captions_and_download_video_url(self, get_captions_info_and_download_video_url,
                                                 get_media_services, get_settings_azure):
        block = self.make_one()
        captions_and_download_video_url = block.get_captions_and_download_video_url(
            mock.Mock(method="POST", body=json.dumps({'asset_id': 'asset_id'}))
        )

        get_settings_azure.assert_called_once_with()
        get_media_services.assert_called_once_with({'settings_azure': 'settings_azure'})
        media_services = get_media_services()
        media_services.get_locator_sas_for_asset.assert_called_once_with('asset_id')
        media_services.get_files_for_asset.assert_called_once_with('asset_id')
        get_captions_info_and_download_video_url.assert_called_once_with('locator', ['file1', 'file2'])
        expected_captions_and_download_video_url = {
            'captions': ['info_caption'],
            'download_video_url': 'download_video_url'
        }
        self.assertEqual(captions_and_download_video_url.json, expected_captions_and_download_video_url)

    @mock.patch('azure_media_services.AMSXBlock.get_settings_azure', return_value={'settings_azure': 'settings_azure'})
    @mock.patch('azure_media_services.AMSXBlock.get_media_services', return_value=mock.Mock(
        get_locator_sas_for_asset=mock.Mock(return_value=None)
    ))
    def test_get_captions_and_download_video_url_when_locator_does_not_exist(self, get_media_services,
                                                                             get_settings_azure):
        block = self.make_one()
        captions = block.get_captions_and_download_video_url(mock.Mock(method="POST",
                                                                       body=json.dumps({'asset_id': 'asset_id'})))

        get_settings_azure.assert_called_once_with()
        get_media_services.assert_called_once_with({'settings_azure': 'settings_azure'})
        media_services = get_media_services()
        media_services.get_locator_sas_for_asset.assert_called_once_with('asset_id')
        expected_error_message = {
            'result': 'error',
            'message': "To be able to use captions/transcripts auto-fetching, "
                       "AMS Asset should be published properly "
                       "(in addition to 'streaming' locator a 'progressive' "
                       "locator must be created as well)."
        }
        self.assertEqual(captions.json, expected_error_message)

    def test_get_captions_info_and_download_video_url(self):
        block = self.make_one()
        files = [
            {
                "Name": "caption1.vtt",
            },
            {
                "Name": "caption2.vtt",
            },
            {
                "Name": "fileName_1000.mp4",
                "ContentFileSize": "1000"
            },
            {
                "Name": "fileName_1001.mp4",
                "ContentFileSize": "1001"
            },
            {
                "Name": "fileName.mp4",
                "ContentFileSize": "size"
            }
        ]
        locator = {
            "Path": "https://storage.blob.core.windows.net/asset-id?sv=2015-07-08&sr=c&si=si"
        }
        info_captions = block.get_captions_info_and_download_video_url(locator, files)

        expected_info_captions = ([
            {
                'download_url': '//storage.blob.core.windows.net/asset-id/caption1.vtt?sv=2015-07-08&sr=c&si=si',
                'name_file': 'caption1.vtt'
            },
            {
                'download_url': '//storage.blob.core.windows.net/asset-id/caption2.vtt?sv=2015-07-08&sr=c&si=si',
                'name_file': 'caption2.vtt'
            }],
            '//storage.blob.core.windows.net/asset-id/fileName_1001.mp4?sv=2015-07-08&sr=c&si=si'
        )
        self.assertEqual(info_captions, expected_info_captions)
