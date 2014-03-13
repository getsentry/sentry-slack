try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry-slack').version
except Exception, e:
    VERSION = 'unknown'
