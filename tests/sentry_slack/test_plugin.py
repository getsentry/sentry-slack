from __future__ import absolute_import

import responses

from exam import fixture
from sentry.models import Rule
from sentry.plugins import Notification
from sentry.testutils import TestCase

from sentry_slack.plugin import SlackPlugin


class SlackPluginTest(TestCase):
    @fixture
    def plugin(self):
        return SlackPlugin()

    @responses.activate
    def test_simple_notification(self):
        responses.add('POST', 'http://example.com/slack')
        self.plugin.set_option('webhook', 'http://example.com/slack', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(group=group, message='Hello world')

        rule = Rule.objects.create(project=self.project, label='my rule')

        notification = Notification(event=event, rule=rule)

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.notify(notification)
