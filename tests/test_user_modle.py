import unittest
from app.models import User

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        u = User( password='123' )
        self.assertTrue(u.password_hash is not None)

    def test_two_users_password_hash_not_equal(self):
        u1 = User( password= '123')
        u2 = User(password='123')
        self.assertFalse(u1.password_hash == u2.password_hash)

    def test_get_password(self):
        u = User(password='123')
        with self.assertRaises(AttributeError):
            u.password

    def test_verify_password(self):
        u = User(password='123')
        self.assertTrue(u.verify_password('123') )
        self.assertFalse(u.verify_password('234'))