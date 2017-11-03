/* global tinyMCE baseUrl gettext */

/**
 * Javascript for StudioEditableXBlockMixin.
 * @param runtime
 * @param element
 * @constructor
 */
function StudioEditableXBlockMixin(runtime, element) {
    'use strict';

    var fields = [],
        studioSubmit;
    // Studio includes a copy of tinyMCE and its jQuery plugin
    var tinyMceAvailable = (typeof $.fn.tinymce !== 'undefined');
    var datepickerAvailable = (typeof $.fn.datepicker !== 'undefined'); // Studio includes datepicker jQuery plugin
    var handlerUrlGetCaptions = runtime.handlerUrl(element, 'get_captions');
    var $containerCaptions = $(element).find('.js-container-captions');

    $(element).find('.field-data-control').each(function() {
        var $field = $(this);
        var $wrapper = $field.closest('li');
        var $resetButton = $wrapper.find('button.setting-clear');
        var type = $wrapper.data('cast');
        var fieldChanged;
        fields.push({
            name: $wrapper.data('field-name'),
            isSet: function() { return $wrapper.hasClass('is-set'); },
            hasEditor: function() { return tinyMceAvailable && $field.tinymce(); },
            val: function() {
                var val = $field.val();
                // Cast values to the appropriate type so that we send nice clean JSON over the wire:
                if (type === 'boolean') {
                    return (val === 'true' || val === '1');
                }
                if (type === 'integer') {
                    return parseInt(val, 10);
                }
                if (type === 'float') {
                    return parseFloat(val);
                }
                if (type === 'generic' || type === 'list' || type === 'set') {
                    val = val.trim();
                    if (val === '') {
                        val = null;
                    } else {
                        val = JSON.parse(val); // TODO: handle parse errors
                    }
                }
                return val;
            },
            removeEditor: function() {
                $field.tinymce().remove();
            }
        });
        fieldChanged = function() {
            // Field value has been modified:
            $wrapper.addClass('is-set');
            $resetButton.removeClass('inactive').addClass('active');
        };
        $field.bind('change input paste', fieldChanged);
        $resetButton.click(function() {
            // Use attr instead of data to force treating the default value as a string
            $field.val($wrapper.attr('data-default'));
            $wrapper.removeClass('is-set');
            $resetButton.removeClass('active').addClass('inactive');
        });
        if (type === 'html' && tinyMceAvailable) {
            tinyMCE.baseURL = baseUrl + '/js/vendor/tinymce/js/tinymce';
            $field.tinymce({
                theme: 'modern',
                skin: 'studio-tmce4',
                height: '200px',
                formats: {code: {inline: 'code'}},
                codemirror: {path: '' + baseUrl + '/js/vendor'},
                convert_urls: false,
                plugins: 'link codemirror',
                menubar: false,
                statusbar: false,
                toolbar_items_size: 'small',
                toolbar: 'formatselect | styleselect | bold italic underline forecolor wrapAsCode | ' +
                'bullist numlist outdent indent blockquote | link unlink | code',
                resize: 'both',
                setup: function(ed) {
                    ed.on('change', fieldChanged);
                }
            });
        }

        if (type === 'datepicker' && datepickerAvailable) {
            $field.datepicker('destroy');
            $field.datepicker({dateFormat: 'm/d/yy'});
        }
    });

    $(element).find('.wrapper-list-settings .list-set').each(function() {
        var $optionList = $(this);
        var $checkboxes = $(this).find('input');
        var $wrapper = $optionList.closest('li');
        var $resetButton = $wrapper.find('button.setting-clear');
        var fieldChanged;

        fields.push({
            name: $wrapper.data('field-name'),
            isSet: function() { return $wrapper.hasClass('is-set'); },
            hasEditor: function() { return false; },
            val: function() {
                var val = [];
                $checkboxes.each(function() {
                    if ($(this).is(':checked')) {
                        val.push(JSON.parse($(this).val()));
                    }
                });
                return val;
            }
        });
        fieldChanged = function() {
            // Field value has been modified:
            $wrapper.addClass('is-set');
            $resetButton.removeClass('inactive').addClass('active');
        };
        $checkboxes.bind('change input', fieldChanged);

        $resetButton.click(function() {
            var defaults = JSON.parse($wrapper.attr('data-default'));
            $checkboxes.each(function() {
                var val = JSON.parse($(this).val());
                $(this).prop('checked', defaults.indexOf(val) > -1);
            });
            $wrapper.removeClass('is-set');
            $resetButton.removeClass('active').addClass('inactive');
        });
    });

    studioSubmit = function(data) {
        var handlerUrl = runtime.handlerUrl(element, 'submit_studio_edits');
        runtime.notify('save', {state: 'start', message: gettext('Saving')});
        $.ajax({
            type: 'POST',
            url: handlerUrl,
            data: JSON.stringify(data),
            dataType: 'json',
            global: false,  // Disable Studio's error handling that conflicts with studio's notify('save')
                            // and notify('cancel') :-/
            success: function() { runtime.notify('save', {state: 'end'}); }
        }).fail(function(jqXHR) {
            var message = gettext('This may be happening because of an error with our server or your internet ' +
                'connection. Try refreshing the page or making sure you are online.');
            if (jqXHR.responseText) { // Is there a more specific error message we can show?
                try {
                    message = JSON.parse(jqXHR.responseText).error;
                    if (typeof message === 'object' && message.messages) {
                        // e.g. {"error": {"messages": [{"text": "Unknown user 'bob'!", "type": "error"}, ...]}} etc.
                        message = $.map(message.messages, function(msg) { return msg.text; }).join(', ');
                    }
                } catch (error) { message = jqXHR.responseText.substr(0, 300); }
            }
            runtime.notify('error', {title: gettext('Unable to update settings'), message: message});
        });
    };

    $('.save-button', element).bind('click', function(e) {
        var i,
            field;
        var values = {};
        var notSet = []; // List of field names that should be set to default values
        e.preventDefault();
        for (i = 0; i < fields.length; i++) {
            field = fields[i];
            if (field.isSet()) {
                values[field.name] = field.val();
            } else {
                notSet.push(field.name);
            }
            // Remove TinyMCE instances to make sure jQuery does not try to access stale instances
            // when loading editor for another block:
            if (field.hasEditor()) {
                field.removeEditor();
            }
        }
        studioSubmit({values: values, defaults: notSet});
    });

    $(element).find('.cancel-button').bind('click', function(e) {
        // Remove TinyMCE instances to make sure jQuery does not try to access stale instances
        // when loading editor for another block:
        var i,
            field;
        e.preventDefault();
        for (i = 0; i < fields.length; i++) {
            field = fields[i];
            if (field.hasEditor()) {
                field.removeEditor();
            }
        }
        runtime.notify('cancel', {});
    });
    /**
     * Handle error messages
     * @param jqXHR
     */
    function showErrorFail(jqXHR) {
        var message = gettext('This may be happening because of an error with our server or your internet ' +
                'connection. Try refreshing the page or making sure you are online.');
        if (jqXHR.responseText) { // Is there a more specific error message we can show?
            try {
                message = JSON.parse(jqXHR.responseText).error;
                if (typeof message === 'object' && message.messages) {
                    // e.g. {"error": {"messages": [{"text": "Unknown user 'bob'!", "type": "error"}, ...]}} etc.
                    message = $.map(message.messages, function(msg) { return msg.text; }).join(', ');
                }
            } catch (error) { message = jqXHR.responseText.substr(0, 300); }
        }
        runtime.notify('error', {title: gettext('Unable to update settings'), message: message});
    }

    /**
     * setCaptionsField
     */
    function setCaptionsField() {
        var captions = [];
        $containerCaptions.find('[name = "captions"]:checked').each(function() {
            var $selectLang = $(this).parents('li').find('option:selected');
            var caption = {
                kind: 'subtitles',
                src: $(this).val(),
                srclang: $selectLang.val(),
                label: $selectLang.text()
            };
            captions.push(caption);
        });
        $(element).find('[data-field-name = "captions"] textarea').val(JSON.stringify(captions))
            .trigger('change');
    }

    /**
     * setOnChangeCaptions
     */
    function setOnChangeCaptions() {
        $containerCaptions.find('[name = "captions"]').on('change', function() {
            setCaptionsField();
        });
        $containerCaptions.find('[name = "language"]:visible').on('change', function() {
            setCaptionsField();
        });
    }

    /**
     * renderCaptions
     * @param data
     */
    function renderCaptions(data) {
        var i, html;
        var $selectLang = $(element).find('.js-tempate-lang');
        $containerCaptions.empty();
        if (data.length === 0) {
            $containerCaptions.text(gettext('No captions/transcripts available for selected video.'));
        } else {
            for (i = 0; i < data.length; i++) {
                html = '<li class="select-holder"><div class="wrap-input-captions"><input id="checkbox-captions-' + i +
                        '" type="checkbox" name="captions" value="' +
                        data[i].download_url + '"/><label for="checkbox-captions-' + i + '">' +
                        data[i].name_file + '</label></div>' +
                        $selectLang.clone().removeClass('hidden').html() + '</li>';
                $containerCaptions.append(html);
            }
            setOnChangeCaptions();
        }
    }

    /**
     * getCaptions
     * @param $ev
     */
    function getCaptions($ev) {
        var assetId = $ev.data('asset-id');
        $containerCaptions.html('<div class="loader-wrapper"><span class="loader"><svg class="icon icon-spinner11">' +
            '<use xlink:href="#icon-spinner11"></use></svg></span></div class="loader-wrapper">');
        $.ajax({
            type: 'POST',
            url: handlerUrlGetCaptions,
            data: JSON.stringify({asset_id: assetId}),
            dataType: 'json',
            success: function(data) {
                if (data.result === 'error') {
                    $containerCaptions.html(data.message);
                } else {
                    renderCaptions(data);
                }
            }
        }).fail(showErrorFail);
    }

    $(element).find('.js-header-tab').on('click', function(e) {
        var $currentTarget = $(e.currentTarget);
        var dataTab = $currentTarget.data('tab');
        e.preventDefault();
        $(element).find('.js-header-tab').removeClass('current');
        $currentTarget.addClass('current');
        $(element).find('.component-tab').addClass('is-inactive');
        $(element).find('.' + dataTab).removeClass('is-inactive');
    });

    $(element).find('[name = "stream_video"]').on('change', function(e) {
        var $currentTarget = $(e.currentTarget);
        var urlSmoothStreaming = $currentTarget.val();
        getCaptions($currentTarget);
        $(element).find('[data-field-name = "video_url"] input').val(urlSmoothStreaming)
            .trigger('change');
    });
}
