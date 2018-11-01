import operator
import random

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


class SavedQuizzes(BaseModel):
    user = ForeignKeyField(User, unique=False)
    quiz_name = CharField(max_length=250, unique=True)
    created_by = CharField(default=User.username)
    assigned_by = CharField(default=User.username)
    math_op = CharField(default="+")
    starting_num = IntegerField(default=0)
    ending_num = IntegerField(default=10)
    allow_neg_answers = BooleanField(default=False)
    quiz_length = IntegerField(default=-1)
    #quiz_questions_answers = BareField()

    def create_facts(self):
        facts = {}
        first_num = 0
        math_operators = {"+": operator.add,
                          "-": operator.sub,
                          "*": operator.mul,
                          }

        def in_dict(k, v, dictionary):
            if self.allow_neg_answers is True:
                if k not in dictionary:
                    dictionary[k] = v
            elif self.allow_neg_answers is False:
                if k not in dictionary and v >= 0:
                    dictionary[k] = v

        while first_num <= self.ending_num:
            for i in range(self.starting_num, self.ending_num+1):
                key1 = "{} {} {}".format(first_num, self.math_op, i)
                value1 = math_operators[self.math_op](first_num, i)
                in_dict(key1, value1, facts)

                if first_num != i:
                    key2 = "{} {} {}".format(i, self.math_op, first_num)
                    value2 = math_operators[self.math_op](i, first_num)
                    in_dict(key2, value2, facts)
                    key3 = "{} {} {}".format(i, self.math_op, i)
                    value3 = math_operators[self.math_op](i, i)
                    in_dict(key3, value3, facts)

            first_num += 1

        return facts

    def create_test(self, facts):
        if self.quiz_length == -1 or self.quiz_length > len(facts):
            test_length = len(facts)
        else:
            test_length = self.quiz_length
        test_questions = random.sample(list(facts), test_length)

        return test_questions


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Score, SavedQuizzes], safe=True)
    DATABASE.close()
