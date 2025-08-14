#!/usr/bin/env python3
"""
Application entry point for AWS Elastic Beanstalk
This file is required for EB deployment and should be named 'application.py'
"""

import os
from web_app import app as application

if __name__ == "__main__":
    # For local testing
    application.run(host='0.0.0.0', port=5000, debug=False)
