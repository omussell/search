
import logging

import requests
import core.constants as constants
import calendar
import csv
import furl
from flask_paginate import Pagination, get_page_parameter

import core.utils as utils
import core.exceptions as exceptions


def sort_type(request):
    sort_by = 'relevance'
    if 'sort' in request.args:
        sort_by = request.args['sort']

    return sort_by


def get_api_url(category, request):
    """
    Return the Crossref API url depending on the category
    :param category: API category
    :param query: api query parameter
    :return:
    """

    url = None
    params = {}
    search_type = None

    sort_by = sort_type(request)
    if sort_by == 'year':
        sort_by = 'published'

    rows = constants.ROWS_PER_PAGE
    if 'format' in request.args:
        rows = constants.MAX_ROWS

    if category == constants.CATEGORY_WORKS:
        if 'q' in request.args:
            query = request.args['q'].strip()

            if constants.DOI_REGEX.match(query):
                url = constants.WORKS_API_URL + "/" + query
                search_type = constants.SEARCH_TYPE_DOI
            elif constants.ISSN_REGEX.match(query):
                url = constants.JOURNALS_API_URL.format(query)
                search_type = constants.SEARCH_TYPE_ISSN
            elif constants.ORCID_REGEX.match(query):
                url = constants.BASE_API_URL + "works?filter=orcid:{" + query + "}"
                search_type = constants.SEARCH_TYPE_ORCID
            else:
                url = constants.WORKS_API_URL + "?query=" + query
                params['sort'] = sort_by
                params['rows'] = str(rows)

    elif category == constants.CATEGORY_FUNDERS:
        if 'q' in request.args:
            url = constants.FUNDERS_API_URL + "?query=" + request.args['q']
        elif 'id' in request.args:
            url = constants.FUNDER_WORKS_API_URL.format(request.args['id'])
            params['sort'] = sort_by
        params['rows'] = str(rows)

    if 'page' in request.args:
        page_value = int(request.args['page'])
        offset = (page_value - 1) * rows
        params['offset'] = str(offset)

    if 'publisher' in request.args:
        params['query.container-title'] = request.args['publisher']

    return furl.furl(url).add(params), search_type


def get_request_url(request, exclude):
    """
    Return the request url removing the exclude parameters from query string
    :param request: request object
    :param exclude: array of exclude parameters
    :return:
    """
    f = furl.furl(request.url)
    if isinstance(exclude, list):
        f.remove(exclude)
    elif isinstance(exclude, str):
        f.remove(exclude.split(','))
    return f.url


def get_pagination_url(request):
    url = get_request_url(request, ['page'])
    url += '&page={0}'
    return url


def format_item_type(item):
    item_type = None
    if "type" in item:
        item_type = item["type"]
        item_type = item_type.replace('-', ' ').upper()
    return item_type


def add_published_date(item, row):
    published = None
    if "published-print" in item:
        published = item["published-print"]
    elif "published-online" in item:
        published = item["published-online"]

    if published:
        if "date-parts" in published:
            date_parts = published["date-parts"][0]
            date_parts_len = len(date_parts)
            published_date = ""
            if date_parts_len > 2:
                published_date = str(date_parts[2]) + " "
            if date_parts_len > 1:
                published_date += calendar.month_name[date_parts[1]] + " "
            if date_parts_len > 0:
                published_date += str(date_parts[0])
                row['year'] = str(date_parts[0])

            row['published_date'] = published_date


def add_publication(item, row):
    if "container-title" in item and len(item["container-title"]) > 0:
        container_title = item["container-title"][0]

        row['publication'] = container_title


def add_alternative_id(item, row):
    if 'alternative-id' in item:
        row['supplementary_ids'] = item['alternative-id']


def add_doi(item, row):
    if 'DOI' in item:
        row["display_doi"] = utils.get_doi_url(item['DOI'])
        doi = item['DOI']
        row["doi"] = doi

        if doi.startswith('10.5555') or doi.startswith('10.55555'):
            row["test_doi"] = True
        else:
            row["test_doi"] = False


def add_grant_info(item, row):
    if 'funder' in item:
        funders = []
        awards = []
        funder_names = []
        for funder in item['funder']:
            if 'name' in funder:
                funder_names.append(funder['name'])
            if 'name' in funder and 'award' in funder:
                awards.append(",".join(funder['award']))
                funders.append(funder['name'] + " (" + ",".join(funder['award']) + ")")
        if len(funders) > 0:
            row['grant_info'] = " | ".join(funders)
        if len(awards) > 0:
            row['awards'] = ",".join(awards)
        if len(funder_names) > 0:
            row['funders'] = ",".join(funder_names)


def add_names(items_list, item_name, row):
    if items_list:
        items = []
        for item in items_list:
            name = None
            if 'name' in item:
                name = item['name']
            elif 'given' in item and 'family' in item:
                name = item['given'] + " " + item['family']
            elif 'given' in item:
                name = item['given']
            if name:
                items.append(name)
        if len(items) > 0:
            row[item_name] = " | ".join(items)
            row[item_name+'_csv'] = ",".join(items)


def add_people(item, row):
    add_names(item['editor'] if 'editor' in item else None, 'editors', row)
    add_names(item['author'] if 'author' in item else None, 'authors', row)
    add_names(item['chair'] if 'chair' in item else None, 'chairs', row)
    add_names(item['translator'] if 'translator' in item else None, 'translators', row)


def add_supplementary_id(item, row):
    if 'alternative-id' in item:
        row['supplementary_ids'] = " | ".join(item['alternative-id'])


def add_id(item, row):
    if 'id' in item:
        row['id'] = item['id']


def add_location(item, row):
    if 'location' in item:
        row['location'] = item['location']


def add_title(item, row):
    if 'title' in item:
        row['title'] = item["title"][0].replace("\\", "") if 'title' in item else ''


def add_name(item, row):
    if 'name' in item:
        row['name'] = item['name']


def add_type(item, row):
    if "type" in item:
        item_type = item["type"]
        row['type'] = item_type.replace('-', ' ').upper()


def add_item_data(item, row):
    add_type(item, row)
    add_published_date(item, row)
    add_publication(item, row)
    add_alternative_id(item, row)
    add_title(item, row)
    add_name(item, row)
    add_id(item, row)
    add_location(item, row)
    add_doi(item, row)
    add_grant_info(item, row)
    add_people(item, row)
    add_supplementary_id(item, row)


def get_items(obj):
    items = []
    total = 0
    if obj['message-type'] == 'funder-list' or obj['message-type'] == 'work-list':
        if obj["message"]["total-results"]:
            total = obj["message"]["total-results"]
        if obj["message"]["items"]:
            for item in obj["message"]["items"]:
                row = {}
                add_item_data(item, row)
                items.append(row)
    elif obj['message-type'] == 'funder' or obj['message-type'] == 'work':
        item = obj["message"]
        row = {}
        add_item_data(item, row)
        items.append(row)
        total = 1

    return items, total


def get_query_string(request, category):
    if category == constants.CATEGORY_WORKS:
        if 'q' in request.args:
            return request.args['q']

    elif category == constants.CATEGORY_FUNDERS:
        if 'id' in request.args:
            res = requests.get(constants.FUNDER_INFO_API_URL.format(request.args['id']),
                               timeout=constants.REQUEST_TIME_OUT)
            res = res.json()
            if 'message' in res:
                if 'name' in res['message']:
                    return res['message']['name']
    return ""


def search_query(category, request):
    url, search_type = get_api_url(category, request)
    try:
        logging.debug("Search URL : " + str(url))
        res = requests.get(url, timeout=constants.REQUEST_TIME_OUT)
        logging.debug("Response Code : " + str(res.status_code))
    except Exception as e:
        raise exceptions.APIConnectionException(e)

    if res.status_code == 200:
        page_number = request.args.get(get_page_parameter(), type=int, default=1)
        max_results_to_display = constants.ROWS_PER_PAGE * 10

        # If page is greater than 10, show max limit message
        if int(page_number) > constants.PAGINATION_PAGE_LIMIT:
            items = []
            total = max_results_to_display + 1
        else:
            items, total = get_items(res.json())

        total_rows = total
        # Restrict the pages to 10. If the user tries to access the 11th page display
        # a message regarding limitation

        if total > max_results_to_display:
            total_rows = max_results_to_display + 1
        # set pagination max to 11 pages
        pagination = Pagination(page=page_number, total=total_rows, search=False, per_page=constants.ROWS_PER_PAGE,
                                href=get_pagination_url(request))
        page = {'pagination': pagination,
                'sort_url': get_request_url(request, ['sort']),
                'publisher_url': get_request_url(request, ['publisher']),
                'sort_type': sort_type(request),
                'api_url': constants.WORKS_API_URL,
                'query': get_query_string(request, category),
                'search_type': search_type
                }

        if int(page_number) <= constants.PAGINATION_PAGE_LIMIT:
            page['total'] = str(total)

        if category == constants.CATEGORY_FUNDERS and 'id' in request.args:
            page['funder_id'] = request.args['id']

        return items, page

    else:
        logging.error("Error while getting the results: Response Code: " + str(res.status_code) + " Description: "
                      + res.text)
        raise exceptions.APIConnectionException()


def resolve_references(citation_texts):
    page = {}
    if len(citation_texts) > constants.MAX_MATCH_TEXTS:
        page = {"results": [],
                "query_ok": False,
                "reason": "Too many citations. Maximum is" + str(constants.MAX_MATCH_TEXTS)
                }
    else:
        results = []
        for citation_text in citation_texts:
            if len(citation_text.split()) < constants.MIN_MATCH_TERMS:
                results.append({
                    "text": citation_text,
                    "match": False,
                    "reason": 'Too few terms',
                })
            else:
                url = constants.WORKS_API_URL
                url = furl.furl(url).add(args={'query': citation_text, 'rows': 1}).url
                res = requests.get(url, timeout=constants.REQUEST_TIME_OUT)
                if res.status_code == 200:
                    res = res.json()
                    if 'message' in res:
                        if 'items' in res['message']:
                            if len(res['message']['items']) > 0:
                                item = res['message']['items'][0]
                                if item['score'] < constants.MIN_MATCH_SCORE:
                                    results.append({
                                        "text": citation_text,
                                        "match": False,
                                        "reason": 'Result score too low',
                                    })
                                else:
                                    results.append({
                                        "text": citation_text,
                                        "match": True,
                                        "doi": item['URL'],
                                        "score": item['score']
                                    })

        page = {"results": results, "query_ok": True}

    return page


def search_references(request):
    refs_text = request.form.get('references').strip()

    if refs_text:
        refs = [line for line in refs_text.split("\n") if line.strip() != '']
        return resolve_references(refs)

    return None


def all_funders_data(category, request):
    total_pages = 1
    page = 1
    all_items = []
    while page <= total_pages:
        url, search_type = get_api_url(category, request)
        try:
            res = requests.get(url, timeout=constants.REQUEST_TIME_OUT)
        except Exception as e:
            raise exceptions.APIConnectionException(e)

        if res.status_code == 200:
            items, total = get_items(res.json())
            total_pages = -(total // -constants.MAX_ROWS)

            all_items += items

            page += 1

    return all_items


class Line(object):
    def __init__(self):
        self._line = None

    def write(self, line):
        self._line = line

    def read(self):
        return self._line


def csv_data(items):
    """
    Writes data to CSV format
    :param items: data
    :return:
    """
    fields = ['display_doi', 'type', 'year', 'title', 'publication', 'authors_csv', 'funders', 'awards']
    line = Line()

    writer = csv.DictWriter(line, fieldnames=fields, extrasaction='ignore')
    writer.writerow({'display_doi': 'DOI', 'type': 'Type', 'year': 'Year', 'title': 'Title', 'publication': 'Publication',
                     'authors_csv': 'Authors', 'funders': 'Funders', 'awards': 'Awards'})
    yield line.read()
    for item in items:
        writer.writerow(item)
        yield line.read()
