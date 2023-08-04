from flask import render_template, flash, Response
from flask import Blueprint
from flask import request
import core.constants as constants
import core.service.search_service as service
import core.exceptions as exceptions
import logging as logger

search = Blueprint('search', __name__)

home = Blueprint('', __name__)

help = Blueprint('help', __name__)


@search.route('/works')
def works():
    if request.args and 'from_ui' not in request.args:
        return index()
    if request.args and 'q' in request.args:
        try:
            items, page = service.search_query(constants.CATEGORY_WORKS, request)
            page['name'] = constants.CATEGORY_WORKS
            return render_template("results.html", items=items, page=page)
        except exceptions.APIConnectionException as e:
            logger.exception(e)
            flash(constants.API_REQUEST_ERROR, constants.MESSAGE_TYPE_ERROR)
        except Exception as e:
            logger.exception(e)
            flash(constants.UNKNOWN_ERROR, constants.MESSAGE_TYPE_ERROR)

    page = {'name': constants.CATEGORY_WORKS}
    return render_template("splash.html", page=page)


@search.route('/funders')
def funders():
    try:
        if request.args and 'from_ui' not in request.args:
            return index()
        if request.args and 'q' in request.args:
            items = service.search_query(constants.CATEGORY_FUNDERS, request)
            return items

        elif request.args and 'id' in request.args:
            items, page = service.search_query(constants.CATEGORY_FUNDERS, request)
            page['name'] = constants.CATEGORY_FUNDERS
            return render_template("results.html", items=items, page=page)

    except exceptions.APIConnectionException as e:
        logger.exception(e)
        flash(constants.API_REQUEST_ERROR, constants.MESSAGE_TYPE_ERROR)
    except Exception as e:
        logger.exception(e)
        flash(constants.UNKNOWN_ERROR, constants.MESSAGE_TYPE_ERROR)

    page = {'name': constants.CATEGORY_FUNDERS}
    return render_template("funder_search.html", page=page)


@search.route('/download_csv')
def csv_download():
    items = service.all_funders_data(constants.CATEGORY_FUNDERS, request)
    csv_data = service.csv_data(items)
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
    return response


@search.route('/references', methods=['POST', 'GET'])
def references():
    if request.method == 'GET':
        page = {'name': constants.CATEGORY_REFERENCES}
        return render_template("references.html", page=page)
    else:
        try:
            page = service.search_references(request)
            page['name'] = constants.CATEGORY_REFERENCES
            return render_template("references_result.html", page=page)
        except exceptions.APIConnectionException as e:
            logger.exception(e)
            flash(constants.API_REQUEST_ERROR, constants.MESSAGE_TYPE_ERROR)
        except Exception as e:
            logger.exception(e)
            flash(constants.UNKNOWN_ERROR, constants.MESSAGE_TYPE_ERROR)


@home.route('/')
def index():
    page = {'name': constants.CATEGORY_WORKS}
    return render_template("splash.html", page=page)


@help.route('/works')
def works_help():
    page = {'name': constants.CATEGORY_HELP}
    return render_template("search_help.html", page=page)
