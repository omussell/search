import json
import logging
import time

import requests
from core.service.orcid_service import create_orcid_claim_json, extract_orcid_dois
from core.ip_utils import get_client_ip
from core.utils import prepare_api_headers
from flask import Blueprint, abort, redirect, render_template, request
from oauthlib.oauth2 import WebApplicationClient
from core.utils import get_request_data
from settings import API_HEADERS

from core import constants, exceptions, utils
from core.service import auth_service

auth = Blueprint("auth", __name__)
orcid = Blueprint("orcid", __name__)


@auth.route("/orcid")
def orcid_redirect():
    """Signin to orcid. Redirects to orcid site.
    :return:
    """
    utils.set_host_url(request.host_url)
    client = WebApplicationClient(utils.get_app_config("ORCID_CLIENT_ID"))
    url = client.prepare_request_uri(utils.get_app_config("ORCID_AUTHORIZE_URL"),
                                     redirect_uri=utils.get_host_url() + constants.ORCID_REDIRECT_URL,
                                     scope="/read-limited /activities/update")
    return redirect(url)


@auth.route("/orcid/search-and-link")
@auth.route("/orcid/callback")
def orcid_callback():
    """Callback for orcid signin.
    :return:
    """
    utils.set_host_url(request.host_url)
    if "code" in request.args:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        if request.path == '/auth/orcid/search-and-link':
            redirect_uri = utils.get_host_url() + constants.ORCID_SEARCH_AND_LINK_REDIRECT_URL
        else:
            redirect_uri = utils.get_host_url() + constants.ORCID_REDIRECT_URL

        data = "client_id=" + utils.get_app_config("ORCID_CLIENT_ID") + \
               "&client_secret=" + utils.get_app_config("ORCID_CLIENT_SECRET") + \
               "&grant_type=authorization_code" \
               "&redirect_uri=" + redirect_uri + \
               "&code=" + request.args["code"]

        response = requests.post(utils.get_app_config(
            "ORCID_TOKEN_URL"), headers=headers, data=data, verify=False)
        if response.status_code == 200:

            res_json = response.json()
            res_json["expires_at"] = int(time.time()) + res_json["expires_in"]

            auth_service.set_orcid_info(res_json)

            if request.path == '/auth/orcid/search-and-link':
                return render_template("splash.html")
            else:
                return render_template("auth_callback.html")

        else:
            logging.error("Error in orcid authorization response: status code: " +
                          str(response.status_code) + " message: " + response.text +
                          " | redirect_uri: " + redirect_uri)
            abort(400)
            return None

    else:
        logging.error("Error in the orcid call back " + get_request_data())
        abort(400)
        return None


@orcid.route("/claim")
def claim():
    """Claim the doi
    :return:
    """
    status = None
    signed_in, orcid_info, session_expired = utils.signed_in_info()
    client_ip = get_client_ip(request)

    if signed_in and "doi" in request.args:
        doi = request.args["doi"]

        if orcid_info:
            try:
                extracted_dois = extract_orcid_dois(orcid_info)
            except exceptions.OrcidAPINotFoundException as e:
                logging.error(str(e))
                return {"status": "error", "message": "DOI not found"}, 404
            except exceptions.OrcidAPIUnauthorizedException as e:
                logging.error(str(e))
                return {"status": "error", "message": "Unauthorized access"}, 401
            except exceptions.OrcidAPIException as e:
                logging.error(str(e))
                return {"status": "error", "message": "ORCID API error"}, 500

            if doi.casefold() in extracted_dois:
                status = "ok"
            else:
                url = constants.WORKS_API_URL + "/" + doi
                try:
                    res = requests.get(
                        url, timeout=constants.REQUEST_TIME_OUT, headers=prepare_api_headers(client_ip))

                except Exception as e:
                    logging.exception(
                        f"Exception during GET request to {url}: {e}")
                    raise exceptions.APIConnectionException(e)

                if res.status_code == 200:
                    doi_record = None
                    response_json = res.json()
                    if response_json["message"]:
                        doi_record = response_json["message"]
                    if doi_record:
                        json_record = create_orcid_claim_json(doi_record, client_ip=client_ip)

                    # Attempt the submission to Orcid
                    try:
                        post_url = utils.get_app_config(
                            "ORCID_MEMBER_URL") + orcid_info["orcid"] + "/work"
                        headers = {
                            "Accept": "application/vnd.orcid+json",
                            "Authorization": "Bearer " + orcid_info["access_token"],
                            "Content-Type": "application/vnd.orcid+json",
                        }

                        response = requests.post(
                            post_url, data=json_record, headers=headers, verify=False)

                        if response.status_code == 201:
                            extracted_dois = extract_orcid_dois(orcid_info)
                            if doi.casefold() in extracted_dois:
                                status = "ok_visible"
                            else:
                                status = "ok"

                    except Exception as e:
                        logging.exception(
                            f"Exception during POST request to {post_url}: {e}")
                        raise exceptions.APIConnectionException(e)

                else:
                    status = "no_such_doi"
    return {"status": status}


@orcid.route("/dois")
def dois_info():
    """Check and return dois if claimed by the user
    :return: dictionary of dois along with status if claimed.
    """
    dois = request.args["dois"]
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
    if "redirect_uri" in request.args:
        return redirect(request.args["redirect_uri"])
    else:
        return redirect("/")
