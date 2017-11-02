# -*- coding: utf-8 -*-
"""
Copyright (c) Microsoft Corporation. All Rights Reserved.

Licensed under the MIT license. See LICENSE file on the project webpage for details.
"""
import os
from HTMLParser import HTMLParser

from django.template import Engine, Context

html_parser = HTMLParser()  # pylint: disable=invalid-name


def _(text):
    """
    Make '_' a no-op so we can scrape strings.
    """
    return text


def render_template(template_name, **context):
    """
    Render static resource using provided context.

    Returns: django.utils.safestring.SafeText
    """
    template_dirs = [os.path.join(os.path.dirname(__file__), 'templates')]
    engine = Engine(dirs=template_dirs, debug=True)
    html = engine.get_template(template_name)

    return html_parser.unescape(
        html.render(Context(context))
    )
