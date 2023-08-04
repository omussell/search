from flask import Blueprint
from flask import redirect, render_template, request, session, abort
import requests
import time
import logging
import json
from oauthlib.oauth2 import WebApplicationClient

from core import constants, utils, exceptions
from core.service import auth_service

auth = Blueprint('auth', __name__)
orcid = Blueprint('orcid', __name__)


@auth.route("/orcid")
def orcid_redirect():
    """
    Signin to orcid. Redirects to orcid site.
    :return:
    """
    utils.set_host_url(request.host_url)
    client = WebApplicationClient(utils.get_app_config('ORCID_CLIENT_ID'))
    url = client.prepare_request_uri(utils.get_app_config('ORCID_AUTHORIZE_URL'),
                                     redirect_uri=utils.get_host_url() + constants.ORCID_REDIRECT_URL,
                                     scope="/authenticate /activities/update")
    return redirect(url)


@auth.route("/orcid/callback")
def orcid_callback():
    """
    Callback for orcid signin.
    :return:
    """
    if 'code' in request.args:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = 'client_id=' + utils.get_app_config('ORCID_CLIENT_ID') + \
               '&client_secret=' + utils.get_app_config('ORCID_CLIENT_SECRET') + \
               '&grant_type=authorization_code&' \
               '&redirect_uri=' + utils.get_host_url() + constants.ORCID_REDIRECT_URL + request.args['token'] + \
               '&code=' + request.args["code"]

        response = requests.post(utils.get_app_config('ORCID_TOKEN_URL'), headers=headers, data=data, verify=False)
        if response.status_code == 200:

            res_json = response.json()
            res_json['expires_at'] = int(time.time()) + res_json['expires_in']

            auth_service.set_orcid_info(res_json)

            return render_template("auth_callback.html")
        else:
            logging.error("Error in orcid authorization response: status code: " +
                         str(response.status_code) + ' message: ' + response.text)
            abort(400)

    else:
        logging.error("Error in the orcid call back " + request.json())
        abort(400)


def extract_orcid_dois(account_info):
    """
    Get all the dois claimed by the user
    :param account_info: User orcid account info
    :return:
    """
    extracted_dois = []

    headers = {
        'Accept': 'application/vnd.orcid+json',
        'Authorization': 'Bearer ' + account_info['access_token']
    }

    try:
        response = requests.get(utils.get_app_config('ORCID_MEMBER_URL') + account_info['orcid'] + "/works",
                                headers=headers, verify=False)
    except Exception as e:
        logging.exception(e)
        raise exceptions.APIConnectionException(e)

    if response.status_code == 200:
        res_json = response.json()

        if 'group' in res_json:
            works = res_json['group']

            for work_loc in works:
                if 'external-ids' in work_loc:
                    if 'external-id' in work_loc['external-ids']:
                        ids_loc = work_loc['external-ids']['external-id']
                        for id_loc in ids_loc:
                            id_type = id_loc['external-id-type']
                            id_val = id_loc['external-id-value']

                            if id_type.upper() == 'DOI':
                                extracted_dois.append(id_val.casefold())
    else:
        logging.error("API returns error. Status Code : " + str(response.status_code) + " - Message : " +
                     response.text)

    return extracted_dois


def create_orcid_json_item(doi_record):
    """
    Convert doi record to Orcid json record to claim
    :param doi_record: doi record
    :return: list of dois claimed
    """
    parser = utils.DOIRecordParser(doi_record)
    record = parser.parse_doi_record()
    orcid_record = {"title": {"title": {"value": record['title']}}}
    if 'container_title' in record and record['container_title']:
        orcid_record["journal-title"] = {"value": record['container_title']}
    if 'type' in record and record['type']:
        orcid_record["type"] = record['type']
    if 'doi' in record and record['doi']:
        orcid_record["external-ids"] = {"external-id": [{"external-id-type": "doi", "external-id-value": record['doi'],
                            "external-id-url": {"value": record['url']}, "external-id-relationship": "self"}]}

    return json.dumps(orcid_record)


@orcid.route("/claim")
def claim():
    """
    Claim the doi
    :return:
    """
    status = None
    signed_in, orcid_info, session_expired = utils.signed_in_info()

    if signed_in and 'doi' in request.args:
        doi = request.args['doi']

        if orcid_info:

            extracted_dois = extract_orcid_dois(orcid_info)

            if doi.casefold() in extracted_dois:
                status = 'ok'
            else:
                url = constants.WORKS_API_URL + "/" + doi
                try:
                    res = requests.get(url, timeout=constants.REQUEST_TIME_OUT)
                except Exception as e:
                    logging.exception(e)
                    raise exceptions.APIConnectionException(e)

                if res.status_code == 200:
                    doi_record = None
                    response_json = res.json()
                    if response_json["message"]:
                        doi_record = response_json["message"]
                    if doi_record:
                        json_record = create_orcid_json_item(doi_record)

                        headers = {
                            'Accept': 'application/vnd.orcid+json',
                            'Authorization': 'Bearer ' + orcid_info['access_token'],
                            'Content-Type': 'application/vnd.orcid+json'
                        }

                        try:
                            response = requests.post(utils.get_app_config('ORCID_MEMBER_URL') +
                                                     orcid_info['orcid'] + "/work",
                                                     data=json_record, headers=headers, verify=False)
                        except Exception as e:
                            logging.exception(e)
                            raise exceptions.APIConnectionException(e)

                        if response.status_code == 201:
                            extracted_dois = extract_orcid_dois(orcid_info)
                            if doi.casefold() in extracted_dois:
                                status = 'ok_visible'
                            else:
                                status = 'ok'
                        elif response.status_code == 500:
                            logging.error("Error while adding item : " + response.text)
                            return {"status": "error", "text": "ORCID Serverside error. Item not added to ORCID"}
                        else:
                            logging.error("Error while adding item : " + response.text)
                            return {"status": "error", "text": "Unknown error occurred. Item not added to ORCID"}

                    else:
                        status = 'no_such_doi'
                else:
                    status = 'no_such_doi'

    return {"status": status}


@orcid.route("/dois")
def dois_info():
    """
    Check and return dois if claimed by the user
    :return: dictionary of dois along with status if claimed
    """
    dois = request.args['dois']
    signed_in, orcid_info, session_expired = utils.signed_in_info()

    dois_status = {}
    if signed_in:
        dois_list = dois.split(",")
        if orcid_info:
            extracted_dois = extract_orcid_dois(orcid_info)
            for doi in dois_list:
                if doi.casefold() in extracted_dois:
                    dois_status[doi] = "claimed"
                else:
                    dois_status[doi] = "not_claimed"

    return json.dumps(dois_status)


@auth.route("/signout")
def logout():
    utils.logout()
    if 'redirect_uri' in request.args:
        return redirect(request.args['redirect_uri'])
    else:
        return redirect("/")
