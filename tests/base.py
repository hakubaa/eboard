import unittest
import os

from app import create_app, db


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        # db.create_all()
        self.client = self.app.test_client(use_cookies = True)

    def tearDown(self):
        self.app_context.pop()