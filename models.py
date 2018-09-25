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
    current_quiz = TextField(default="[]")
    is_admin = BooleanField(default=False)
    is_student = BooleanField(default=True)
    is_teacher = BooleanField(default=False)

    @classmethod
    def create_user(cls, username, password, current_quiz="[]", admin=False, student=True, teacher=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password),
                    current_quiz=current_quiz,
                    is_admin=admin,
                    is_student=student,
                    is_teacher=teacher,
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
    user_id = ForeignKeyField(User, unique=True)
    total_quiz_num = IntegerField(default=0)
    total_questions_correct = IntegerField(default=0)
    total_questions_wrong = IntegerField(default=0)



def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Score], safe=True)
    DATABASE.close()
