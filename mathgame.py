from datetime import datetime
from functools import wraps
import random
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
            return redirect(url_for('index', quiz_type=None))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.is_teacher is False:
            return redirect(url_for('index', quiz_type=None))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Checks that the filename contains an extension.
    Checks that the extension is in ALLOWED_EXTENSIONS.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_equation_question(operation, qstn_type, num_start, num_end, neg_answers):
    if not neg_answers:
        q = (models.Questions.select()
             .where(models.Questions.question_op == operation,
                    models.Questions.question_type == qstn_type,
                    models.Questions.answer >= 0,
                    models.Questions.first_num >= num_start,
                    models.Questions.first_num <= num_end,
                    models.Questions.second_num >= num_start,
                    models.Questions.second_num <= num_end)
             .order_by(fn.Random()).limit(1)
             )
    else:
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


def get_number_bond_question(base_number):
    q = (models.Questions.select()
         .where(models.Questions.question_op == '+',
                models.Questions.question_type == 'Equation',
                models.Questions.answer == base_number)
         .order_by(fn.Random()).limit(1)
         )
    return q


def create_equation_quiz(operation_type, start_number, end_number, quiz_length):
    new_equation_quiz = models.Quizzes(math_op=operation_type,
                                       starting_num=start_number,
                                       ending_num=end_number,
                                       allow_neg_answers=False,
                                       quiz_length=quiz_length,
                                       quiz_type='Equation'
                                       )
    return new_equation_quiz


def create_number_bonds_quiz(start_number, end_number, quiz_length):
    new_number_bonds_quiz = models.Quizzes(math_op='+',
                                           starting_num=start_number,
                                           ending_num=end_number,
                                           allow_neg_answers=False,
                                           quiz_length=quiz_length,
                                           quiz_type='Number Bonds'
                                           )
    return new_number_bonds_quiz


def get_student_list(teacher_id):
    student_list = (models.User.select(models.User)
                    .join(models.Students, on=(models.User.id == models.Students.user_id))
                    .where(models.Students.teacher_id == teacher_id)
                    )
    return student_list


def create_teacher_quiz(teacher_id, quiz_name, quiz_id):
    new_teacher_quiz = models.TeacherQuizzes(teacher_id=teacher_id,
                                             quiz_name=quiz_name,
                                             quiz_id=quiz_id
                                             )
    return new_teacher_quiz


def student_list_from_form(form_data_dict):
    return [k for k, v in form_data_dict.items() if v == 'on']


def assign_quiz(student_list, quiz_id, teacher_id):
    for student in student_list:
        models.AssignedQuizzes.create(user_id=student,
                                      quiz_id=quiz_id,
                                      assigned_by_id=teacher_id
                                      )


def find_saved_user_quiz(quiz_id):
    saved_quiz = models.UserQuizzes.get(models.UserQuizzes.quiz_id == quiz_id)
    return saved_quiz


def find_saved_teacher_quiz(quiz_id):
    saved_quiz = models.TeacherQuizzes.get(models.TeacherQuizzes.quiz_id == quiz_id)
    return saved_quiz


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
            flash('Registration successful. Please log in.', 'success')
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
            flash('That username or password is incorrect.', 'danger')
            return render_template('login.html')
        else:
            if check_password_hash(user.password, password):
                session['username'] = username
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('That username or password is incorrect.', 'danger')
                return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logs a user out and removes information from the current session."""
    session.pop('username', None)
    session.pop('current_facts', None)
    session.pop('current_quiz_desc', None)
    session.pop('previous_questions', None)
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
                        .where(models.UserQuizzes.user_id == current_user.id)
                        )
        assigned_quizzes = (models.TeacherQuizzes.select()
                            .join(models.AssignedQuizzes,
                                  on=(models.TeacherQuizzes.quiz_id == models.AssignedQuizzes.quiz_id))
                            .where(models.AssignedQuizzes.user_id == current_user.id)
                            )
        quiz_list = user_quizzes[:6]
        assigned_quiz_list = assigned_quizzes[:6]

        return render_template('index.html',
                               selected_user=selected_user,
                               quiz_list=quiz_list,
                               assigned_quizzes=assigned_quiz_list,
                               )


@app.route('/game/<quiz_id>/<quiz_type>/<quiz_attempt_id>', methods=['GET', 'POST'])
@login_required
def game(quiz_id, quiz_type, quiz_attempt_id):
    selected_quiz = models.Quizzes.get(models.Quizzes.id == quiz_id)
    selected_quiz_type = quiz_type
    selected_quiz_attempt = models.QuizAttempts.get(models.QuizAttempts.id == quiz_attempt_id)
    user_quizzes = (models.UserQuizzes.select()
                    .where(models.UserQuizzes.user_id == current_user.id)
                    )
    assigned_quizzes = (models.TeacherQuizzes.select()
                        .join(models.AssignedQuizzes,
                              on=(models.TeacherQuizzes.quiz_id == models.AssignedQuizzes.quiz_id))
                        .where(models.AssignedQuizzes.user_id == current_user.id)
                        )
    quiz_list = user_quizzes[:6]
    assigned_quiz_list = assigned_quizzes[:6]
    return render_template('game.html',
                           selected_quiz=selected_quiz.id,
                           quiz_type=selected_quiz_type,
                           quiz_attempt=selected_quiz_attempt.id,
                           quiz_list=quiz_list,
                           assigned_quizzes=assigned_quiz_list
                           )


# Change this so it goes to '/profile/<user_id>'
@app.route('/profile/', methods=['GET', 'POST'])
@login_required
def profile():
    selected_user = models.User.get(models.User.id == current_user.id)
    quiz_list = (models.UserQuizzes.select()
                 .where(models.UserQuizzes.user_id == current_user.id)
                 )
    total_quizzes = (models.QuizAttempts.select()
                     .join(models.User, on=(models.QuizAttempts.user_id == models.User.id))
                     .where(models.User.id == current_user.id)
                     )
    total_assigned_quizzes = (models.TeacherQuizzes.select()
                              .join(models.AssignedQuizzes,
                                    on=(models.TeacherQuizzes.quiz_id == models.AssignedQuizzes.quiz_id))
                              .where(models.AssignedQuizzes.user_id == current_user.id)
                              )
    quiz_types = [quiz.quiz_type for quiz in total_quizzes]

    return render_template('profile.html',
                           selected_user=selected_user,
                           quiz_list=quiz_list,
                           assigned_quizzes=total_assigned_quizzes,
                           total_quizzes=total_quizzes,
                           quiz_types=quiz_types
                           )


@app.route('/uploader', methods=['GET', 'POST'])
@login_required
def uploader():
    selected_user = models.User.get(models.User.id == current_user.id)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
    file = request.files['file']

    if file.filename == '':
        flash('No file selected', 'danger')
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
    current_quiz = models.Quizzes.get(models.Quizzes.id == 0)
    current_quiz_attempt = models.QuizAttempts.create(user_id=current_user.id,
                                                      quiz_id=current_quiz.id,
                                                      quiz_type=current_quiz.math_op,
                                                      questions_correct=0,
                                                      questions_wrong=0,
                                                      questions_total=current_quiz.quiz_length,
                                                      date_take=datetime.now()
                                                      )
    session['current_facts'] = current_quiz.quiz_length
    session['current_quiz_desc'] = 'Basic Addition Math Facts from 0 to 10'
    session['previous_questions'] = []

    return redirect(url_for('game',
                            quiz_id=current_quiz.id,
                            quiz_type=current_quiz.quiz_type,
                            quiz_attempt_id=current_quiz_attempt.id
                            )
                    )


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

        new_cust_quiz = models.Quizzes.create(math_op=quiz_op,
                                              starting_num=quiz_start,
                                              ending_num=quiz_end,
                                              allow_neg_answers=False,
                                              quiz_length=quiz_length
                                              )

        if quiz_setup['save-quiz'] == 'yes':
            models.UserQuizzes.create(user_id=current_user.id,
                                      quiz_name=quiz_desc,
                                      quiz_id=new_cust_quiz.id
                                      )

        current_quiz_attempt = models.QuizAttempts.create(user_id=current_user.id,
                                                          quiz_id=new_cust_quiz.id,
                                                          quiz_type=quiz_op,
                                                          questions_correct=0,
                                                          questions_wrong=0,
                                                          questions_total=quiz_length,
                                                          date_taken=datetime.now()
                                                          )
        session['current_facts'] = quiz_length
        session['current_quiz_desc'] = quiz_desc
        session['previous_questions'] = []
        return redirect(url_for('game',
                                quiz_id=new_cust_quiz.id,
                                quiz_type=new_cust_quiz.quiz_type,
                                quiz_attempt_id=current_quiz_attempt.id
                                )
                        )
    else:
        # Check this, may not make sense
        return render_template('startquiz.html')


@app.route('/startsavedquiz/<saved_quiz_id>/<user_or_teacher>', methods=['GET', 'POST'])
@login_required
def startsavedquiz(saved_quiz_id, user_or_teacher):
    # Currently this does not allow you to retake the exact same questions
    if user_or_teacher == 'user':
        saved_quiz_info = find_saved_user_quiz(saved_quiz_id)
    elif user_or_teacher == 'teacher':
        saved_quiz_info = find_saved_teacher_quiz(saved_quiz_id)
    else:
        raise ValueError('There is a problem with this quiz.')

    base_quiz = models.Quizzes.get(models.Quizzes.id == saved_quiz_id)
    current_quiz_attempt = models.QuizAttempts.create(user_id=current_user.id,
                                                      quiz_id=saved_quiz_id,
                                                      quiz_type=base_quiz.math_op,
                                                      questions_correct=0,
                                                      questions_wrong=0,
                                                      questions_total=base_quiz.quiz_length,
                                                      date_taken=datetime.now()
                                                      )
    session['current_facts'] = base_quiz.quiz_length
    session['current_quiz_desc'] = saved_quiz_info.quiz_name
    session['previous_questions'] = []
    return redirect(url_for('game',
                            quiz_id=saved_quiz_id,
                            quiz_type=base_quiz.quiz_type,
                            quiz_attempt_id=current_quiz_attempt.id
                            )
                    )


# Possibly delete this route
@app.route('/checkquiztype', methods=['GET'])
@login_required
def checkquiztype():
    try:
        session['current_quiz_type']
    except KeyError:
        return jsonify(question="You haven't started a quiz!", quiz_type=None)
    else:
        return jsonify(quiz_type=session['current_quiz_type'])


@app.route('/numberbond', methods=['GET'])
@login_required
def numberbond():
    try:
        session['current_facts']
    except KeyError:
        return jsonify(question="You haven't started a quiz!", quiz_type=None)
    else:
        if session['current_facts'] > 0:
            base_number = random.randint(session['current_end_start'][0], session['current_end_start'][1])
            session['current_facts'] -= 1
            return jsonify(question=base_number, quiz_type=session['current_quiz_type'])
        else:
            current_correct = session['current_num_correct']
            current_incorrect = session['current_num_incorrect']
            return jsonify(question='End of Quiz!',
                           quiz_type=None,
                           current_correct=current_correct,
                           current_incorrect=current_incorrect,
                           )


@app.route('/question', methods=['GET', 'POST'])
@login_required
def question():
    if request:
        data = request.get_data().decode("utf-8")
        provided_quiz_id = data.split('=')[1].split('&')[0]
        provided_quiz = models.Quizzes.get(models.Quizzes.id == provided_quiz_id)
        provided_quiz_attempt_id = data.split('=')[2]

    else:
        return jsonify(question='Something went wrong. No valid quiz provided.', quiz_type=None)

    try:
        # This is an int equal to the length of the quiz
        session['current_facts']
    except KeyError:
        return jsonify(question="You haven't started a quiz!", quiz_type=None)
    else:
        if session['current_facts'] > 0:
            problem = get_equation_question(provided_quiz.math_op,
                                            provided_quiz.quiz_type,
                                            provided_quiz.starting_num,
                                            provided_quiz.ending_num,
                                            provided_quiz.allow_neg_answers
                                            )

            if problem[0].id in session['previous_questions']:
                # Delete after more testing
                print("NEED NEW PROBLEM: {}".format(problem[0].id))
                problem = get_equation_question(provided_quiz.math_op,
                                                provided_quiz.quiz_type,
                                                provided_quiz.starting_num,
                                                provided_quiz.ending_num,
                                                provided_quiz.allow_neg_answers
                                                )

            # session['current_question'] = problem[0].id
            # Delete after more testing
            print("CURRENT QUESTION ID: {}".format(problem[0].id))
            session['previous_questions'].append(problem[0].id)
            # Delete after more testing
            print("PREV QSTS: {}".format(session['previous_questions']))
            qst = problem[0].question
            session['current_facts'] -= 1
            # Delete after more testing
            print("CURRENT FACTS: {}".format(session['current_facts']))
            return jsonify(question=qst, quiz_type=provided_quiz.quiz_type, question_id=problem[0].id)
        else:
            current_quiz_attempt = models.QuizAttempts.get(models.QuizAttempts.id == provided_quiz_attempt_id)
            current_correct = current_quiz_attempt.questions_correct
            current_incorrect = current_quiz_attempt.questions_wrong
            return jsonify(question='End of Quiz!',
                           quiz_type=None,
                           current_correct=current_correct,
                           current_incorrect=current_incorrect,
                           )


@app.route('/checkanswer', methods=['GET', 'POST'])
@login_required
def checkanswer():
    data = request.form
    print("CHECK ANSWER DATA: {}".format(data))
    current_quiz_id = int(data['quiz_id'])
    current_quiz_attempt_id = int(data['quiz_attempt_id'])
    current_question_id = int(data['question_id'])
    try:
        user_answer = int(data['userAnswer'])
    except ValueError:
        return jsonify(answer='Try again! Please enter a number.')
    else:
        # correct_answer = models.Questions.get(models.Questions.id == session['current_question']).answer
        correct_answer = models.Questions.get(models.Questions.id == current_question_id).answer
        if user_answer == correct_answer:
            q_c1 = (models.QuizAttempts
                    .update({models.QuizAttempts.questions_correct: models.QuizAttempts.questions_correct + 1})
                    .where(models.QuizAttempts.id == current_quiz_attempt_id))
            q_c1.execute()
            models.QuestionAttempts.create(user_id=current_user.id,
                                           question_id=current_question_id,
                                           quiz_id=current_quiz_id,
                                           correct=True,
                                           incorrect=False,
                                           date_attempted=datetime.now()
                                           )
            # session['current_num_correct'] += 1
            return jsonify(answer='CORRECT!')
        else:
            q_w1 = (models.QuizAttempts
                    .update({models.QuizAttempts.questions_wrong: models.QuizAttempts.questions_wrong + 1})
                    .where(models.QuizAttempts.id == current_quiz_attempt_id))
            q_w1.execute()
            models.QuestionAttempts.create(user_id=current_user.id,
                                           question_id=current_question_id,
                                           quiz_id=current_quiz_id,
                                           correct=False,
                                           incorrect=True,
                                           date_attempted=datetime.now()
                                           )
            # session['current_num_incorrect'] += 1
            return jsonify(answer="Sorry! That's not the right answer.")


@app.route('/checknumberbond', methods=['GET', 'POST'])
@login_required
def checknumberbond():
    data = request.form
    print(data)
    return render_template('index.html')


@app.route('/teacher', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher():
    student_list = (models.User.select(models.User)
                    .join(models.Students, on=(models.User.id == models.Students.user_id))
                    .where(models.Students.teacher_id == current_user.id)
                    )
    return render_template('teacher.html',
                           student_list=student_list)


@app.route('/addstudent', methods=['GET', 'POST'])
@login_required
@teacher_required
def addstudent():
    if request.form:
        student_username = request.form['student-username']
        student_record = models.User.get(models.User.username == student_username)
        student_id = student_record.id
        models.Students.create(user_id=student_id, teacher_id=current_user.id)
        flash('Student added.', 'success')
        return redirect(url_for('teacher'))
    else:
        flash('Something went wrong. Please try again.', 'danger')
        return redirect(url_for('teacher'))


@app.route('/saveteacherquiz', methods=['GET', 'POST'])
@login_required
@teacher_required
def saveteacherquiz():
    student_list = get_student_list(current_user.id)

    if request.form:
        assigned_to = student_list_from_form(request.form.to_dict())
        nq = request.form
        nq_desc = nq['test-name']
        nq_op = nq['fact-type']
        nq_length = int(nq['number-questions'])

        if nq['start-num'] != '':
            nq_start = int(nq['start-num'])
        else:
            nq_start = 0

        if nq['end-num'] != '':
            nq_end = int(nq['end-num'])
        else:
            nq_end = 10

        new_quiz = create_equation_quiz(nq_op, nq_start, nq_end, nq_length)
        new_quiz.save()
        teacher_quiz = create_teacher_quiz(current_user.id, nq_desc, new_quiz.id)
        teacher_quiz.save()
        assign_quiz(assigned_to, new_quiz.id, current_user.id)
        flash('Quiz saved.', 'success')
        return redirect(url_for('teacher'))
    else:
        return render_template('teacherquiz.html',
                               student_list=student_list)


@app.route('/numberbonds', methods=['GET', 'POST'])
@login_required
@teacher_required
def numberbonds():
    student_list = get_student_list(current_user.id)

    if request.form:
        assigned_to = student_list_from_form(request.form.to_dict())
        nb_form = request.form
        nb_desc = nb_form['test-name']
        nb_length = int(nb_form['number-questions'])

        if nb_form['end-num'] != '':
            nb_end = int(nb_form['end-num'])
        else:
            nb_end = 10

        if nb_form['start-num'] != '':
            nb_start = int(nb_form['start-num'])
        else:
            nb_start = nb_end

        new_nb_quiz = create_number_bonds_quiz(nb_start, nb_end, nb_length)
        new_nb_quiz.save()
        new_teacher_quiz = create_teacher_quiz(current_user.id, nb_desc, new_nb_quiz.id)
        new_teacher_quiz.save()
        assign_quiz(assigned_to, new_nb_quiz.id, current_user.id)
        flash('Quiz saved.', 'success')
        return redirect(url_for('teacher'))
    else:
        return render_template('numberbonds.html',
                               student_list=student_list)


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
        except peewee.IntegrityError:
            flash('Unable to populate database.', 'danger')
        else:
            flash('Database populated successfully.', 'success')
    return render_template('admin.html')


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG)
