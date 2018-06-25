from flask_bcrypt import generate_password_hash
from flask_login import UserMixin

from peewee import *

DATABASE = SqliteDatabase('mathgame.db')

class BaseModel(Model):
    class Meta:
        database = DATABASE


class User(UserMixin, BaseModel):
    username = CharField(unique=True)
    password = CharField(max_length=25)
    is_admin = BooleanField(default=False)

    @classmethod
    def create_user(cls, username, password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password),
                    is_admin=admin
                )
        except IntegrityError:
            raise ValueError("Username already exists. Try again.")

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def is_active(self):
        return self.authenticated

    def is_anonymous(self):
        return False

class Score(BaseModel):
    # Tracks how many quizes user has taken and type (addition, subtraction, etc.)
    # Type should be a different model?
    user = ForeignKeyField(User, unique=True)
    total_quiz_num = IntegerField
    total_questions_correct = IntegerField
    total_questions_wrong = IntegerField



def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Score], safe=True)
    DATABASE.close()
