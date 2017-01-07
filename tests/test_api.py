from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from app import create_app, db


class TestTasks(TestCase):

    def create_app(self):
        return create_app("testing")

    def test_fail(self):
        self.assertEqual(1, 0)

    def test_(self):
        response = self.client.get(url_for("api.get_tasks"))