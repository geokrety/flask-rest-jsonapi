# -*- coding: utf-8 -*-

import json

from flask_rest_jsonapi.exceptions import BadRequest, InvalidFilters, InvalidSort, InvalidInclude


class QueryStringManager(object):
    """Querystring parser according to jsonapi reference
    """

    MANAGED_KEYS = (
        'filter',
        'page',
        'fields',
        'sort',
        'include'
    )

    def __init__(self, querystring):
        """Initialization instance

        :param dict querystring: query string dict from request.args
        """
        if not isinstance(querystring, dict):
            raise ValueError('QueryStringManager require a dict-like object query_string parameter')

        self.qs = querystring

    def _get_key_values(self, index):
        """Return a dict containing key / values items for a given key, used for items like filters, page, etc.

        :param str index: index to use for filtering
        :return dict: a dict of key / values items
        """
        results = {}

        for key, value in self.qs.items():
            try:
                if not key.startswith(index):
                    continue

                key_start = key.index('[') + 1
                key_end = key.index(']')
                item_key = key[key_start:key_end]

                if ',' in value:
                    item_value = value.split(',')
                else:
                    item_value = value
                results.update({item_key: item_value})
            except Exception:
                raise BadRequest({'parameter': key}, "Parse error")

        return results

    @property
    def querystring(self):
        """Return original querystring but containing only managed keys

        :return dict: dict of managed querystring parameter
        """
        return {key: value for (key, value) in self.qs.items() if key.startswith(self.MANAGED_KEYS)}

    @property
    def filters(self):
        """Return filters from query string.

        :return list: filter information
        """
        filters = self.qs.get('filters')
        if filters is not None:
            try:
                filters = json.loads(filters)
            except (ValueError, TypeError):
                raise InvalidFilters("Parse error")

            if not isinstance(filters, list):
                raise InvalidFilters("Must be a list")

        return filters

    @property
    def pagination(self):
        """Return all page parameters as a dict.

        :return dict: a dict of pagination information

        To allow multiples strategies, all parameters starting with `page` will be included. e.g::

            {
                "number": '25',
                "size": '150',
            }

        Example with number strategy::

            >>> query_string = {'page[number]': '25', 'page[size]': '10'}
            >>> parsed_query.pagination
            {'number': '25', 'size': '10'}
        """
        # check values type
        result = self._get_key_values('page', multiple_values=False)
        for key, value in result.items():
            try:
                int(value)
            except ValueError:
                raise BadRequest({'parameter': 'page[%s]' % key}, "Parse error")

        return result

    @property
    def fields(self):
        """Return fields wanted by client.

        :return dict: a dict of sparse fieldsets information

        Return value will be a dict containing all fields by resource, for example::

            {
                "user": ['name', 'email'],
            }

        """
        return self._get_key_values('fields')

    @property
    def sorting(self):
        """Return fields to sort by including sort name for SQLAlchemy and row
        sort parameter for other ORMs

        :return list: a list of sorting information

        Example of return value::

            [
                {'field': 'created_at', 'order': 'desc'},
            ]

        """
        if self.qs.get('sort'):
            try:
                sorting_results = []
                for sort_field in self.qs['sort'].split(','):
                    field = sort_field.replace('-', '')
                    order = 'desc' if sort_field.startswith('-') else 'asc'
                    sorting_results.append({'field': field, 'order': order})
            except Exception:
                raise InvalidSort("Parse error")

        return []

    @property
    def include(self):
        """Return fields to include

        :return list: a list of include information
        """
        include_param = self.qs.get('include')
        try:
            return include_param.split(',') if include_param else []
        except Exception:
            raise InvalidInclude("Parse error")
