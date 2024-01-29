"""
ComicVine API Information & Documentation:
https://comicvine.gamespot.com/api/
https://comicvine.gamespot.com/api/documentation
"""
import json
import logging
from django.conf import settings

import requests

logger = logging.getLogger(__name__)


class ComicVineClient(object):
    """
    Interacts with the ``search`` resource of the ComicVine API. Requires an
    account on https://comicvine.gamespot.com/ in order to obtain an API key.
    """

    # All API requests made by this client will be made to this URL.
    API_URL = "https://www.comicvine.com/api/search/"

    # A valid User-Agent header must be set in order for our API requests to
    # be accepted, otherwise our request will be rejected with a
    # **403 - Forbidden** error.
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:7.0) "
        "Gecko/20130825 Firefox/36.0"
    }

    # A set of valid resource types to return in results.
    RESOURCE_TYPES = {
        "character",
        "issue",
        "location",
        "object",
        "person",
        "publisher",
        "story_arc",
        "team",
        "volume",
    }

    def __init__(self, api_key, expire_after=300):
        """
        Store the API key in a class variable, and install the requests cache,
        configuring it using the ``expire_after`` parameter.

        :param api_key: Your personal ComicVine API key.
        :type  api_key: str
        :param expire_after: The number of seconds to retain an entry in cache.
        :type  expire_after: int or None
        """

        self.api_key = api_key

    def search(self, query, offset=0, limit=10, resources=None):
        """
        Perform a search against the API, using the provided query term. If
        required, a list of resource types to filter search results to can
        be included.

        Take the JSON contained in the response and provide it to the custom
        ``Response`` object's constructor. Return the ``Response`` object.

        :param query: The search query with which to make the request.
        :type  query: str
        :param offset: The index of the first record returned.
        :type  offset: int or None
        :param limit: How many records to return **(max 10)**
        :type  limit: int or None
        :param resources: A list of resources to include in the search results.
        :type  resources: list or None
        :type  use_cache: bool

        :return: The response object containing the results of the search
                 query.
        :rtype:  comicvine_search.response.Response
        """

        params = self._request_params(query, offset, limit, resources)
        json_data = self._query_api(params)

        return json_data

    def _request_params(self, query, offset, limit, resources):
        """
        Construct a dict containing the required key-value pairs of parameters
        required in order to make the API request.

        The documentation for the ``search`` resource can be found at
        https://comicvine.gamespot.com/api/documentation#toc-0-30.

        Regarding 'limit', as per the documentation:

            The number of results to display per page. This value defaults to
            10 and can not exceed this number.

        :param query: The search query with which to make the request.
        :type  query: str
        :param offset: The index of the first record returned.
        :type  offset: int
        :param limit: How many records to return **(max 10)**
        :type  limit: int
        :param resources: A list of resources to include in the search results.
        :type  resources: list or None

        :return: A dictionary of request parameters.
        :rtype:  dict
        """

        return {
            "api_key": self.api_key,
            "format": "json",
            "limit": min(10, limit),  # hard limit of 10
            "offset": max(0, offset),  # cannot provide negative offset
            "query": query,
            "resources": self._validate_resources(resources),
        }

    def _validate_resources(self, resources):
        """
        Provided a list of resources, first convert it to a set and perform an
        intersection with the set of valid resource types, ``RESOURCE_TYPES``.
        Return a comma-separted string of the remaining valid resources, or
        None if the set is empty.

        :param resources: A list of resources to include in the search results.
        :type  resources: list or None

        :return: A comma-separated string of valid resources.
        :rtype:  str or None
        """

        if not resources:
            return None

        valid_resources = self.RESOURCE_TYPES & set(resources)
        return ",".join(valid_resources) if valid_resources else None

    def _query_api(self, params):
        """
        Query the ComicVine API's ``search`` resource, providing the required
        headers and parameters with the request. Optionally allow the caller
        of the function to disable the request cache.

        If an error occurs during the request, handle it accordingly. Upon
        success, return the JSON from the response.

        :param params: Parameters to include with the request.
        :type  params: dict
        :param use_cache: Toggle the use of requests_cache.
        :type  use_cache: bool

        :return: The JSON contained in the response.
        :rtype:  dict
        """

        # Since we're performing the identical action regardless of whether
        # or not the request cache is to be used, store the procedure in a
        # local function to avoid repetition.
        def __httpget():
            response = requests.get(
                self.API_URL, headers=self.HEADERS, params=params
            )

            if not response.ok:
                self._handle_http_error(response)

            return response.json()

        return __httpget()

    def _handle_http_error(self, response):
        """
        Provided a ``requests.Response`` object, if the status code is
        anything other than **200**, we will treat it as an error.

        Using the response's status code, determine which type of exception to
        raise. Construct an exception message from the response's status code
        and reason properties before raising the exception.

        :param response: The requests.Response object returned by the HTTP
                         request.
        :type  response: requests.Response

        :raises ComicVineUnauthorizedException: if no API key provided.
        :raises ComicVineForbiddenException: if no User-Agent header provided.
        :raises ComicVineApiException: if an unidentified error occurs.
        """

        exception = {
            401: Exception,
            403: Exception,
        }.get(response.status_code, Exception)
        message = f"{response.status_code} {response.reason}"

        raise exception(message)


def lookup_comic_from_comicvine(title: str) -> dict:
    api_key = getattr(settings, "COMICVINE_API_KEY", "")
    if not api_key:
        logger.warn("No ComicVine API key configured, not looking anything up")
        return {}

    client = ComicVineClient(
        api_key=getattr(settings, "COMICVINE_API_KEY", None)
    )
    return client.search(title)
    results = [
        r
        for r in client.search(title).get("results")
        if r.get("resource_type") == "volume"
    ]

    return results
    """
    {
        "title": top.get("title"),
        "isbn": isbn,
        "comicvine_id": ol_id,
        "first_publish_year": top.get("first_publish_year"),
        "first_sentence": first_sentence,
        "pages": top.get("number_of_pages_median", None),
        "cover_url": COVER_URL.format(id=ol_id),
        "cv_author_id": ol_author_id,
        "subject_key_list": top.get("subject_key", []),
    }

    """
