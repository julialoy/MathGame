import datetime
import operator

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
    is_admin = BooleanField(default=False)
    is_student = BooleanField(default=True)
    is_teacher = BooleanField(default=False)

    @classmethod
    def create_user(cls, username, password, pic='math_profile_blank.png', admin=False,
                    student=True, teacher=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password),
                    pic=pic,
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


class Quizzes(BaseModel):
    quiz_name = CharField(max_length=250, unique=True)
    math_op = CharField(default='+')
    starting_num = IntegerField(default=0)
    ending_num = IntegerField(default=10)
    allow_neg_answers = BooleanField(default=False)
    quiz_length = IntegerField(default=-1)


class QuizAttempts(BaseModel):
    user_id = ForeignKeyField(User, unique=False)
    assigned_by = ForeignKeyField(User, default=None, null=False, unique=False)
    quiz_id = ForeignKeyField(Quizzes, unique=False)
    quiz_type = CharField(default='+', null=False)
    questions_correct = IntegerField(default=0)
    questions_wrong = IntegerField(default=0)
    questions_total = IntegerField(default=0)
    date_taken = DateTimeField(default=datetime.datetime.now())


class UserQuizzes(BaseModel):
    """Joined table for quizzes created by and saved by users."""
    user_id = ForeignKeyField(User, unique=False)
    quiz_id = ForeignKeyField(Quizzes, unique=True)


class Questions(BaseModel):
    question = CharField(unique=True)
    answer = IntegerField()
    first_num = IntegerField()
    second_num = IntegerField()
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
                        first_num=first,
                        second_num=i,
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
                        first_num=i,
                        second_num=j,
                        question_type='Equation',
                        question_op=qstn_op
                    )


class QuestionAttempts(BaseModel):
    user_id = ForeignKeyField(User, unique=False)
    question_id = ForeignKeyField(Questions, unique=False)
    quiz_id = ForeignKeyField(Quizzes, null=False, unique=False)
    correct = BooleanField()
    incorrect = BooleanField()
    date_attempted = DateTimeField(default=datetime.datetime.now())


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Quizzes, QuizAttempts, UserQuizzes, Questions, QuestionAttempts], safe=True)
    DATABASE.close()
