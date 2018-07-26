from sqlalchemy.exc import IntegrityError
from random import seed,randint
from app import db
import forgery_py
from app.models import User,Post


def generate_fake_users(count=100):
    seed()
    for i in range(count):
        u = User(email=forgery_py.internet.email_address())
        u.username = forgery_py.internet.user_name(True)
        u.password = forgery_py.lorem_ipsum.word()
        u.confirmed = True
        u.name = forgery_py.name.full_name()
        u.location = forgery_py.address.city()
        u.about_me = forgery_py.lorem_ipsum.sentence()
        u.member_since = forgery_py.date.date(True)
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def generate_fake_posts(count=100):
    seed()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0,user_count-1)).first()
        p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                 timestamp=forgery_py.date.date(True), author=u)
        db.session.add(p)
        db.session.commit()

