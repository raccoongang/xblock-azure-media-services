[![Circle CI Build: Status](https://img.shields.io/circleci/project/raccoongang/xblock-azure-media-services/dev.svg)](https://circleci.com/gh/raccoongang/xblock-azure-media-services/tree/dev)

Azure Media Services xBlock
===========================

This xBlock allows for the inclusion of videos that are hosted on Azure Media Services inside of Open edX courses. The primary features of this xBlock are:

* (optionally) protected videos that only students enrolled in a course can watch the video. This contrasts with the standard Open edX video player which does not offer any protection from non-enrolled students to watch the video

* subtitles/captions via WebVTT standards

* interactive transcripts

This xBlock is still at an experimental stage and is still under development.

Code of Conduct
---------------
This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

Installation
------------

To install the Azure Media Services XBlock within your edX Python environment, run the following command (for fullstack):

```bash
$ sudo -u edxapp bash
$ source /edx/app/edxapp/edxapp_env
$ pip install /path/to/xblock-azure-media-services/
```

or for devstack:

```bash
$ sudo su edxapp
$ pip install /path/to/xblock-azure-media-services/
```


Enabling in Studio
------------------

To enable the Azure Media Services XBlock within studio:

1. Navigate to `Settings -> Advanced Settings` from the top nav bar.
2. Add `"azure_media_services"` to the Advanced Module List, as shown in the screen shot below.

![Advanced Module List](docs/img/advanced_components.png)


Usage
-----

After the Azure Media Services xBlock is enabled, when the Studio user is inside of a Unit, when he/she clicks on the Advanced button (displayed below all existing components inside of a Unit), the “Azure Media Services Video Player” will appear in the list. Such as:

![List of components](docs/img/list_of_advanced_components.png)

Clicking that xBlock will populate, the Unit with a functional - but unconfigured - Azure Media Player:

![New Instance](docs/img/new_instance.png)

Click the `Edit` button in the upper right corner to expose the scrollable setting panel for the xBlock:

![Settings1](docs/img/settings1.png)

![Settings2](docs/img/settings2.png)

![Settings3](docs/img/settings3.png)

Video URL field may be configured manually (please, see below).

The following is a description of the fields and how to configure them. At a minimum, the courseware author will need to fill in the Video Url to match what Azure Media Services portal says the Publish URL is, for example (old Azure dashboard):

![Dashboard Publish Url](docs/img/azure_published_url.png)

Or in the new Azure dashboard:

![Dashboard Publish Url](docs/img/azure_published_url_new_dashboard.png)

In order to avoid mixing HTTP/HTTPS which can cause some warnings to appear in some browsers, it is recommended that you simply drop the http: or https: and simply start at the double slashes: e.g. ‘//cdodgetestmediaservice.streaming.mediaservices.windows.net/7aaeec64-aa78-436b-bd43-68ae72bb3b4d/big_buck_bunny.ism/Manifest'

At this point, if the video you want to include does not utilize Video Protection, then you can simply Save and Close the Setting dialog box. Then the page should refresh and you should see the video be loaded (but not auto-play).

If the video DOES use Protection, then if you just specify the Video URL but fail to specify the protection related properties (or have them incorrectly configured), then you will see something like:

![Cant Decrypt](docs/img/cant_decrypt.png)

If you wish to use Azure Media Service’s Video Protection features, then you will need to have your Azure dashboard set up in a particular manner. For example (old Azure dashboard):

![AES Protection](docs/img/aes_protection.png)

In the new Azure dashboard, the Content Protection area looks different, but is basically the same concept:

![AES Protection](docs/img/aes_protection_new_dashboard.png)

At this point in time, the Azure Media Services xBlock only can generate “JSON Web Tokens”, so that must be selected. Then for the Issuer and Scope fields, it is very important that you EITHER a) use the defaults that are in the xBlock OR b) reconcile the values between the Azure portal and the xBlock setting dialog AS THEY MUST MATCH EXACTLY. The defaults for the xBlock are shown in the above screenshot (‘http://open.edx.org’ and ‘urn:xblock-azure-media-services’, respectively). There are no semantic meaning behind these two defaults.

Also, for the older version of Azure Media Services dashboard, users will need to generate and copy over the Verification Keys from the portal to the xBlock:

![AES Protection Keys](docs/img/aes_protection_keys.png)

In the newer Azure dashboard/portal, the Regenerate Keys button has moved to the top of the pane:

![AES Protection Keys](docs/img/aes_protection_keys_new_dashboard.png)

Or, as an option, you can create your own AES encryption keys, but note that they must be base64 encoded:

![AES Protection Keys Closeup](docs/img/aes_protection_keys_closeup_new_dashboard.png)

If you’d prefer to generate keys on a local machine, then - for example on OSx - you can:

```
dd bs=1 count=32 if=/dev/urandom | openssl base64
This will output something like:
32+0 records in
32+0 records out
32 bytes transferred in 0.000059 secs (543392 bytes/sec)
vBjBqVqioLb6q3ayVWpkuGOn4i3xKitKkZpH/FSF1Yg=
```

The last line at the bottom is a valid Base64 encoded AES encryption key. Just copy that into your cut/paste buffer and put into the Azure “Manage verification keys” portion of the portal.

Then, regardless of how you generate these keys, simply copy one of the keys - typically the primary - into the clipboard and then paste it into the xBlock settings pane:

![Filled in URL settings](docs/img/filled_in_url_settings.png)

IMPORTANT: The courseware author also needs to specify the “Protection Type” in this case to match which Protection is being utilized - in this case AES.

If all is configured correctly - i.e. the verification key, protection type, the token issuer, and token scope - then after saving these changes the video should properly play back.

IMPORTANT: I have noticed some latency for some configuration changes in Azure Media Services to take effect. If protected video playback doesn’t work, wait a few minutes and refresh the page. If it still doesn’t work, carefully inspect all of the values and make sure they match between the Azure portal and the xBlock settings

Working with Transcripts/Subtitles/Captions
-------------------------------------------

    Note: the same files (*.vtt file extension) are used as transcripts, captions, and subtitles.

This version of the Azure Media Services xBlock supports several means to associate text (i.e. dialog) with a video. All text associations with videos uses the WebVTT standard: https://w3c.github.io/webvtt/

**_Subtitles/Captions_**: These are short pieces of text which are rendered in the lowest center portion of the video player, in a manner similar to captions on a television. The Azure Media Player supports subtitles and captions out of the box, and the Azure Media Services xBlock merely wires through the existing support.

While subtitles/captions are rendered in the same manner, they are typically targeted to different audiences. Subtitles are typically for translations between languages, but captions are for users who have accessibility needs.

To use subtitles/captions, simply fill in the `Captions` field inside the xBlock settings panel. Right now the UI is a text field in which the content editor will have to input in a JSON formatted array of dictionaries. This will change into a more user-friendly UI in a subsequent version of the xBlock:

![Captions Setting](docs/img/captions_setting.png)

As a better illustration of the data payload, here is a sample:

```
[{
"srclang": "en",
"kind": "subtitles",
"label": "english",
"src":"//ams-samplescdn.streaming.mediaservices.windows.net/11196e3d-2f40-4835-9a4d-fc52751b0323/TOS-en.vtt"}
,{
"srclang": "es",
"kind": "subtitles",
"label": "spanish",
"src":"//ams-samplescdn.streaming.mediaservices.windows.net/11196e3d-2f40-4835-9a4d-fc52751b0323/TOS-es.vtt"}
,{
"srclang": "fr",
"kind": "subtitles",
"label": "french",
"src":"//ams-samplescdn.streaming.mediaservices.windows.net/11196e3d-2f40-4835-9a4d-fc52751b0323/TOS-fr.vtt"}
,{
"srclang": "it",
"kind": "subtitles",
"label": "italian",
"src":"//ams-samplescdn.streaming.mediaservices.windows.net/11196e3d-2f40-4835-9a4d-fc52751b0323/TOS-it.vtt"
}]
```

The kind field can either be _‘subtitles’_ or _‘captions’_. The srclang field is an ISO short declaration of the language that the text is in. The label field is what is displayed in the select menu in the player. And src is a URL where the VTT file can be sourced from.

When everything is configured, the player should look like something like:

![Captions](docs/img/captions.png)

**_Transcripts_**

Transcripts are very similar to captions/subtitles, but it is designed more for display of larger amounts of text associated with a video. The WebVTT text is displayed in a large, scrollable pane to the side of the video player region. Furthermore, as the video is played, the current portion of the audio track is highlighted in the text region. As the video progresses, the user can visually see what area of the transcript is current. In addition, the transcript acts as a “seek” mechanism. If a user clicks on an area of the transcript, the video jumps to the portion of the video that correlates to that piece of text. 

Transcript features are part of Open edX and the implementation in the Azure Media Services xBlocks is meant to be a “feature parity” compared to the out-of-the-box video player support in Open edX.

**_Transcripts downloading_**

If any transcripts available the *downloads button* appears in player's control bar. This button opens *Download dashboard*:

![Download Dashboard](docs/img/transcripts-download.png)

To download desired transcript file one must choose 'Transcript' (asset type to download), pick the language and hit the Download button.

Analytic Events
---------------

This Azure Media Services xBlock produces analytics events. We have decided to use the existing video player events/schemas so that it will be compatible with existing video engagement analytics tools as defined at http://edx.readthedocs.io/projects/devdata/en/latest/internal_data_formats/tracking_logs.html#video

The following events are currently emitted from the Azure Media Services xBlock into the analytics stream:

```
edx.video.loaded
edx.video.played
edx.video.paused
edx.video.position.changed
edx.video.stopped
```

The next iteration of this player will include the following analytic events.

```
edx.video.transcript.hidden
edx.video.transcript.shown
edx.video.closed_captions.hidden
edx.video.closed_captions.shown
speed_change_video
edx.video.language_menu.hidden
edx.video.language_menu.shown
```


Automatic way to configure Video URL
------------------------------------
Before use this way, please be sure that you configure the following settings https://github.com/raccoongang/edx-platform/blob/oxa/video/cms/djangoapps/azure_video_pipeline/README.md

The simplest way to configure Video URL lays within `MANAGEMENT` tab.

![Management tab](docs/img/management-tab.png)

All is needed is to open `MANAGEMENT` tab and pick the video file from the list of available ones on the left panel.

![Management: available videos](docs/img/management-tab-videos-list.png)

As soon as the video is selected the list of available transcripts (captions) appears on the right panel. Initially, all transcripts are unchecked. To enable certain transcript its checkbox should be checked.

![Management: available videos](docs/img/management-tab-transcripts-list.png)


Working with Transcripts/Subtitles/Captions
-------------------------------------------
If Video URL field was configured via `MANAGEMENT` tab `Captions` field should be already filled.
To enable transcripts player control in the Azure Media Services xBlock, turn on the boolean `Transcripts enabled` field:


![Transcript Setting](docs/img/transcripts-switch.png)

If transcripts feature is enabled new `TRANSCRIPTS` control  and transcripts download links appear in the Player.

![Transcript Setting](docs/img/transcritps-controls.png)

If configured correctly, the entire WebVTT file will be read and presented in the scrolling region to the right of the video player. When the video plays, you will notice that the current text associated with the video track will be highlighted. The viewer can click on any piece of the transcript text and the video player will seek to the time associated to that portion of the clicked transcript.


Assets downloading
------------------
Assets (video, transcripts) downloading can be performed in different modes. Certain download mode is configured in Studio editor by setting `Assets download mode` switch field:
- Edx-way (footer links) - (default) only footer download buttons are shown beneath the Player;
- Via Player (download dashboard) - only download player's control button is available;
- Combined - first two options enabled simultaneously;
- Off - assets downloading disabled.

![Download modes](docs/img/download-modes.png)

![Assets downloading](docs/img/assets-downloading.png)


Sharing option
--------------

In order to use xblock’s Sharing feature additional platform changes must be performed:
- `azure_media_services` app urls must be included both to LMS and CMS`

```
# lms/urls.py:
url( r'^azure_media_services_xblock/', include('azure_media_services.urls') ),
#cms/urls.py:
url( r'^azure_media_services_xblock/', include('azure_media_services.urls') ),
```

The video can be shared in standard `embed iframe` way by copying generated html code snippet into the desired environment. By default sharing feature is disabled and it can be configured by corresponding Studio editor control:
- Off - disabled (default);
- Staff only - only _staff_ users can see `share` button;
- All - sharing is available for everyone.

![Video share](docs/img/video-share.png)

![Share popup](docs/img/share-popup.png)
