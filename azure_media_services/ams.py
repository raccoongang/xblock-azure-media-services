# -*- coding: utf-8 -*-
"""
Copyright (c) Microsoft Corporation. All Rights Reserved.

Licensed under the MIT license. See LICENSE file on the project webpage for details.

XBlock to allow for video playback from Azure Media Services
Built using documentation from: http://amp.azure.net/libs/amp/latest/docs/index.html
"""
import logging

from django.conf import settings
import requests

from xblock.core import List, Scope, String, XBlock
from xblock.fields import Boolean
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from .media_services_management_client import MediaServicesManagementClient
from .models import SettingsAzureOrganization
from .utils import _, LANGUAGES


log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# According to edx-platform vertical xblocks
CLASS_PRIORITY = ['video']


@XBlock.needs('i18n')
class AMSXBlock(StudioEditableXBlockMixin, XBlock):
    """
    The xBlock to play videos from Azure Media Services.
    """

    RESOURCE = 'https://rest.media.azure.net'

    display_name = String(
        display_name=_("Display Name"),
        help=_(
            "Enter the name that students see for this component. "
            "Analytics reports may also use the display name to identify this component."
        ),
        scope=Scope.settings,
        default=_("Azure Media Services Video Player"),
    )
    video_url = String(
        display_name=_("Video Url"),
        help=_(
            "Enter the URL to your published video on Azure Media Services"
        ),
        default="",
        scope=Scope.settings
    )
    # Ultimately this should come via some secure means, but this is OK for a PoC
    verification_key = String(
        display_name=_("Verification Key"),
        help=_(
            "Enter the Base64 encoded Verification Key from your Azure Management Portal"
        ),
        default="",
        scope=Scope.settings
    )
    protection_type = String(
        display_name=_("Protection Type"),
        help=_(
            "This can be either blank (meaning unprotected), 'AES', or 'PlayReady'"
        ),
        default="",
        scope=Scope.settings
    )
    token_issuer = String(
        display_name=_("Token Issuer"),
        help=_(
            "This value must match what is in the 'Content Protection' area of the Azure Media Services portal"
        ),
        default="http://openedx.microsoft.com/",
        scope=Scope.settings
    )
    token_scope = String(
        display_name=_("Token Scope"),
        help=_(
            "This value must match what is in the 'Content Protection' area of the Azure Media Services portal"
        ),
        default="urn:xblock-azure-media-services",
        scope=Scope.settings
    )
    captions = List(
        display_name=_("Captions"),
        help=_("A list of caption definitions"),
        scope=Scope.settings
    )
    transcripts_enabled = Boolean(
        display_name=_("Transcripts enabled"),
        help=_("Transcripts switch"),
        default=False,
        scope=Scope.settings
    )
    download_url = String(
        display_name=_("Video Download URL"),
        help=_("A download URL"),
        scope=Scope.settings
    )

    # These are what become visible in the Mixin editor
    editable_fields = (
        'display_name', 'video_url', 'verification_key', 'protection_type',
        'token_issuer', 'token_scope', 'captions', 'transcripts_enabled', 'download_url',
    )

    def studio_view(self, context):
        """
        Render a form for editing this XBlock.
        """
        settings_azure = self.get_settings_azure()
        list_stream_videos = []

        if settings_azure:
            list_stream_videos = self.get_list_stream_videos(settings_azure)
        context = {
            'fields': [],
            'is_settings_azure': settings_azure is not None,
            'list_stream_videos': list_stream_videos,
            'languages': LANGUAGES
        }
        fragment = Fragment()
        # Build a list of all the fields that can be edited:
        for field_name in self.editable_fields:
            field = self.fields[field_name]
            assert field.scope in (Scope.content, Scope.settings), (
                "Only Scope.content or Scope.settings fields can be used with "
                "StudioEditableXBlockMixin. Other scopes are for user-specific data and are "
                "not generally created/configured by content authors in Studio."
            )
            field_info = self._make_field_info(field_name, field)
            if field_info is not None:
                context["fields"].append(field_info)
        fragment.content = loader.render_django_template('templates/studio_edit.html', context)
        fragment.add_css(loader.load_unicode('public/css/studio.css'))
        fragment.add_javascript(loader.load_unicode('static/js/studio_edit.js'))
        fragment.initialize_js('StudioEditableXBlockMixin')
        return fragment

    def _get_context_for_template(self):
        """
        Add parameters for the student view.
        """
        context = {
            "video_url": self.video_url,
            "protection_type": self.protection_type,
            "captions": self.captions,
            "transcripts_enabled": self.transcripts_enabled,
            "download_url": self.download_url,
        }

        if self.protection_type:
            context.update({
                "auth_token": self.verification_key,
            })

        return context

    def student_view(self, context):
        """
        Student view of this component.

        Arguments:
            context (dict): XBlock context

        Returns:
            xblock.fragment.Fragment: XBlock HTML fragment

        """
        fragment = Fragment()
        context.update(self._get_context_for_template())
        fragment.add_content(loader.render_django_template('/templates/player.html', context))

        '''
        Note: DO NOT USE the "latest" folder in production, but specify a version
                from https://aka.ms/ampchangelog . This allows us to run a test
                pass prior to ingesting later versions.
        '''
        fragment.add_javascript(loader.load_unicode('node_modules/videojs-vtt.js/lib/vttcue.js'))

        fragment.add_css_url('//amp.azure.net/libs/amp/1.8.1/skins/amp-default/azuremediaplayer.min.css')
        fragment.add_javascript_url('//amp.azure.net/libs/amp/1.8.1/azuremediaplayer.min.js')

        fragment.add_javascript(loader.load_unicode('static/js/player.js'))

        fragment.add_css(loader.load_unicode('public/css/player.css'))

        # NOTE: The Azure Media Player JS file includes the VTT JavaScript library, so we don't
        # actually need to include our local copy of public/js/vendor/vtt.js. In fact, if we do
        # the overlay subtitles stop working

        # @TODO: Make sure all fields are well structured/formatted, if it is not correct, then
        # print out an error msg in view rather than just silently failing

        fragment.initialize_js('AzureMediaServicesBlock')
        return fragment

    # xblock runtime navigation tab video image
    def get_icon_class(self):
        """
        Return the highest priority icon class.
        """
        child_classes = set(child.get_icon_class() for child in self.get_children())
        new_class = 'video'
        for higher_class in CLASS_PRIORITY:
            if higher_class in child_classes:
                new_class = higher_class
        return new_class

    def get_settings_azure(self):
        parameters = None
        settings_azure = SettingsAzureOrganization.objects.filter(organization__short_name=self.location.org).first()
        if settings_azure:
            parameters = {
                'client_id': settings_azure.client_id,
                'secret': settings_azure.client_secret,
                'tenant': settings_azure.tenant,
                'resource': self.RESOURCE,
                'rest_api_endpoint': settings_azure.rest_api_endpoint
            }
        elif (settings.FEATURES.get('AZURE_CLIENT_ID') and
              settings.FEATURES.get('AZURE_CLIENT_SECRET') and
              settings.FEATURES.get('AZURE_TENANT') and
              settings.FEATURES.get('AZURE_REST_API_ENDPOINT')):
            parameters = {
                'client_id': settings.FEATURES.get('AZURE_CLIENT_ID'),
                'secret': settings.FEATURES.get('AZURE_CLIENT_SECRET'),
                'tenant': settings.FEATURES.get('AZURE_TENANT'),
                'resource': self.RESOURCE,
                'rest_api_endpoint': settings.FEATURES.get('AZURE_REST_API_ENDPOINT')
            }
        return parameters

    def get_media_services(self, settings_azure):
        return MediaServicesManagementClient(settings_azure)

    def get_list_stream_videos(self, settings_azure):
        media_services = self.get_media_services(settings_azure)
        locators = media_services.get_list_locators_on_demand_origin()
        for locator in locators:
            files = media_services.get_files_for_asset(locator.get('AssetId'))
            yield self.get_info_stream_video(files, locator)

    def get_info_stream_video(self, files, locator):
        name_file = ''
        for file in files:
            if file.get('MimeType', '') == 'application/octet-stream' and file.get('Name', '').endswith('.ism'):
                name_file = file['Name'].encode('utf-8')
                break
        path = locator.get('Path').split(':', 1)[-1]
        return {
            'url_smooth_streaming': '{}{}/manifest'.format(path, name_file),
            'name_file': name_file,
            'asset_id': locator.get('AssetId')
        }

    def get_info_captions(self, locator, files):
        data = []
        path = locator.get('Path').split(':', 1)[-1]
        for file in files:
            if file.get('Name', '').endswith('.vtt'):
                name_file = file['Name'].encode('utf-8')
                download_url = '/{}?'.format(name_file).join(path.split('?'))
                data.append({
                    'download_url': download_url,
                    'name_file': name_file,
                })

        return data

    # Xblock handlers:
    @XBlock.json_handler
    def get_captions(self, data, suffix=''):
        asset_id = data.get('asset_id')
        settings_azure = self.get_settings_azure()
        media_services = self.get_media_services(settings_azure)
        locator = media_services.get_locator_sas_for_asset(asset_id)
        if locator:
            files = media_services.get_files_for_asset(asset_id)
            return self.get_info_captions(locator, files)

        return {'result': 'error',
                'message': _("To be able to use captions/transcripts auto-fetching, "
                             "AMS Asset should be published properly "
                             "(in addition to 'streaming' locator a 'progressive' "
                             "locator must be created as well).")}

    @XBlock.json_handler
    def publish_event(self, data, suffix=''):
        try:
            event_type = data.pop('event_type')
        except KeyError:
            return {'result': 'error', 'message': _('Missing event_type in JSON data')}

        data['video_url'] = self.video_url
        data['user_id'] = self.scope_ids.user_id

        self.runtime.publish(self, event_type, data)
        return {'result': 'success'}

    @XBlock.json_handler
    def fetch_transcript(self, data, _suffix=''):
        """
        Xblock handler to perform actual transcript content fetching.

        :param data: transcript language code and transcript URL
        :param _suffix: not using
        :return: transcript's text content
        """
        handler_response = {'result': 'error', 'message': _('Missing required transcript data: `src` and `srcLang`')}

        try:
            transcript_url = data.pop('srcUrl')
            transcript_lang = data.pop('srcLang')
        except KeyError:
            return handler_response

        failure_message = "Transcript fetching failure: language [{}]".format(transcript_lang)
        try:
            response = requests.get(transcript_url)
            return {
                'result': 'success',
                'content': response.content
            }
        except IOError:
            log.exception(failure_message)
            handler_response['message'] = _(failure_message)
            return handler_response
        except (ValueError, KeyError, TypeError, AttributeError):
            log.exception("Can't get content of the fetched transcript: language [{}]".format(transcript_lang))
            handler_response['message'] = _(failure_message)
            return handler_response
