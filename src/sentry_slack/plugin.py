"""
sentry_slack.plugin
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2015 by Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import sentry_slack

from django import forms

from sentry import http
from sentry.plugins.bases import notify
from sentry.utils import json

import urllib

LEVEL_TO_COLOR = {
    'debug': 'cfd3da',
    'info': '2788ce',
    'warning': 'f18500',
    'error': 'f43f20',
    'fatal': 'd20f2a',
}


class SlackOptionsForm(notify.NotificationConfigurationForm):
    webhook = forms.CharField(
        help_text='Your custom Slack webhook URL',
        widget=forms.TextInput(attrs={'class': 'span8'}))


class SlackPlugin(notify.NotificationPlugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry'
    resource_links = (
        ('Bug Tracker', 'https://github.com/getsentry/sentry-slack/issues'),
        ('Source', 'https://github.com/getsentry/sentry-slack'),
    )

    title = 'Slack'
    slug = 'slack'
    description = 'Post notifications to a Slack channel.'
    conf_key = 'slack'
    version = sentry_slack.VERSION
    project_conf_form = SlackOptionsForm

    def is_configured(self, project):
        return all((self.get_option(k, project) for k in ('webhook',)))

    def color_for_group(self, group):
        return '#' + LEVEL_TO_COLOR.get(group.get_level_display(), 'error')

    def notify_users(self, group, event, fail_silently=False):
        webhook = self.get_option('webhook', event.project)
        project = event.project
        team = event.team

        title = '%s on <%s|%s %s>' % (
            'New event' if group.times_seen == 1 else 'Regression',
            group.get_absolute_url(),
            team.name.encode('utf-8'),
            project.name.encode('utf-8'),
        )

        message = getattr(group, 'message_short', group.message).encode('utf-8')
        culprit = getattr(group, 'title', group.culprit).encode('utf-8')

        # They can be the same if there is no culprit
        # So we set culprit to an empty string instead of duplicating the text
        if message == culprit:
            culprit = ''

        payload = {
            'parse': 'none',
            'text': title,
            'attachments': [{
                'color': self.color_for_group(group),
                'fields': [{
                    'title': message,
                    'value': culprit,
                    'short': False,
                }]
            }]
        }

        values = {'payload': json.dumps(payload)}

        return http.safe_urlopen(webhook, method='POST', data=values)
