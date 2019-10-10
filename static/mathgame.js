//Store some info about the session
const userSessionStorage = window.sessionStorage;

//Get and display equation quiz question
//const getEquationQuestion = () => {
//    $.ajax({url:"/question", dataType:"json"}).then( data => {
//      emptyTenframe();
//      if (data.question === "You haven't started a quiz!" || data.question === "End of Quiz!") {
//        $('#quiz-question').append(`<h3>${data.question}</h3>`);
//        $('#user-answer').hide();
//        $('#submit-answer-button').hide();
//        $('#show-tenframe').hide();
//        //$('#answer-tenframe').hide();
//      } else {
//        $('#quiz-question').append(`<h3>${data.question} = ?</h3>`);
//        $('#get-next-btn').hide();
//        const quizNumbers = splitOnOperator($.trim($('#quiz-question').text()).split(" = ")[0]);
//        if (useTenframes(quizNumbers, data.question) === false) {
//          $('#show-tenframe').hide();
//         // $('#answer-tenframe').hide();
//        }
//      }
//    });
//};

//Get and display number bond quiz question
const getNumberBondQuestion = () => {
    $.ajax({url:"/numberbond", dataType:"json"}).then( data => {
        console.log("NUMBER BOND DATA: ", data.question, data.quiz_type);
        if (data.question === "You haven't started a quiz!" || data.question === "End of Quiz!") {
            $('#quiz-question').append(`<h3>${data.question}</h3>`);
        } else {
            console.log("NUMBER BOND QUESTION: ", data.question);
            $('#base-number').append(`<h3>${data.question}</h3>`);
        }
    });
};

//Detect user touch
//window.addEventListener('touchstart', function onFirstTouch() {
//  userSessionStorage.setItem('touch_enable', 'true');
//  console.log(userSessionStorage.getItem('touch_enable'));
//  window.removeEventListener('touchstart', onFirstTouch, false);
//}, false);

$.ajax({url:"/checkquiztype", dataType:"json"}).then( data => {
  if (data.quiz_type === null) {
    $('#quiz-message').append(`<h3>${data.question}</h3>`);
  }
//  else if (data.quiz_type === 'Equation') {
//    getEquationQuestion();
//  } else if (data.quiz_type === 'Number Bonds') {
//    getNumberBondQuestion();
//  } else {
//    $('#quiz-message').append(`<h3>Something went wrong</h3>`);
//  }
});

//Check user's password
//Submit user registration info if password is typed correctly in password and confirm password fields
$('#register-form').submit( evt => {
  const username = $('#createUsername').val();
  const password = $('#createPassword').val();
  const confirmPassword = $('#confirmPassword').val();
  if (password !== confirmPassword) {
    alert("Those passwords do not match.");
    $('#createUsername').val("");
    $('#createPassword').val("");
    $('#confirmPassword').val("");
//    $('#adminCheck').prop("checked", false);
//    $('#teacherCheck').prop("checked", false);
    evt.preventDefault();
  }
});

//Give user session the current username on signin
$('#signin-form').submit( evt => {
  const username = $('#inputUsername').val();
  userSessionStorage.setItem('username', username);
  console.log(userSessionStorage.getItem('username'));
});

//Check ending number
$('#quiz-setup-form').submit( evt => {
  const startNum = parseInt($('#startNum').val());
  const endNum = parseInt($('#endNum').val());
  if (startNum > endNum) {
    alert("The starting number must be greater than the ending number. Please provide a new starting number.");
    $('#startNum').val("");
    evt.preventDefault();
  } else if (endNum > 2000) {
    alert("The ending number must be 2000 or less. Please provide a new ending number.");
    $('#endNum').val("");
    evt.preventDefault();
  }
});

//Submit user's answer to quiz question
//Display "correct" or "wrong" feedback for question answer
//$('#user-answer-equation').submit( evt => {
//  evt.preventDefault();
//  $('#show-tenframe').hide();
//  const url = $(evt.target).attr('action');
//  const question = $('h3').text().slice(0, -4);
//  const userAnswer = $('#user-answer-text').val();
//  $.ajax(url, {
//    dataType: "json",
//    data: {"question": question, "userAnswer": userAnswer},
//    type: "POST",
//  }).then( data => {
//    if (data.answer === "Try again! Please enter a number.") {
//      $('#quiz-answer').empty();
//      $("#quiz-answer").append(data.answer);
//      $('#user-answer-text').val("");
//    } else if (data.answer === "CORRECT!") {
//      $('#game-container').css("background-color", "mediumseagreen");
//      $('#quiz-question').hide();
//      $('#quiz-answer').empty();
//      $("#quiz-answer").append(`<h3>${data.answer} ${question} = ${userAnswer}.</h3>`);
//      $('#user-answer-equation').hide();
//      $('#submit-answer-button').hide();
//      $('#user-answer-text').val("");
//      $('#tenframes').prop('hidden', true);
//      //$('#answer-tenframe').hide();
//      setTimeout(nextQuestion, 2000);
//    } else if (data.answer === "Sorry! That's not the right answer.") {
//      $('#game-container').css("background-color", "indianred");
//      $('#quiz-question').hide();
//      $('#quiz-answer').empty();
//      $("#quiz-answer").append(`<h3>${data.answer} ${question} does not equal ${userAnswer}.</h3>`);
//      $('#user-answer-equation').hide();
//      $('#submit-answer-button').hide();
//      $('#user-answer-text').val("");
//      $('#tenframes').prop('hidden', true);
//      //$('#answer-tenframe').hide();
//      setTimeout(nextQuestion, 2000);
//    }
//  });
//});

$('#user-answer-number-bond').submit( evt => {
    evt.preventDefault();
    console.log("CHECK BOND");
    const url = $(evt.target).attr('action');
    const base = $('#base-number').text();
    const userBondOne = $('#user-answer-bond-1').val();
    const userBondTwo = $('#user-answer-bond-2').val();
    console.log(userBondOne, userBondTwo)
    $.ajax(url, {
        dataType: "json",
        data: {"base": base, "userBondOne": userBondOne, "userBondTwo": userBondTwo},
        type: "POST",
    }).then( data => {
        if (data.answer === "Try again! Please enter a number.") {
            $('#base-number').empty();
            $('#base-number').append(data.answer);
            $('#user-answer-bond-1').val("");
            $('#user-answer-bond-2').val("");
        } else if (data.answer === "CORRECT!") {
            $('#game-container').css("background-color", "mediumseagreen");
            $('#base-number').hide();
            $('#user-answer-bond-1').hide();
            $('#user-answer-bond-2').hide();
            $('#submit-bond-button').hide();
        }
    })
});

//Make profile image show profile pic modal
$('#profile-pic').click( evt => {
  $('#profileModal').modal('show');
});

//Makes remove pic button function
$('#remove-pic').click( evt => {
  location.href = '/removeimage';
});

//Make Add Student button in teacher view display add student modal
$('#teacher-add-student').click( evt => {
    $('#addStudentModal').modal('show');
});

//Make Student List button show the student list
$('#teacher-student-list').click( evt => {
    $('#studentListModal').modal('show');
});

