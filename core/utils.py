import time

from flask import session, request
from datetime import datetime


from core.service import auth_service
import logging as logger

CONFIG = None
BASE_ROOT = None
HOST_URL = None


def prepare_api_headers(request_or_ip=None):
    """Return API headers with X-Forwarded-For from request if enabled."""
    from settings import API_HEADERS, FORWARD_CLIENT_IP
    
    headers = API_HEADERS.copy()
    
    if not FORWARD_CLIENT_IP or not request_or_ip:
        return headers
    
    if isinstance(request_or_ip, str):
        headers['X-Forwarded-For'] = request_or_ip
    elif hasattr(request_or_ip, 'headers'):
        xff = request_or_ip.headers.get('X-Forwarded-For')
        if xff:
            headers['X-Forwarded-For'] = xff
    
    return headers


def get_doi_url(doi):
    return "https://doi.org/" + doi


def signed_in_info():
    """Checks if the user is signed in and returns user info
    :return: True, user info if signed in else False and None. True if session expired.
    """
    orcid_info = auth_service.get_orcid_info()
    if orcid_info:
        time_now = time.time()
        if orcid_info["expires_at"] <= time_now:
            expired_at_human_readable = datetime.fromtimestamp(orcid_info["expires_at"]).strftime('%Y-%m-%d %H:%M:%S')
            logger.error("Orcid session expired. Expired at: " + orcid_info["expires_at"] + " " + expired_at_human_readable)
            logout()
            # returns signed_in, orcid_info and expired
            return False, None, True
        else:
            return True, orcid_info, False

    else:
        return False, None, False


def logout():
    session.clear()


def set_app_config(app_config):
    global CONFIG
    CONFIG = app_config


def get_app_config(key):
    if CONFIG:
        return CONFIG.get(key)
    return None


def set_base_path(app_root):
    global BASE_ROOT
    BASE_ROOT = app_root


def get_base_path():
    return BASE_ROOT


def set_host_url(host_url):
    global HOST_URL
    HOST_URL = host_url


def get_host_url():
    return HOST_URL

def get_request_data():
    if request.is_json:
        return request.json
    elif request.data:
        return f"Raw data: {request.data.decode('utf-8')}"
    elif request.form:
        return f"Form data: {request.form}"
    elif request.args:
        return f"Query parameters: {request.args}"
    else:
        return "No data in request"


class DOIRecordParser:
    def __init__(self, doi_record) -> None:
        self.doi_record = doi_record

    def parse_doi_record(self):
        title = self.doi_record["title"][0] if "title" in self.doi_record and self.doi_record["title"] and \
                len(self.doi_record["title"]) > 0 else None
        container_title = self.doi_record["container-title"][0] if "container-title" in self.doi_record and \
                          self.doi_record["container-title"] and len(self.doi_record["container-title"]) > 0 else None
        type = self.doi_record["type"] if "type" in self.doi_record else None
        doi = self.doi_record["DOI"] if "DOI" in self.doi_record else None
        url = self.doi_record["URL"] if "URL" in self.doi_record else None

        return {
            "title": title,
            "container_title": container_title,
            "type": type,
            "doi": doi,
            "url": url,
        }
