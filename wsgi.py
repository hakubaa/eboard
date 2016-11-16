#!/usr/bin/env python

import os
from app import create_app

application = create_app("production")

if __name__ == "__main__":
    application.run(debug = True, host = "0.0.0.0", port = 8888)
