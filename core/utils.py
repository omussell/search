from flask import session
import uuid
import time
import core.constants as constants
from core.service import auth_service

CONFIG = None
BASE_ROOT = None
HOST_URL = None


def get_doi_url(doi):
    return "https://doi.org/" + doi


def signed_in_info():
    """
    Checks if the user is signed in and returns user info
    :return: True, user info if signed in else False and None. True if session expired
    """
    orcid_info = auth_service.get_orcid_info()
    if orcid_info:
        time_now = time.time()
        if orcid_info['expires_at'] <= time_now:
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


class DOIRecordParser:
    def __init__(self, doi_record):
        self.doi_record = doi_record

    def parse_doi_record(self):
        title = self.doi_record['title'][0] if 'title' in self.doi_record and self.doi_record['title'] and \
                len(self.doi_record['title']) > 0 else None
        container_title = self.doi_record['container-title'][0] if 'container-title' in self.doi_record and \
                          self.doi_record['container-title'] and len(self.doi_record['container-title']) > 0 else None
        type = self.doi_record['type'] if 'type' in self.doi_record else None
        doi = self.doi_record['DOI'] if 'DOI' in self.doi_record else None
        url = self.doi_record['URL'] if 'URL' in self.doi_record else None

        return {
            'title': title,
            'container_title': container_title,
            'type': type,
            'doi': doi,
            'url': url
        }
