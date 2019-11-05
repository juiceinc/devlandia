import os
from unittest.mock import call, patch

from ..utils.juice_log_searcher import JuiceboxLoggingSearcher


class TestJuiceboxLoggingSearcher:
    def test_parse_log_parts(self):
        searcher = JuiceboxLoggingSearcher()
        d = searcher._parse_log_parts('performance', 'a=b c=d')
        assert d == {'a': 'b', 'c': 'd'}

    def test_parse_log_parts_performance(self):
        searcher = JuiceboxLoggingSearcher()
        line = '''2019-04-15 00:00:13,950 [DEBUG] dataservices.performance: service_id=jb3:1a561d1e-a82d-430f-b639-93bf2481d534 user=timothy.schailey@jefferson.edu service=apps.caygd.stacks.trend.trendservice.LeaderboardService totaltime=6.551'''
        d = searcher._parse_log_parts('performance', line)
        assert d == {
            'totaltime': 6.551,
            'service_id': 'jb3:1a561d1e-a82d-430f-b639-93bf2481d534',
            'user': 'timothy.schailey@jefferson.edu',
            'service':
            'apps.caygd.stacks.trend.trendservice.LeaderboardService'
        }

    def test_parse_log_parts_recipe(self):
        searcher = JuiceboxLoggingSearcher()
        line = '''2019-04-17 00:02:20,305 [DEBUG] dataservices.recipe: service_id=jb3:6642a50c-325b-4c65-9360-3ca73298e1c0 user=binh.chung@juiceanalytics.com service=apps.preverity.stacks.individual.individualservice.RankedListService rows=8 db=0.018 enchant=0.000 cached=True  QUERYSTART SELECT juice.model_features.feature_friendly_name AS feature_friendly_name_id, juice.model_features.feature_friendly_name AS feature_friendly_name, juice.model_features.feature_name AS feature_name_id, juice.model_features.feature_name AS feature_name, juice.model_features.feature_order AS feature_order_id, juice.model_features.feature_order AS feature_order, max(juice.model_features.feature_value) AS feature_value FROM juice.model_features WHERE juice.model_features.npi = '1003809583' AND juice.model_features.prediction_year IN (2018) GROUP BY juice.model_features.feature_friendly_name, juice.model_features.feature_name, juice.model_features.feature_order ORDER BY juice.model_features.feature_order QUERYEND'''
        d = searcher._parse_log_parts('recipe', line)
        assert d == {
            'db':
            0.018,
            'query':
            "SELECT juice.model_features.feature_friendly_name AS feature_friendly_name_id, juice.model_features.feature_friendly_name AS feature_friendly_name, juice.model_features.feature_name AS feature_name_id, juice.model_features.feature_name AS feature_name, juice.model_features.feature_order AS feature_order_id, juice.model_features.feature_order AS feature_order, max(juice.model_features.feature_value) AS feature_value FROM juice.model_features WHERE juice.model_features.npi = '1003809583' AND juice.model_features.prediction_year IN (2018) GROUP BY juice.model_features.feature_friendly_name, juice.model_features.feature_name, juice.model_features.feature_order ORDER BY juice.model_features.feature_order ",
            'rows':
            8,
            'service':
            'apps.preverity.stacks.individual.individualservice.RankedListService',
            'service_id':
            'jb3:6642a50c-325b-4c65-9360-3ca73298e1c0',
            'user':
            'binh.chung@juiceanalytics.com'
        }

    def test_parse_log_parts_recipe_noquerymarkers(self):
        searcher = JuiceboxLoggingSearcher()
        line = '''2019-04-17 00:02:20,305 [DEBUG] dataservices.recipe: service_id=jb3:6642a50c-325b-4c65-9360-3ca73298e1c0 user=binh.chung@juiceanalytics.com service=apps.preverity.stacks.individual.individualservice.RankedListService rows=8 db=0.018 enchant=0.000 cached=True SELECT juice.model_features.feature_friendly_name AS feature_friendly_name_id, juice.model_features.feature_friendly_name AS feature_friendly_name, juice.model_features.feature_name AS feature_name_id, juice.model_features.feature_name AS feature_name, juice.model_features.feature_order AS feature_order_id, juice.model_features.feature_order AS feature_order, max(juice.model_features.feature_value) AS feature_value FROM juice.model_features WHERE juice.model_features.npi = '1003809583' AND juice.model_features.prediction_year IN (2018) GROUP BY juice.model_features.feature_friendly_name, juice.model_features.feature_name, juice.model_features.feature_order ORDER BY juice.model_features.feature_order'''
        d = searcher._parse_log_parts('recipe', line)
        assert d == {
            'db':
            0.018,
            'query':
            "SELECT juice.model_features.feature_friendly_name AS feature_friendly_name_id, juice.model_features.feature_friendly_name AS feature_friendly_name, juice.model_features.feature_name AS feature_name_id, juice.model_features.feature_name AS feature_name, juice.model_features.feature_order AS feature_order_id, juice.model_features.feature_order AS feature_order, max(juice.model_features.feature_value) AS feature_value FROM juice.model_features WHERE juice.model_features.npi = '1003809583' AND juice.model_features.prediction_year IN (2018) GROUP BY juice.model_features.feature_friendly_name, juice.model_features.feature_name, juice.model_features.feature_order ORDER BY juice.model_features.feature_order",
            'rows':
            8,
            'service':
            'apps.preverity.stacks.individual.individualservice.RankedListService',
            'service_id':
            'jb3:6642a50c-325b-4c65-9360-3ca73298e1c0',
            'user':
            'binh.chung@juiceanalytics.com'
        }

    def test_parse_log_parts_params(self):
        searcher = JuiceboxLoggingSearcher()
        line = '''2019-04-23 01:03:09,230 [DEBUG] dataservices.params: service_id=jb3:424b27e8-b122-4b02-9e62-b17eac1d88b8 user=taffe.bishop@tn.gov service=apps.tdoe_eplan.stacks.dashboard.dashboard_data_service.FilterService   User extra: { u'_initial_selections': { u'district_id': 700, u'school_id': u'700~0'}, u'_plan_external_id': u'5478', u'districts': [u'*'], u'is_priority': 0, u'schools': [u'*']} Request params: { u'benchmark_type': [u'benchmark'], u'district': [700], u'multiple_districts': [], u'school': [u'700~53']} Automatic filters: { 'district': [700], 'school': [u'700~53']} Custom filters: { 'benchmark_type': [u'benchmark'], 'district': [700], 'school': [u'700~53']}'''
        d = searcher._parse_log_parts('params', line)
        from pprint import pprint
        pprint(d)
        assert d == {
            'automatic_filters':
            "{ 'district': [700], 'school': [u'700~53']} ",
            'custom_filters':
            "{ 'benchmark_type': [u'benchmark'], 'district': [700], 'school': [u'700~53']}",
            'request_params':
            "{ u'benchmark_type': [u'benchmark'], u'district': [700], u'multiple_districts': [], u'school': [u'700~53']} ",
            'service':
            'apps.tdoe_eplan.stacks.dashboard.dashboard_data_service.FilterService',
            'service_id':
            'jb3:424b27e8-b122-4b02-9e62-b17eac1d88b8',
            'user':
            'taffe.bishop@tn.gov',
            'user_extra':
            "{ u'_initial_selections': { u'district_id': 700, u'school_id': u'700~0'}, u'_plan_external_id': u'5478', u'districts': [u'*'], u'is_priority': 0, u'schools': [u'*']} "
        }

    # @mock.patch.dict(os.environ, {'LP_USERNAME': 'foo', 'LP_PASSWORD': 'bar'})
    # @patch('elasticsearch.Elasticsearch')
    # @patch('elasticsearch_dsl.Search')
    # def test_search(self, mock_search, mock_es):
    #     mock_search.scan.return_value = []
    #     searcher = JuiceboxLoggingSearcher()
    #     searcher.search(username='foo', password='bar')
    #
    #     print(mock_es.mock_calls)
    #     print(mock_search.mock_calls)
