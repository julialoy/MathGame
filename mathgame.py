from datetime import datetime
from functools import wraps
import os

from flask import (Flask, flash, g, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_bcrypt import check_password_hash
from flask_login import current_user, LoginManager, login_required, login_user, logout_user
from werkzeug.utils import secure_filename
from peewee import *

import models

DEBUG = True
UPLOAD_FOLDER = 'static/images/pics_user'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'dshfjkrehtuia^&#C@@%&*(fdsh21243254235'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.is_admin is False:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.is_teacher is False:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Checks that the filename contains an extension.
    Checks that the extension is in ALLOWED_EXTENSIONS.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_question(operation, qstn_type, num_start, num_end):
    q = (models.Questions.select()
         .where(models.Questions.question_op == operation,
                models.Questions.question_type == qstn_type,
                models.Questions.first_num >= num_start,
                models.Questions.first_num <= num_end,
                models.Questions.second_num >= num_start,
                models.Questions.second_num <= num_end)
         .order_by(fn.Random()).limit(1)
         )
    return q


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


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Accesses the username and password supplied by the user through the HTML form and tries to create
    a user and score model for the new user.
    If successful, redirects the user to the login page.
    If unsuccessful, reloads the registration page.
    """
    if request.form:
        user_registration = request.form
        if 'is-admin' in user_registration.keys():
            is_admin = True
        else:
            is_admin = False

        if 'is-teacher' in user_registration.keys():
            is_teacher = True
        else:
            is_teacher = False

        if is_admin or is_teacher is True:
            is_student = False
        else:
            is_student = True
        username = user_registration['username']
        password = user_registration['password']
        try:
            models.User.create_user(username=username,
                                    password=password,
                                    admin=is_admin,
                                    student=is_student,
                                    teacher=is_teacher
                                    )
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except ValueError:
            return render_template('register.html')
    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
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
    session.pop('current_quiz_id', None)
    session.pop('current_quiz', None)
    session.pop('current_facts', None)
    session.pop('current_qstn_type', None)
    session.pop('current_end_start', None)
    session.pop('current_quiz_desc', None)
    session.pop('previous_questions', None)
    session.pop('current_num_correct', None)
    session.pop('current_num_incorrect', None)
    session.pop('current_user_score', None)
    logout_user()
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    """If the current user is not authenticated/there is no current user,
    show the login page.
    Otherwise show the index.
    """
    if not current_user.is_authenticated:
        return render_template('login.html')
    elif current_user.is_admin:
        return redirect(url_for('admin'))
    elif current_user.is_teacher:
        return redirect(url_for('teacher'))
    else:
        selected_user = models.User.get(models.User.id == current_user.id)
        user_quizzes = (models.UserQuizzes.select()
                        .where(models.UserQuizzes.user_id == current_user.id))
        quiz_list = user_quizzes[:5]
        return render_template('index.html',
                               selected_user=selected_user,
                               quiz_list=quiz_list
                               )


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    selected_user = models.User.get(models.User.id == current_user.id)
    quiz_list = (models.UserQuizzes.select()
                 .where(models.UserQuizzes.user_id == current_user.id))
    total_quizzes = (models.QuizAttempts.select()
                     .join(models.User, on=(models.QuizAttempts.user_id == models.User.id))
                     .where(models.User.id == current_user.id))
    quiz_types = [quiz.quiz_type for quiz in total_quizzes]

    return render_template('profile.html',
                           selected_user=selected_user,
                           quiz_list=quiz_list,
                           total_quizzes=total_quizzes,
                           quiz_types=quiz_types
                           )


@app.route('/uploader', methods=['GET', 'POST'])
@login_required
def uploader():
    selected_user = models.User.get(models.User.id == current_user.id)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
    file = request.files['file']

    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        q = models.User.update(pic=filename).where(models.User.id == selected_user)
        q.execute()
        return redirect(url_for('profile', user_id=selected_user))


@app.route('/uploads/<filename>')
@login_required
def upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/removeimage', methods=["GET", "POST"])
@login_required
def remove_pic():
    """Removes a profile picture from a user's profile.
    Does not delete the file from the upload folder.
    """
    selected_user = models.User.get(models.User.id == current_user.id)
    q = models.User.update(pic='math_profile_blank.png').where(models.User.id == selected_user)
    q.execute()
    return redirect(url_for('profile'))


@app.route('/startquickquiz', methods=['GET', 'POST'])
@login_required
def startquickquiz():
    """Starts a quiz with 10 random addition facts using numbers from 0 to 10 and adds the quiz to the current
    session for the current user.
    """
    # Quick quizzes and unsaved custom quizzes still need to generate a unique quiz id ?
    # This will allow all quizzes to be recreated, effectively saving a quiz that a user doesn't want to save?
    current_user_score = models.QuizAttempts.create(user_id=current_user.id,
                                                    quiz_id=0,
                                                    quiz_type="+",
                                                    questions_crrect=0,
                                                    questions_wrong=0,
                                                    questions_total=10,
                                                    date_take=datetime.now()
                                                    )
    session['current_quiz_id'] = None
    session['current_facts'] = 10
    session['current_quiz'] = '+'
    session['current_qstn_type'] = 'Equation'
    session['current_end_start'] = [0, 10]
    session['current_quiz_desc'] = 'Basic Addition Math Facts from 0 to 10'
    session['previous_questions'] = []
    session['current_num_correct'] = 0
    session['current_num_incorrect'] = 0
    session['current_user_score'] = current_user_score.id
    return redirect(url_for('index'))


@app.route('/startcustomquiz', methods=['GET', 'POST'])
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

        new_cust_quiz = models.Quizzes(math_op=quiz_op,
                                       starting_num=quiz_start,
                                       ending_num=quiz_end,
                                       allow_neg_answers=False,
                                       quiz_length=quiz_length
                                       )
        new_cust_quiz.save()

        if quiz_setup['save-quiz'] == 'yes':
            models.UserQuizzes.create(user_id=current_user.id,
                                      quiz_name=quiz_desc,
                                      quiz_id=new_cust_quiz.id
                                      )

        cust_id = new_cust_quiz.id

        current_user_score = models.QuizAttempts.create(user_id=current_user.id,
                                                        quiz_id=cust_id,
                                                        quiz_type=quiz_op,
                                                        questions_correct=0,
                                                        questions_wrong=0,
                                                        questions_total=quiz_length,
                                                        date_taken=datetime.now()
                                                        )
        session['current_quiz_id'] = cust_id
        session['current_facts'] = quiz_length
        session['current_quiz'] = quiz_op
        session['current_qstn_type'] = 'Equation'
        session['current_end_start'] = [quiz_start, quiz_end]
        session['current_quiz_desc'] = quiz_desc
        session['previous_questions'] = []
        session['current_num_correct'] = 0
        session['current_num_incorrect'] = 0
        session['current_user_score'] = current_user_score.id
        return redirect(url_for('index'))
    else:
        return render_template('startquiz.html')


@app.route('/startsavedquiz/<saved_quiz_id>', methods=['GET', 'POST'])
@login_required
def startsavedquiz(saved_quiz_id):
    # Currently this does not allow you to retake the exact same questions
    # Need to fix question view to do that
    basic_info = models.UserQuizzes.get(models.UserQuizzes.id == saved_quiz_id)
    base = models.Quizzes.get(models.Quizzes.id == saved_quiz_id)
    current_user_score = models.QuizAttempts.create(user_id=current_user.id,
                                                    quiz_id=saved_quiz_id,
                                                    quiz_type=base.math_op,
                                                    questions_correct=0,
                                                    questions_wrong=0,
                                                    questions_total=base.quiz_length,
                                                    date_taken=datetime.now()
                                                    )
    session['current_quiz_id'] = base.id
    session['current_facts'] = base.quiz_length
    session['current_quiz'] = base.math_op
    session['current_qstn_type'] = 'Equation'
    session['current_end_start'] = [base.starting_num, base.ending_num]
    session['current_quiz_desc'] = basic_info.quiz_name
    session['previous_questions'] = []
    session['current_num_correct'] = 0
    session['current_num_incorrect'] = 0
    session['current_user_score'] = current_user_score.id
    return redirect(url_for('index'))


@app.route('/question', methods=['GET'])
@login_required
def question():
    try:
        session['current_facts']
    except KeyError:
        return jsonify(question="You haven't started a quiz!")
    else:
        if session['current_facts'] > 0:
            problem = get_question(session['current_quiz'], session['current_qstn_type'],
                                   session['current_end_start'][0], session['current_end_start'][1])

            if problem[0].id in session['previous_questions']:
                # Delete after more testing
                print("NEED NEW PROBLEM: {}".format(problem[0].id))
                problem = get_question(session['current_quiz'], session['current_qstn_type'],
                                       session['current_end_start'][0], session['current_end_start'][1])

            session['current_question'] = problem[0].id
            # Delete after more testing
            print("CURRENT QUESTION ID: {}".format(problem[0].id))
            session['previous_questions'].append(problem[0].id)
            # Delete after more testing
            print("PREV QSTS: {}".format(session['previous_questions']))
            qst = problem[0].question
            session['current_facts'] -= 1
            # Delete after more testing
            print("CURRENT FACTS: {}".format(session['current_facts']))
            return jsonify(question=qst)
        else:
            current_correct = session['current_num_correct']
            current_incorrect = session['current_num_incorrect']
            return jsonify(question='End of Quiz!',
                           current_correct=current_correct,
                           current_incorrect=current_incorrect,
                           )


@app.route('/checkanswer', methods=['GET', 'POST'])
@login_required
def checkanswer():
    data = request.form
    try:
        user_answer = int(data['userAnswer'])
    except ValueError:
        return jsonify(answer='Try again! Please enter a number.')
    else:
        correct_answer = models.Questions.get(models.Questions.id == session['current_question']).answer
        if user_answer == correct_answer:
            q_c1 = (models.QuizAttempts
                    .update({models.QuizAttempts.questions_correct: models.QuizAttempts.questions_correct + 1})
                    .where(models.QuizAttempts.id == session['current_user_score']))
            q_c1.execute()
            models.QuestionAttempts.create(user_id=current_user.id,
                                           question_id=session['current_question'],
                                           quiz_id=session['current_quiz_id'],
                                           correct=True,
                                           incorrect=False,
                                           date_attempted=datetime.now()
                                           )
            session['current_num_correct'] += 1
            return jsonify(answer='CORRECT!')
        else:
            q_w1 = (models.QuizAttempts
                    .update({models.QuizAttempts.questions_wrong: models.QuizAttempts.questions_wrong + 1})
                    .where(models.QuizAttempts.id == session['current_user_score']))
            q_w1.execute()
            models.QuestionAttempts.create(user_id=current_user.id,
                                           question_id=session['current_question'],
                                           quiz_id=session['current_quiz_id'],
                                           correct=False,
                                           incorrect=True,
                                           date_attempted=datetime.now()
                                           )
            session['current_num_incorrect'] += 1
            return jsonify(answer="Sorry! That's not the right answer.")


@app.route('/teacher', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher():
    return render_template('teacher.html')


@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    return render_template('admin.html')


@app.route('/populate', methods=['GET', 'POST'])
@login_required
@admin_required
def populate():
    """Allows administrators to populate the Questions table with questions.
    Questions are used to create quizzes for all users.
    """
    if request.form:
        form = request.form
        quest_type = form['populate-questions']
        try:
            models.Questions.mass_populate(quest_type)
        except IntegrityError:
            flash('Unable to populate database.')
        else:
            flash('Database populated successfully.')
    return render_template('admin.html')


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG)
