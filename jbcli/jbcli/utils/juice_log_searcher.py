""" An elastic search class that queries juicebox logs """

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus
from os import environ
import re
import tablib

# Extract timestamp, loglevel and data service log source
prefix_pattern = re.compile('(.*)\ \[([A-Z]*)\]\ dataservices.(\w+)')
# Extract part of the dataservices.params logs
params_pattern = re.compile(
    'User extra: (.*)Request params: (.*)Automatic filters: (.*)Custom filters: (.*)'
)


class JuiceboxLoggingSearcher(object):
    def _parse_log_parts(self, data_service_log, parts):
        """ Parse the log messages """
        row = {}

        # Each query contains data that looks like key=value key2=value2
        # and sometimes extra data
        if data_service_log == 'params':
            kv_parts, extra_parts = parts.split('   ', 1)
        elif data_service_log == 'recipe':
            kv_parts, extra_parts = parts.split('SELECT ', 1)
            extra_parts = 'SELECT ' + extra_parts
            extra_parts = extra_parts.replace('QUERYEND', '')
        elif data_service_log == 'performance':
            kv_parts, extra_parts = parts, ''

        # Handle the  key=value key2=value2 data
        for part in parts.split(' '):
            if part and '=' in part:
                k, v = part.split('=')

                # parse some values into numbers
                if k == 'rows':
                    v = int(v)
                if k in ('enchant', 'db', 'totaltime'):
                    v = float(v)
                if k and v:
                    row[k] = v

        # Handle the log specific extra parts
        if data_service_log == 'recipe':
            row['query'] = extra_parts

        elif data_service_log == 'params':
            m = re.match(params_pattern, extra_parts)
            if m:
                user_extra, request_params, automatic_filters, custom_filters = m.groups(
                )
            else:
                user_extra = request_params = automatic_filters = custom_filters = 'NOMATCH'
            row['user_extra'] = user_extra
            row['request_params'] = request_params
            row['automatic_filters'] = automatic_filters
            row['custom_filters'] = custom_filters
        return row

    def dataset(self, *args, **kwargs):
        """Create a tablib dataset of a search"""
        data = self.search(*args, **kwargs)

        dataset = tablib.Dataset()

        # Pull these keys to the front
        initial_keys = [
            'timestamp',
            'service_id',
            'service',
            'user',
            'environment',
        ]
        if data:
            keys = list(
                sorted([k for k in data[0].keys() if k not in initial_keys]))
            initial_keys = [k for k in initial_keys if k in data[0].keys()]
            dataset.headers = initial_keys + keys
            for row in data:
                values = [row.get(k) for k in dataset.headers]
                dataset.append(values)

        return dataset

    def search(self,
               username=None,
               password=None,
               env='legacy-prod',
               service_pattern='.*',
               user_pattern='.*',
               data_service_log='performance',
               lookback_window=10,
               limit=100):
        """Return some data as a list of dicts

        :param username: The username used to connect to elasticsearch
        :param password: The password used to connect to elasticsearch
        :param env: can be one of 'legacy-staging', 'legacy-prod', 'prod', 'hstm-qa', 'hstm-prod', determines the elasticsearch server to connect to and
        environment to hit
        :param service_pattern: a regex pattern that the data service must match
        :param user_pattern: a regex pattern that the user must match
        :param data_service_log: one of recipe, performance, params
            recipe: sql queries that were run and their runtime and number of rows returned
            params: parameters passed to a data service and user extra
            performance: how long the data service took to run
        :param lookback_window: a number of days to get history for
        :param limit: how many rows to return, 0 returns all rows
        """
        assert (data_service_log in ('recipe', 'performance', 'params'))

        service_pattern = re.compile(service_pattern)
        user_pattern = re.compile(user_pattern)

        # TODO: We could do so much more with this query
        q = Q(
            'bool',
            filter=[
                Q(
                    'range', **{
                        '@timestamp': {
                            'gte': 'now-{}d'.format(lookback_window),
                            'lt': 'now'
                        }
                    }),
                Q(
                    'simple_query_string', **{
                        "query": 'dataservices.{}'.format(data_service_log),
                        "fields": ["message"],
                    }),
            ])

        if env.startswith('hstm'):
            username = quote_plus(environ.get('HSL_USERNAME') or username)
            password = quote_plus(environ.get('HSL_PASSWORD') or password)
            client = Elasticsearch([
                'https://{}:{}@hsl.juiceboxdata.com:443'.format(
                    username, password)
            ])
            filter_type = 'log'
        else:
            username = quote_plus(environ.get('LP_USERNAME') or username)
            password = quote_plus(environ.get('LP_PASSWORD') or password)
            client = Elasticsearch([
                'https://{}:{}@lp.juiceboxdata.com:443'.format(
                    username, password)
            ])
            filter_type = 'jb_data_services'

        search = Search(index='logstash-*') \
            .using(client) \
            .filter('term', type=filter_type) \
            .sort('@timestamp', {"lines": {"order": "asc"}}) \
            .query(q)

        # Adapt search queries to target the right environment
        if env == 'hstm-qa':
            pass
            # TODO: come up with a better way of filtering to staging
            # These are filtered when iterating over results by looking
            # at beat.hostname.
        elif env == 'hstm-prod':
            pass
            # TODO: come up with a better way of filtering to prod
            # These are filtered when iterating over results by looking
            # at beat.hostname.
        elif env == 'legacy-staging':
            search = search.filter('term', **{
                'fields.env': 'staging'
            }).filter(
                'term', environment='legacy')
        elif env == 'legacy-prod':
            search = search.filter('term', **{
                'fields.env': 'prod'
            }).filter(
                'term', environment='legacy')
        elif env == 'prod':
            search = search.filter('term', environment='prod')

        results = []
        cnt = 0
        for hit in search.scan():
            if limit and cnt >= limit:
                break

            # Filter hstm rows, would be better to do this in the ES query
            if env == 'hstm-prod' and 'prod' not in hit.beat.hostname:
                continue
            if env == 'hstm-qa' and 'staging' not in hit.beat.hostname:
                continue

            # prefix = 2019-04-16 01:08:25,794 [DEBUG] dataservices.params:
            # parts = data about this request
            prefix, parts = hit.message.split(': ', 1)

            prefix_match = re.match(prefix_pattern, prefix)
            ts, level, data_service_log = prefix_match.groups()

            # Parse the log message into a dictionary
            # Get the timestamp and the debug level
            row = {
                'timestamp': ts,
                'environment': hit.environment,
                'data_service_log': data_service_log
            }
            row.update(self._parse_log_parts(data_service_log, parts))

            # Filter to a specific service pattern
            if re.match(service_pattern, row.get('service', '')) and \
                    re.match(user_pattern, row.get('user', '')):
                cnt += 1
                results.append(row)

        return results

