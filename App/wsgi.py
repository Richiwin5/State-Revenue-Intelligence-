# wsgi.py
import os
import sys
import subprocess


def application(environ, start_response):
    """WSGI application wrapper for Streamlit"""
    # This is a simple wrapper - Streamlit will handle the actual server
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)

    # Run Streamlit
    port = environ.get('SERVER_PORT', '8501')
    cmd = f"streamlit run dashboard.py --server.port {port} --server.address 0.0.0.0"

    return [b"Streamlit app is running. Use the Streamlit native server instead."]