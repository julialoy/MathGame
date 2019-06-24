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


def allowed_file(filename):
    """Checks that the filename contains an extension.
    Checks that the extension is in ALLOWED_EXTENSIONS.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    session.pop('current_quiz', None)
    session.pop('current_facts', None)
    session.pop('current_quiz_desc', None)
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
    else:
        selected_user = models.User.get(models.User.id == current_user.id)
        quiz_list = (models.SavedQuizzes.select()
                     .join(models.User, on=(models.SavedQuizzes.user_id == models.User.id))
                     .where(models.User.id == current_user.id))
        return render_template('index.html',
                               selected_user=selected_user,
                               quiz_list=quiz_list
                               )


@app.route('/profile', methods=['GET', 'POST'])
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
    new_test = models.SavedQuizzes(user=current_user.id,
                                   quiz_name='Basic Addition Math Facts from 0 to 10',
                                   created_by=current_user.id,
                                   assigned_by=None,
                                   math_op="+",
                                   starting_num=0,
                                   ending_num=10,
                                   allow_neg_answers=False,
                                   quiz_length=10
                                   )
    current_user_score = models.UserScores.create(user_id=current_user.id,
                                                  quiz_id=0,
                                                  quiz_type="+",
                                                  questions_crrect=0,
                                                  questions_wrong=0,
                                                  questions_total=10,
                                                  date_take=datetime.now()
                                                  )
    facts = new_test.create_facts()
    quiz = new_test.create_test(facts)
    session['current_quiz'] = quiz
    session['current_facts'] = facts
    session['current_quiz_desc'] = 'Basic Addition Math Facts from 0 to 10'
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

        new_cust_quiz = models.SavedQuizzes(user=current_user.id,
                                            quiz_name=quiz_desc,
                                            created_by=current_user.username,
                                            assigned_by=current_user.username,
                                            math_op=quiz_op,
                                            starting_num=quiz_start,
                                            ending_num=quiz_end,
                                            allow_neg_answers=False,
                                            quiz_length=quiz_length
                                            )

        if quiz_setup['save-quiz'] == 'yes':
            new_cust_quiz.save()
            cust_id = new_cust_quiz.id
        else:
            cust_id = 0

        current_user_score = models.UserScores.create(user_id=current_user.id,
                                                      quiz_id=cust_id,
                                                      quiz_type=quiz_op,
                                                      questions_correct=0,
                                                      questions_wrong=0,
                                                      questions_total=quiz_length,
                                                      date_taken=datetime.now()
                                                      )
        cust_facts = new_cust_quiz.create_facts()
        cust_quiz = new_cust_quiz.create_test(cust_facts)
        cust_desc = new_cust_quiz.quiz_name
        session['current_facts'] = cust_facts
        session['current_quiz'] = cust_quiz
        session['current_quiz_desc'] = cust_desc
        session['current_num_correct'] = 0
        session['current_num_incorrect'] = 0
        session['current_user_score'] = current_user_score.id
        return redirect(url_for('index'))
    else:
        return render_template('startquiz.html')


@app.route('/startsavedquiz/<saved_quiz_id>', methods=['GET', 'POST'])
@login_required
def startsavedquiz(saved_quiz_id):
    base = models.SavedQuizzes.get(models.SavedQuizzes.id == saved_quiz_id)
    facts = base.create_facts()
    quiz = base.create_test(facts)
    current_user_score = models.UserScores.create(user_id=current_user.id,
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


@app.route('/question', methods=['GET'])
@login_required
def question():
    try:
        len(session['current_quiz'])
    except KeyError:
        return jsonify(question="You haven't started a quiz!")
    else:
        if len(session['current_quiz']) >= 1:
            new_question = session['current_quiz'].pop()
            session['current_quiz'] = session['current_quiz']
            return jsonify(question=new_question)
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
    qstn = data['question']
    try:
        user_answer = int(data['userAnswer'])
    except ValueError:
        return jsonify(answer='Try again! Please enter a number.')
    else:
        if user_answer == session['current_facts'][qstn]:
            q = (models.UserScores
                 .update({models.UserScores.questions_correct: models.UserScores.questions_correct + 1})
                 .where(models.UserScores.id == session['current_user_score']))
            q.execute()
            session['current_num_correct'] += 1
            return jsonify(answer='CORRECT!')
        else:
            q = (models.UserScores
                 .update({models.UserScores.questions_wrong: models.UserScores.questions_wrong + 1})
                 .where(models.UserScores.id == session['current_user_score']))
            q.execute()
            session['current_num_incorrect'] += 1
            return jsonify(answer="Sorry! That's not the right answer.")


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
