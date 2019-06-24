import datetime
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
    pic = CharField(default='math_profile_blank.png')
    current_quiz = TextField(default='[]')
    is_admin = BooleanField(default=False)
    is_student = BooleanField(default=True)
    is_teacher = BooleanField(default=False)

    @classmethod
    def create_user(cls, username, password, pic='math_profile_blank.png', current_quiz='[]', admin=False,
                    student=True, teacher=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password),
                    pic=pic,
                    current_quiz=current_quiz,
                    is_admin=admin,
                    is_student=student,
                    is_teacher=teacher,
                )
        except IntegrityError:
            raise ValueError('Username already exists. Try again.')

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def is_active(self):
        return self.authenticated

    def is_anonymous(self):
        return False


class SavedQuizzes(BaseModel):
    user = ForeignKeyField(User, unique=False)
    quiz_name = CharField(max_length=250, unique=True)
    created_by = CharField(default=User.username)
    assigned_by = CharField(default=User.username)
    math_op = CharField(default='+')
    starting_num = IntegerField(default=0)
    ending_num = IntegerField(default=10)
    allow_neg_answers = BooleanField(default=False)
    quiz_length = IntegerField(default=-1)

    def create_facts(self):
        facts = {}
        first_num = 0
        math_operators = {'+': operator.add,
                          '-': operator.sub,
                          '*': operator.mul,
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
                key1 = '{} {} {}'.format(first_num, self.math_op, i)
                value1 = math_operators[self.math_op](first_num, i)
                in_dict(key1, value1, facts)

                if first_num != i:
                    key2 = '{} {} {}'.format(i, self.math_op, first_num)
                    value2 = math_operators[self.math_op](i, first_num)
                    in_dict(key2, value2, facts)
                    key3 = '{} {} {}'.format(i, self.math_op, i)
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


class UserScores(BaseModel):
    user_id = ForeignKeyField(User, unique=False)
    quiz_id = ForeignKeyField(SavedQuizzes, null=True, unique=False)
    quiz_type = CharField(default='+')
    questions_correct = IntegerField(default=0)
    questions_wrong = IntegerField(default=0)
    questions_total = IntegerField(default=0)
    date_taken = DateTimeField(default=datetime.datetime.now)


class Questions(BaseModel):
    question = CharField(unique=True)
    answer = IntegerField()
    question_type = CharField(default='Equation')
    question_op = CharField()

    @classmethod
    def populate(cls, qstn_op, start_num=0, end_num=10):
        """Populates Questions table with questions based on the mathematical operator, start, and end number (inclusive).
        Cannot be used to add word problems.
        """
        operators = {'+': operator.add, '-': operator.sub, '*': operator.mul}
        first = start_num
        while first <= end_num:
            for i in range(start_num, end_num+1):
                qstn_text = '{} {} {}'.format(first, qstn_op, i)
                ans = operators[qstn_op](first, i)
                with DATABASE.transaction():
                    cls.create(
                        question=qstn_text,
                        answer=ans,
                        question_type='Equation',
                        question_op=qstn_op
                    )
            first += 1

    @classmethod
    def mass_populate(cls, qstn_op):
        """Populates table with all possible equations from 0 to 100 inclusive based on the selected math operator.
        Cannot be used to add word problems.
        """
        operators = {'+': operator.add, '-': operator.sub, '*': operator.mul}
        for i in range(101):
            for j in range(101):
                qstn_text = '{} {} {}'.format(i, qstn_op, j)
                ans = operators[qstn_op](i, j)
                with DATABASE.transaction():
                    cls.create(
                        question=qstn_text,
                        answer=ans,
                        question_type='Equation',
                        question_op=qstn_op
                    )


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, SavedQuizzes, UserScores, Questions], safe=True)
    DATABASE.close()
