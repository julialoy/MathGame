# Rewrote mathgame.py to clean up
from datetime import datetime
import operator
import os
import random

from flask import (Flask, flash, g, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_bcrypt import check_password_hash
from flask_login import current_user, LoginManager, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

import models

DEBUG = True
UPLOAD_FOLDER = 'static/images/pics_user'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'dshfjkrehtuia^&#C@@%&*(fdsh21243254235'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


def allowed_file(filename):
    """Checks that the filename contains an extension.
    Checks that the extension is in ALLOWED_EXTENSIONS.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_test_length(t_length, t_q_and_a):
    """Checks the length of the test.
    Takes a test length as an integer and a dictionary of questions and answers.
    """
    if t_length == -1 or t_length > len(t_q_and_a):
        return len(t_q_and_a)
    else:
        return t_length


def is_in_dict(k, v, dictionary, allow_neg_ans):
    """Adds the math question and its answer to the math facts dictionary.
    If the quiz does not allow a negative number as an answer,
    no questions with a negative answer will be added to the dictionary.
    """
    if allow_neg_ans is True:
        if k not in dictionary:
            dictionary[k] = v
    elif allow_neg_ans is False:
        if k not in dictionary and v >= 0:
            dictionary[k] = v


class Test:
    """Creates the math test."""
    def __init__(self, test_type, test_questions_answers, test_length=-1):
        self.test_type = test_type
        self.test_questions_answers = test_questions_answers
        self.test_length = check_test_length(test_length, self.test_questions_answers)
        # if test_length == -1 or test_length > len(self.test_questions_answers):
        #    self.test_length = len(self.test_questions_answers)
        # else:
        #    self.test_length = test_length
        self.test_questions = random.sample(list(self.test_questions_answers), self.test_length)

    def test_type(self):
        return self.test_type

    def list_questions(self):
        for qstn in self.test_questions_answers:
            print(qstn)

    def test_length(self):
        return self.test_length

    def grab_question(self):
        return self.test_questions.pop()

    def grab_answer(self, quiz_question):
        return self.test_questions_answers[quiz_question]


class MathFacts:
    """Creates the set of questions and answers to feed into the Test class.
    Takes an operator (+, -, *), whether to allow answers < 0, and start and end numbers.
    """
    def __init__(self, math_op="+", start_num=0, end_num=10, neg_answers=False):
        self.math_op = math_op
        self.start_num = start_num
        self.end_num = end_num
        self.neg_answers = neg_answers
        self.facts = {}

    math_operators = {"+": operator.add,
                      "-": operator.sub,
                      "*": operator.mul,
                      }

    def create_facts(self):
        """Creates and returns a dictionary of the selected math facts to test.
        Keys are the equations, values are the answers to the equation.
        All allowed combinations are added to the facts dictionary.
        """
        first_num = 0

        while first_num <= self.end_num:
            # Iterates through a range of numbers (+1) to build a dictionary of equations as keys and their
            # answers as values
            for i in range(self.start_num, self.end_num+1):
                # Builds the equation with the first number for the equation, the operator symbol, and the second
                # number for the equation
                key1 = "{} {} {}".format(first_num, self.math_op, i)
                # Retrieves the correct operation from the math_operators dictionary and performs that operation on
                # first_num and i, with first_num being the first number of the equation and i
                # being the second number in the equation. The value stored in the variable is the answer to the
                # equation.
                value1 = self.math_operators[self.math_op](first_num, i)
                # Uses the is_in_dict function to add the equation and the equation's answer to the facts dictionar
                # based on whether negative answers are allowed or not.
                is_in_dict(key1, value1, self.facts, self.neg_answers)

                # For all equations where the two numbers are not the same, creates a second equation reversing
                # the order of the numbers to get all possible allowed combinations. This ensures the test taker
                # can add 5 + 3 and not just 3 + 5.
                if first_num != i:
                    key2 = "{} {} {}".format(i, self.math_op, first_num)
                    value2 = self.math_operators[self.math_op](i, first_num)
                    is_in_dict(key2, value2, self.facts, self.neg_answers)
                    key3 = "{} {} {}".format(i, self.math_op, i)
                    value3 = self.math_operators[self.math_op](i, i)
                    is_in_dict(key3, value3, self.facts, self.neg_answers)
            first_num += 1


@login_manager.user_loader
def load_user(user_id):
    """Tries to load the user from the database using the user id.
    If the user can be loaded, returns the user with that id.
    Otherwise, returns None.
    """
    try:
        return models.User.get(models.User.id == user_id)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Before a request, connects to the global database, opens a connection, and sets the global user as the
    current user.
    """
    g.db = models.DATABASE
    g.db.connection()
    g.user = current_user


@app.after_request
def after_request(response):
    """After a request, closes the connection to the database and returns the response."""
    g.db.close()
    return response


@app.route('/register', methods=["GET", "POST"])
def register():
    """Accesses the username and password supplied by the user through the HTML form and tries to create
    a user and score model for the new user.
    If successful, redirects the user to the login page.
    If unsuccessful, reloads the registration page.
    """
    if request.form:
        user_registration = request.form
        username = user_registration['username']
        password = user_registration['username']
        try:
            models.User.create_user(
                username=username,
                password=password
            )
            return redirect(url_for('login'))
        except ValueError:
            return render_template('register.html')
    else:
        return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    """Logs an existing user in and creates information for the current session after checking the password hash.
    Provides error messages if a username or password is incorrect.
    """
    if request.form:
        user_info = request.form
        username = user_info['username']
        password = user_info['password']
        try:
            user = models.User.get(models.User.username == username)
        except models.DoesNotExist:
            flash('That username or password is incorrect.')
            return render_template('login.html')
        else:
            if check_password_hash(user.password, password):
                session['username'] = username
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('That username or password is incorrect.')
                return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logs a user out and removes information from the current session."""
    session.pop('username', None)
    session.pop('current_quiz', None)
    session.pop('current_facts', None)
    session.pop('current_quiz_desc', None)
    session.pop('current_num_correct', None)
    session.pop('current_num_incorrect', None)
    session.pop('current_user_score', None)
    logout_user()
    return redirect(url_for('index'))


@app.route('/', methods=["GET", "POST"])
def index():
    """If the current user is not authenticated/there is no current user,
    show the login page.
    Otherwise show the index.
    """
    if not current_user.is_authenticated:
        return render_template('login.html')
    else:
        return render_template('index.html')


@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    selected_user = models.User.get(models.User.id == current_user.id)
    quiz_list = (models.SavedQuizzes.select()
                 .join(models.User, on=(models.SavedQuizzes.user_id == models.User.id))
                 .where(models.User.id == current_user.id))
    total_quizzes = (models.UserScores.select()
                     .join(models.User, on=(models.UserScores.user_id == models.User.id))
                     .where(models.User.id == current_user.id))
    quiz_types = [quiz.quiz_type for quiz in total_quizzes]
    return render_template('profile.html',
                           selected_user=selected_user,
                           quiz_list=quiz_list,
                           total_quizzes=total_quizzes,
                           quiz_types=quiz_types
                           )


@app.route('/uploader', methods=["GET", "POST"])
@login_required
def uploader():
    selected_user = models.User.get(models.User.id == current_user.id)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)
    file = request.files['file']

    if file.filename == '':
        flash("No file selected")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        q = models.User.update(
            pic=filename
        ).where(models.User.user_id == selected_user)
        q.execute()
        return redirect(url_for('profile', user_id=selected_user))


@app.route('/uploads/<filename>')
@login_required
def upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/removeimage/<filename>', methods=["GET", "POST"])
@login_required
def remove_pic():
    """Removes a profile picture from a user's profile.
    Does not delete the file from the upload folder.
    """
    selected_user = models.User.get(models.User.id == current_user.id)
    q = models.User.update(
        pic=""
    ).where(models.User.user_id == selected_user)
    q.execute()
    return redirect(url_for('profile'))


@app.route('/startquickquiz', methods=["GET", "POST"])
@login_required
def startquickquiz():
    """Starts a quiz with 10 random addition facts using numbers from 0 to 10 and adds the quiz to the current
    session for the current user.
    """
    new_facts = MathFacts()
    new_facts.create_facts()
    new_test = Test("Basic Addition Math Facts", new_facts.facts, 10)
    current_user_score = models.UserScores.create(
        user_id=current_user.id,
        quiz_id=0,
        quiz_type="+",
        questions_crrect=0,
        questions_wrong=0,
        questions_total=10,
        date_take=datetime.now()
    )
    session['current_facts'] = new_facts.facts
    session['current_quiz'] = new_test
    session['current_num_correct'] = 0
    session['current_num_incorrect'] = 0
    session['current_user_score'] = current_user_score.id
    return redirect(url_for('index'))


@app.route('/startcustomquiz', methods=["GET", "POST"])
@login_required
def startcustomquiz():
    """Starts a custom math quiz. The user decides on the math operation, starting and ending numbers, and
    number of questions. Adds the new quiz as the current quiz to the session.
    """
    if request.form:
        quiz_setup = request.form
        quiz_desc = quiz_setup['test-name']
        quiz_op = quiz_setup['fact-type']
        quiz_length = int(quiz_setup['number-questions'])

        if quiz_setup['start-num'] != '':
            quiz_start = int(quiz_setup['start-num'])
        else:
            quiz_start = 0

        if quiz_setup['end-num'] != '':
            quiz_end = int(quiz_setup['end-num'])
        else:
            quiz_end = 10

        cust_facts = MathFacts(quiz_op, quiz_start, quiz_end)
        cust_facts.create_facts()
        cust_quiz = Test(quiz_desc, cust_facts.facts, quiz_length)

        if quiz_setup['save_quiz'] == 'yes':
            new_cust_quiz = models.SavedQuizzes(user=current_user.id,
                                                quiz_name=quiz_desc,
                                                created_by=current_user.id,
                                                assigned_by=current_user.id,
                                                math_op=quiz_op,
                                                starting_num=quiz_start,
                                                ending_num=quiz_end,
                                                allow_neg_answers=False,
                                                quiz_length=quiz_length,
                                                )
            new_cust_quiz.save()
            cust_id = new_cust_quiz.id
        else:
            cust_id = 0

        current_user_score = models.UserScores.create(
            user_id=current_user.id,
            quiz_id=cust_id,
            quiz_type=quiz_op,
            questions_correct=0,
            questions_wrong=0,
            questions_total=quiz_length,
            date_taken=datetime.now()
        )
        session['current_facts'] = cust_quiz.test_questions_answers
        session['current_quiz'] = cust_quiz.test_questions
        session['current_num_correct'] = 0
        session['current_num_incorrect'] = 0
        session['current_user_score'] = current_user_score.id
        return redirect(url_for('index'))
    else:
        return render_template('startquiz.html')


@app.route('/startsavedquiz/<saved_quiz_id>', methods=["GET", "POST"])
@login_required
def startsavedquiz(saved_quiz_id):
    base = models.SavedQuizzes.get(models.SavedQuizzes.id == saved_quiz_id)
    facts = base.create_facts()
    quiz = base.create_test(facts)
    current_user_score = models.UserScores.create(
        user_id=current_user.id,
        quiz_id=saved_quiz_id,
        quiz_type=base.math_op,
        questions_correct=0,
        questions_wrong=0,
        questions_total=base.quiz_length,
        date_taken=datetime.now()
    )
    session['current_facts'] = facts
    session['current_quiz'] = quiz
    session['current_quiz_desc'] = base.quiz_name
    session['current_num_correct'] = 0
    session['current_num_incorrect'] = 0
    session['current_user_score'] = current_user_score.id
    return redirect(url_for('index'))


@app.route('/question', methods=["GET", "POST"])
@login_required
def question():
    pass


@app.route('/checkanswer', methods=["GET", "POST"])
@login_required
def checkanswer():
    pass


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG)
