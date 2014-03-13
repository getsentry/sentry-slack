"""
sentry_slack.plugin
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2014 by Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import sentry_slack

from django import forms

from sentry.plugins import Plugin
from sentry.utils import json

import urllib
import urllib2
import logging

logger = logging.getLogger('sentry.plugins.slack')


class SlackOptionsForm(forms.Form):
    webhook = forms.CharField(
        help_text='Your custom Slack webhook URL',
        widget=forms.TextInput(attrs={'class': 'span8'}))


class SlackPlugin(Plugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry'
    description = 'Post new exceptions to a Slack channel.'
    resource_links = (
        ('Bug Tracker', 'https://github.com/getsentry/sentry-slack/issues'),
        ('Source', 'https://github.com/getsentry/sentry-slack'),
    )

    title = 'Slack'
    slug = 'slack'
    conf_key = 'slack'
    description = 'Send errors to Slack'
    version = sentry_slack.VERSION
    project_conf_form = SlackOptionsForm

    def is_configured(self, project):
        return all((self.get_option(k, project) for k in ('webook',)))

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        if not is_new:
            return
        message = event.get_email_subject()
        webhook = self.get_option('webhook', event.project)
        self.send_payload(webhook, group, message)

    def send_payload(self, webhook, group, message):
        text = '<%s|%s>' % (group.get_absolute_url(), message)
        values = {
            'payload': json.dumps({'text': text.encode('utf8')})
        }

        data = urllib.urlencode(values)
        request = urllib2.Request(webhook, data)
        try:
            urllib2.urlopen(request)
        except urllib2.URLError:
            logger.error('Could not connect to Slack.')
        except urllib2.HTTPError as e:
            logger.error('Error posting to Slack: %s', e.read())
