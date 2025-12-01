"""Extract client IP from Flask request for forwarding to Crossref REST API."""

import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Return client IP from request.remote_addr, or None if unavailable."""
    if not request:
        logger.warning("get_client_ip called with None request")
        return None
    
    try:
        client_ip = request.remote_addr
        if client_ip and client_ip.strip():
            return client_ip.strip()
        
        logger.warning("Could not determine client IP from request")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting client IP: {e}")
        return None

