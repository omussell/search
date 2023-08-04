import logging
from datetime import datetime, timedelta
from flask import session
import core.constants as constants


def set_orcid_info(orcid_info):
    """
    Add or update orcid user info to session
    :param orcid_info: orcid info to save
    :return:
    """
    session[constants.ACCESS_TOKEN] = orcid_info['access_token']
    session[constants.USER_NAME] = orcid_info['name']
    session[constants.SESSION_ORCID] = orcid_info['orcid']
    session[constants.EXPIRES_AT] = orcid_info['expires_at']
    session.permanent = True
    expires = datetime.now() + timedelta(minutes=10)
    session['expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')


def get_orcid_info():
    """
    Get the Orcid profile information
    :return: orcid info
    """

    if constants.ACCESS_TOKEN in session and constants.USER_NAME in session and constants.SESSION_ORCID in session and \
       constants.EXPIRES_AT in session:
        return {constants.ACCESS_TOKEN: session[constants.ACCESS_TOKEN],
                constants.USER_NAME: session[constants.USER_NAME],
                constants.SESSION_ORCID: session[constants.SESSION_ORCID],
                constants.EXPIRES_AT: session[constants.EXPIRES_AT]}
    else:
        return None


def remove_user_info(token):
    """
    Remove user info from database
    :param token: user token
    :return:
    """
    try:
        OrcidUser.query.filter_by(session_token=token).delete()
    except Exception as exp:
        logging.exception("Error while deleting user info")
