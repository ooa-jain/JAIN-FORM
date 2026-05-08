"""
passenger_wsgi.py — Hostinger WSGI entry point.

Hostinger shared hosting uses Phusion Passenger.
This file MUST be in your project root folder.
"""
import sys
import os

# Add your project root to Python path
INTERP = os.path.expanduser('~') + '/virtualenv/formcraft/3.11/bin/python'
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
application = create_app()
