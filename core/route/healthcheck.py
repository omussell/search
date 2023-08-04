from flask import Blueprint, Response

healthcheck = Blueprint('healthcheck', __name__)

@healthcheck.route('')
def heartbeat():
    return Response(response="OK", status=200,  mimetype="text/plain")
