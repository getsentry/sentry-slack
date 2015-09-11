"""
sentry_slack.plugin
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2015 by Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import operator
import sentry_slack

from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q

from sentry import http
from sentry.models import TagKey, TagValue
from sentry.plugins.bases import notify
from sentry.utils import json

LEVEL_TO_COLOR = {
    'debug': 'cfd3da',
    'info': '2788ce',
    'warning': 'f18500',
    'error': 'f43f20',
    'fatal': 'd20f2a',
}


# Project.get_full_name backported from v8.0
def get_project_full_name(project):
    if project.team.name not in project.name:
        return '%s %s' % (project.team.name, project.name)
    return project.name


class SlackOptionsForm(notify.NotificationConfigurationForm):
    webhook = forms.URLField(
        help_text='Your custom Slack webhook URL',
        widget=forms.TextInput(attrs={'class': 'span8'}))
    include_tags = forms.BooleanField(
        help_text='Include tags with notifications',
        required=False,
    )
    include_rules = forms.BooleanField(
        help_text='Include triggering rules with notifications',
        required=False,
    )


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

    def _get_tags(self, event):
        # TODO(dcramer): we want this behavior to be more accessible in sentry
        tag_list = event.get_tags()
        if not tag_list:
            return ()

        key_labels = {
            o.key: o.get_label()
            for o in TagKey.objects.filter(
                project=event.project,
                key__in=[t[0] for t in tag_list],
            )
        }
        value_labels = {
            (o.key, o.value): o.get_label()
            for o in TagValue.objects.filter(
                reduce(operator.or_, (Q(key=k, value=v) for k, v in tag_list)),
                project=event.project,
            )
        }
        return (
            (key_labels.get(k, k), value_labels.get((k, v), v))
            for k, v in tag_list
        )

    def notify(self, notification):
        event = notification.event
        group = event.group
        project = group.project

        if not self.is_configured(project):
            return

        webhook = self.get_option('webhook', project)

        title = group.message_short.encode('utf-8')
        culprit = group.culprit.encode('utf-8')
        project_name = get_project_full_name(project).encode('utf-8')

        fields = []

        # They can be the same if there is no culprit
        # So we set culprit to an empty string instead of duplicating the text
        if title != culprit:
            fields.append({
                'title': 'Culprit',
                'value': culprit,
                'short': False,
            })

        fields.append({
            'title': 'Project',
            'value': project_name,
            'short': True,
        })

        if self.get_option('include_rules', project):
            rules = []
            for rule in notification.rules:
                rule_link = reverse('sentry-edit-project-rule', args=[
                    group.organization.slug, project.slug, rule.id
                ])
                rules.append((rule_link, rule.label.encode('utf-8')))

            if rules:
                fields.append({
                    'title': 'Triggered By',
                    'value': ', '.join('<%s | %s>' % r for r in rules),
                    'short': False,
                })

        if self.get_option('include_tags', project):
            for tag_key, tag_value in self._get_tags(event):
                fields.append({
                    'title': tag_key.encode('utf-8'),
                    'value': tag_value.encode('utf-8'),
                    'short': True,
                })

        payload = {
            'parse': 'none',
            'attachments': [{
                'fallback': '[%s] %s' % (project_name, title),
                'title': title,
                'title_link': group.get_absolute_url(),
                'color': self.color_for_group(group),
                'fields': fields,
            }]
        }

        values = {'payload': json.dumps(payload)}

        return http.safe_urlopen(webhook, method='POST', data=values)
