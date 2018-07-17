import operator, random
from flask import Flask, g, jsonify, redirect, render_template, request, session, sessions, url_for
from flask_bcrypt import check_password_hash
from flask_login import (current_user, LoginManager, login_required, login_user, logout_user, UserMixin)

import models

app = Flask(__name__)
app.secret_key = 'dshfjkrehtuia^&#C@@%&*(fdsh21243254235'
DEBUG = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Test:

    def __init__(self, test_type, test_questions_answers, test_length=-1):
        self.test_type = test_type
        self.test_questions_answers = test_questions_answers
        if test_length == -1 or test_length > len(self.test_questions_answers):
            self.test_length = len(self.test_questions_answers)
        else:
            self.test_length = test_length
        self.test_questions = random.sample(list(self.test_questions_answers), self.test_length)

    def test_type(self):
        return self.test_type

    def list_questions(self):
        for question in self.test_questions_answers:
            print(question)

    def test_length(self):
        return self.test_length

    def grab_question(self):
        return self.test_questions.pop()

    def grab_answer(self, quiz_question):
        return self.test_questions_answers[quiz_question]


class CreateMathFacts:

    def __init__(self, math_op="+", neg_answers=False, start_num=0, end_num=10):
        self.math_op = math_op
        self.neg_answers = neg_answers
        self.start_num = start_num
        self.end_num = end_num

    math_operators = {"+": operator.add,
                      "-": operator.sub,
                      "*": operator.mul,
                      }

    def create_facts(self):
        facts = {}
        first_num = 0

        def in_dict(k, v, dictionary):
            if self.neg_answers is True:
                if k not in dictionary:
                    dictionary[k] = v
            elif self.neg_answers is False:
                if k not in dictionary and v >= 0:
                    dictionary[k] = v

        while first_num <= self.end_num:
            for i in range(self.start_num, self.end_num+1):
                key1 = "{} {} {}".format(first_num, self.math_op, i)
                value1 = self.math_operators[self.math_op](first_num, i)
                in_dict(key1, value1, facts)
                #print(key1)

                if first_num != i:
                    key2 = "{} {} {}".format(i, self.math_op, first_num)
                    value2 = self.math_operators[self.math_op](i, first_num)
                    in_dict(key2, value2, facts)
                    key3 = "{} {} {}".format(i, self.math_op, i)
                    value3 = self.math_operators[self.math_op](i, i)
                    in_dict(key3, value3, facts)
                    #print(key2)
                    #print(key3)
            first_num += 1

        return facts


def run_test(test):
    num_correct = 0
    num_wrong = 0
    while len(test.test_questions) >= 1:
        question = test.grab_question()
        print("----> ", question)
        answer = int(input("Your Answer: "))
        if answer == test.test_questions_answers[question]:
            print("CORRECT!")
            num_correct += 1
        else:
            print("WRONG!")
            num_wrong += 1
    print("Number Correct: ", num_correct)
    print("Number Wrong: ", num_wrong)



TESTMATHFACTS = CreateMathFacts().create_facts()
EXAMPLETEST = Test("Kindergarten Math Facts", TESTMATHFACTS, 10)


@login_manager.user_loader
def load_user(id):
    try:
        return models.User.get(models.User.id==id)
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
    # Add button to create new addition test if logged in.
    if not current_user.is_authenticated:
        return render_template('login.html')
    else:
        if 'username' in session:
            print("Logged in as {}".format(session['username']))
        return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    user_info = request.form
    username = user_info['username']
    password = user_info['password']
    try:
        user = models.User.get(models.User.username == username)
    except models.DoesNotExist:
        return jsonify(msg="That username or password is incorrect.")
    else:
        if check_password_hash(user.password, password):
            session['username'] = username
            login_user(user)
            return redirect(url_for('index'))
        else:
            return jsonify(msg="That username or password is incorrect.")


@app.route("/logout")
@login_required
def logout():
    session.pop('username', None)
    session.pop('current_quiz', None)
    session.pop('current_facts', None)
    logout_user()
    return redirect(url_for('index'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.form:
        user_reg = request.form
        username = user_reg['username']
        password = user_reg['password']
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
        except ValueError:
            return jsonify(msg="That username already exists.")
        else:
            return jsonify(url="/login")
    else:
        return jsonify(url="/register")


@app.route("/startquiz", methods=["GET", "POST"])
@login_required
def startquiz():
    new_test = Test("Kindergarten Addition Math Facts", CreateMathFacts().create_facts(), 10)
    session['current_facts'] = new_test.test_questions_answers
    session['current_quiz'] = new_test.test_questions
   # print(session['current_quiz'])
    q = (models.Score
         .update({models.Score.total_quiz_num: models.Score.total_quiz_num + 1})
         .where(models.Score.user_id == current_user.id))
    q.execute()
    return redirect(url_for('index'))


@app.route("/question", methods=["GET"])
def question():
    try:
        len(session['current_quiz']) > 0
    except:
        return jsonify(question="You haven't started a quiz!")
    else:
        if len(session['current_quiz']) >= 1:
           # print("CURRENT_QUIZ", session['current_quiz'])
            new_question = session['current_quiz'].pop()
            session['current_quiz'] = session['current_quiz']
           # print("POPPPED: ", len(session['current_quiz']))
           # print("QUIZ AFTER POP", session['current_quiz'])
            return jsonify(question=new_question)
        else:
            q = (models.Score.select()
                             .join(models.User, on=(models.Score.user_id == models.User.id))
                             .where(models.User.id == current_user.id))
            total_correct = [num.total_questions_correct for num in q]
            total_wrong = [num.total_questions_wrong for num in q]
            return jsonify(question="End of Quiz!", correct=total_correct, wrong=total_wrong)


@app.route("/checkanswer", methods=["GET", "POST"])
def checkanswer():
    data = request.form
    quiz_question = data['question']
    user_answer = int(data['userAnswer'])
    if user_answer == session['current_facts'][quiz_question]:
        q = (models.Score
             .update({models.Score.total_questions_correct: models.Score.total_questions_correct + 1})
             .where(models.Score.user_id == current_user.id))
        q.execute()
        return jsonify(answer="CORRECT!")
    else:
        q = (models.Score
             .update({models.Score.total_questions_wrong: models.Score.total_questions_wrong + 1})
             .where(models.Score.user_id == current_user.id))
        q.execute()
        return jsonify(answer="Sorry! That's not the right answer.")


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG)

