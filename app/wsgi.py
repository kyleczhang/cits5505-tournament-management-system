"""WSGI entry point for production servers.

This module exposes the Flask application as ``application`` so WSGI servers
such as Gunicorn, uWSGI, or Apache mod_wsgi can import and serve it.
"""

from criktrack import create_app

application = create_app()
