from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User


class ApiTestCase(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_user(self, name="Test", password="test"):
        user = User(username=name, password=password)
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, name="Test", password="test"):
        return self.client.post(url_for("auth.login"), data=dict(
            username=name,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get(url_for("auth.logout"), follow_redirects=True)