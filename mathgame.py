# Add: User classes---e.g., student, teacher, administrator --> ADDED w/out distinct functionality
# Add ability to create custom quiz --> ADDED
# End of quiz screen should show how many questions you got right/wrong for that quiz. Could also show a bar graph. ADDED w/out graph
# Move overall right/wrong to a profile/statistics page
# Overall scores should be available on profile page.
# Scores for quick quizzes not kept in database. Scores for teacher-assigned quizzes or custome named quizzes should
# be kept in database and separated by quiz type. Need to add new table for keeping quizzes.
# Add ability to create a quiz with more than one kind of fact (addition AND subtraction, etc.)
# Add sidebar for some of this stuff --> ADDED
# Add ability to save your custom quiz --> ADDED
# Add profile page with stats
# Add list of your saved custom quizzes --> ADDED
# Change list of custom quizzes in sidebar to show only most recent 5 (or 10).
# If more than that number sidebar should show a button for "more" that takes you to your profile page
# Teachers should be able to: see list of all their students by class, create a new class (w/class code), create and save quizzes,
# assign specific quizzes to students/classes with due dates, create assignments (e.g., take 4 addition quizzes by Tues.), see student
# progress, send messages to students (?)
# Students should be able to send messages to teacher for help on a specific quiz (?)
# Distinct functionality for different classes
# Graphs to visually show progress over time
# Achievements with badges?

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, sessions, url_for
from flask_bcrypt import check_password_hash
from flask_login import (current_user, LoginManager, login_required, login_user, logout_user, UserMixin)

import models

app = Flask(__name__)
app.secret_key = 'dshfjkrehtuia^&#C@@%&*(fdsh21243254235'
DEBUG = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#
# class Test:
#     """Creates the math test from the test type (description), a dictionary of the math questions and answers (created
#         by the CreateMathFacts class), and the number of questions.
#     """
#     def __init__(self, test_type, test_questions_answers, test_length=-1):
#         self.test_type = test_type
#         self.test_questions_answers = test_questions_answers
#         if test_length == -1 or test_length > len(self.test_questions_answers):
#             self.test_length = len(self.test_questions_answers)
#         else:
#             self.test_length = test_length
#         self.test_questions = random.sample(list(self.test_questions_answers), self.test_length)
#
#     def test_type(self):
#         return self.test_type
#
#     def list_questions(self):
#         for question in self.test_questions_answers:
#             print(question)
#
#     def test_length(self):
#         return self.test_length
#
#     def grab_question(self):
#         return self.test_questions.pop()
#
#     def grab_answer(self, quiz_question):
#         return self.test_questions_answers[quiz_question]
#
#
# class CreateMathFacts:
#     """Creates the set of questions and answers to feed into the Test class. Takes an operator (+, -, *), whether or
#         not to allow negative answers (true/false), a starting number, and an ending number to use when creating
#         the facts. For example, if you want to test addition math facts from 0 to 10, the start number is 0, the
#         end number is 10.
#     """
#     def __init__(self, math_op="+", start_num=0, end_num=10, neg_answers=False):
#         self.math_op = math_op
#         self.start_num = start_num
#         self.end_num = end_num
#         self.neg_answers = neg_answers
#
#     math_operators = {"+": operator.add,
#                       "-": operator.sub,
#                       "*": operator.mul,
#                       }
#
#     def create_facts(self):
#         facts = {}
#         first_num = 0
#
#         def in_dict(k, v, dictionary):
#             if self.neg_answers is True:
#                 if k not in dictionary:
#                     dictionary[k] = v
#             elif self.neg_answers is False:
#                 if k not in dictionary and v >= 0:
#                     dictionary[k] = v
#
#         while first_num <= self.end_num:
#             for i in range(self.start_num, self.end_num+1):
#                 key1 = "{} {} {}".format(first_num, self.math_op, i)
#                 value1 = self.math_operators[self.math_op](first_num, i)
#                 in_dict(key1, value1, facts)
#                 #print(key1)
#
#                 if first_num != i:
#                     key2 = "{} {} {}".format(i, self.math_op, first_num)
#                     value2 = self.math_operators[self.math_op](i, first_num)
#                     in_dict(key2, value2, facts)
#                     key3 = "{} {} {}".format(i, self.math_op, i)
#                     value3 = self.math_operators[self.math_op](i, i)
#                     in_dict(key3, value3, facts)
#                     #print(key2)
#                     #print(key3)
#             first_num += 1
#
#         return facts


# Old function to run the test on the command line.
# def run_test(test):
#     num_correct = 0
#     num_wrong = 0
#     while len(test.test_questions) >= 1:
#         question = test.grab_question()
#         print("----> ", question)
#         answer = int(input("Your Answer: "))
#         if answer == test.test_questions_answers[question]:
#             print("CORRECT!")
#             num_correct += 1
#         else:
#             print("WRONG!")
#             num_wrong += 1
#     print("Number Correct: ", num_correct)
#     print("Number Wrong: ", num_wrong)


#TESTMATHFACTS = CreateMathFacts().create_facts()
#EXAMPLETEST = Test("Basic Addition Math Facts from 0 to 10", TESTMATHFACTS, 10)


@login_manager.user_loader
def load_user(id):
    try:
        return models.User.get(models.User.id == id)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.connection()
    g.user = current_user


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    else:
        if 'username' in session:
            quiz_list = (models.SavedQuizzes.select()
                         .join(models.User, on=(models.SavedQuizzes.user_id == models.User.id))
                         .where(models.User.id == current_user.id))

            print("Logged in as {}".format(session['username']))
        return render_template('index.html', quiz_list=quiz_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.form:
        user_info = request.form
        username = user_info['username']
        password = user_info['password']
        try:
            user = models.User.get(models.User.username == username)
        except models.DoesNotExist:
            flash("That username or password is incorrect. OMG BATS")
            return render_template('login.html')
        else:
            if check_password_hash(user.password, password):
                session['username'] = username
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("That username or password is incorrect. OMG CATS")
                return render_template('login.html')
    else:
        return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    session.pop('username', None)
    session.pop('current_quiz', None)
    session.pop('current_facts', None)
    session.pop('current_quiz_desc', None)
    session.pop('current_num_correct', None)
    session.pop('current_num_incorrect', None)
    logout_user()
    return redirect(url_for('index'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.form:
        user_reg = request.form
        username = user_reg['username']
        password = user_reg['password']
        print("USERNAME", username)
        print("PASSWORD: ", password)
        try:
            models.User.create_user(
                username=username,
                password=password
            )
            models.Score.create(
                user_id=models.User.get(models.User.username == username),
                total_quiz_num=0,
                total_questions_correct=0,
                total_questions_wrong=0,
            )
            return redirect(url_for('login'))
        except ValueError:
            return render_template('register.html')
    else:
        return render_template('register.html')


@app.route("/startquickquiz", methods=["GET", "POST"])
@login_required
def startquickquiz():
    #new_test = Test("Basic Addition Math Facts from 0 to 10", CreateMathFacts().create_facts(), 10)
    new_test = models.SavedQuizzes(user=current_user.id,
                                   quiz_name="Basic Addition Math Facts from 0 to 10",
                                   created_by=current_user.id,
                                   assigned_by=None,
                                   math_op="+",
                                   starting_num=0,
                                   ending_num=10,
                                   allow_neg_answers=False,
                                   quiz_length=10,
                                   )
    current_facts = new_test.create_facts()
    current_quiz = new_test.create_test(current_facts)
    session['current_facts'] = current_facts
    session['current_quiz'] = current_quiz
    session['current_quiz_desc'] = new_test.quiz_name
    session['current_num_correct'] = 0
    session['current_num_incorrect'] = 0
    q = (models.Score
         .update({models.Score.total_quiz_num: models.Score.total_quiz_num + 1})
         .where(models.Score.user_id == current_user.id))
    q.execute()
    return redirect(url_for('index'))


@app.route("/startcustomquiz", methods=["GET", "POST"])
@login_required
def startcustomquiz():
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
                                            created_by=current_user.id,
                                            assigned_by=current_user.id,
                                            math_op=quiz_op,
                                            starting_num=quiz_start,
                                            ending_num=quiz_end,
                                            allow_neg_answers=False,
                                            quiz_length=quiz_length,
                                            )

        if quiz_setup['save-quiz'] == 'yes':
            new_cust_quiz.save()

        cust_facts = new_cust_quiz.create_facts()
        cust_quiz = new_cust_quiz.create_test(cust_facts)
        session['current_facts'] = cust_facts
        session['current_quiz'] = cust_quiz
        session['current_quiz_desc'] = new_cust_quiz.quiz_name
        session['current_num_correct'] = 0
        session['current_num_incorrect'] = 0
        q = (models.Score
             .update({models.Score.total_quiz_num: models.Score.total_quiz_num + 1})
             .where(models.Score.user_id == current_user.id))
        q.execute()

        return redirect(url_for('index'))
    else:
        return render_template('startquiz.html')


@app.route("/startsavedquiz/<saved_quiz_id>", methods=["GET", "POST"])
@login_required
def startsavedquiz(saved_quiz_id):
    saved_quiz_base = (models.SavedQuizzes.get(models.SavedQuizzes.id == saved_quiz_id))
    saved_quiz_facts = saved_quiz_base.create_facts()
    saved_quiz = saved_quiz_base.create_test(saved_quiz_facts)
    session['current_facts'] = saved_quiz_facts
    session['current_quiz'] = saved_quiz
    session['current_quiz_desc'] = saved_quiz_base.quiz_name
    session['current_num_correct'] = 0
    session['current_num_incorrect'] = 0
    q = (models.Score
         .update({models.Score.total_quiz_num: models.Score.total_quiz_num + 1})
         .where(models.Score.user_id == current_user.id))
    q.execute()
    return redirect(url_for('index'))


@app.route("/question", methods=["GET"])
@login_required
def question():
    try:
        len(session['current_quiz']) > 0
    except:
        return jsonify(question="You haven't started a quiz!")
    else:
        if len(session['current_quiz']) >= 1:
            new_question = session['current_quiz'].pop()
            session['current_quiz'] = session['current_quiz']
            return jsonify(question=new_question)
        else:
            q = (models.Score.select()
                             .join(models.User, on=(models.Score.user_id == models.User.id))
                             .where(models.User.id == current_user.id))
            overall_correct = [num.total_questions_correct for num in q]
            overall_incorrect = [num.total_questions_wrong for num in q]
            current_correct = session['current_num_correct']
            current_incorrect = session['current_num_incorrect']
            return jsonify(question="End of Quiz!",
                           overall_correct=overall_correct,
                           overall_incorrect=overall_incorrect,
                           current_correct=current_correct,
                           current_incorrect=current_incorrect,
                           )


@app.route("/checkanswer", methods=["GET", "POST"])
def checkanswer():
    data = request.form
    quiz_question = data['question']
    # user_answer = int(data['userAnswer'])
    try:
        user_answer = int(data['userAnswer'])
    except ValueError:
        return jsonify(answer="Try again! Please enter a number.")
    else:
        if user_answer == session['current_facts'][quiz_question]:
            q = (models.Score
                 .update({models.Score.total_questions_correct: models.Score.total_questions_correct + 1})
                 .where(models.Score.user_id == current_user.id))
            q.execute()
            session['current_num_correct'] += 1
            return jsonify(answer="CORRECT!")
        else:
            q = (models.Score
                 .update({models.Score.total_questions_wrong: models.Score.total_questions_wrong + 1})
                 .where(models.Score.user_id == current_user.id))
            q.execute()
            session['current_num_incorrect'] += 1
            return jsonify(answer="Sorry! That's not the right answer.")


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG)
