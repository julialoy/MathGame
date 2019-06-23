//Store some info about the session
const userSessionStorage = window.sessionStorage;

//Split string on mathematical operator
const splitOnOperator = (myString) => {
  if (myString.includes('+')) {
    const splitNum = myString.split(" + ");
    return splitNum;
  } else if (myString.includes('-')) {
    const splitNum = myString.split(" - ");
    return splitNum;
  } else if (myString.includes('*')) {
    const splitNum = myString.split(" * ");
    return splitNum;
  }
};

//Check whether to use ten frames
const useTenframes = (numbers, qst) => {
  if (qst.includes('*')) {
    const tenFrame = false;
    return tenFrame;
  } else if (qst.includes('/')) {
    const tenFrame = false;
    return tenFrame;
  }

  if (numbers[0] < 11 && numbers[1] < 11) {
    const tenFrame = true;
    return tenFrame;
  } else {
    const tenFrame = false;
    return tenFrame;
  }
};

//Fill two ten frames per the current quiz question
const fillTenframe = (numbers, qst) => {
  if (useTenframes(numbers, qst) === true) {
      const tableOne = document.getElementById('tenframe-table-one');
      const tableTwo = document.getElementById('tenframe-table-two');
      const tableOneCells = tableOne.getElementsByTagName("td");
      const tableTwoCells = tableTwo.getElementsByTagName("td");

      for (i = 0; i < parseInt(numbers[0]); i++) {
        const redSphereOne = tableOneCells[i].firstChild;
        redSphereOne.setAttribute("style", "background-color:#17a2b8");
      }

      for (i = 0; i <parseInt(numbers[1]); i++) {
        const redSphereTwo = tableTwoCells[i].firstChild;
        redSphereTwo.setAttribute("style", "background-color:#17a2b8");
      }
  } else {
    $('#show-tenframe').hide();
  }
};

//Change to two empty ten frames
const emptyTenframe = () => {
  const tableOne = document.getElementById('tenframe-table-one');
  const tableTwo = document.getElementById('tenframe-table-two');
  const tableOneCells = tableOne.getElementsByTagName("td");
  const tableTwoCells = tableTwo.getElementsByTagName("td");
  for (i = 0; i < 10; i++) {
    const redSphereOne = tableOneCells[i].firstChild;
    const redSphereTwo = tableTwoCells[i].firstChild;
    redSphereOne.setAttribute("style", "background-color:#212529");
    redSphereTwo.setAttribute("style", "background-color:#212529");
  }
};

//Get the next quiz question
const nextQuestion = () => {
  $('#game-container').css("background-color", "lightgrey");
  $('#quiz-question').empty();
  $('#quiz-answer').empty();
  $('#quiz-question').show();
  $('#user-answer').show();
  $('#submit-answer-button').show();
  emptyTenframe();
  $('#show-tenframe').html('Show Ten Frame');
  $.ajax({url:"/question", dataType:"json"}).then( data => {
    $('#get-next-btn').hide();
    if (data.question === "You haven't started a quiz!") {
      $('#quiz-question').append(`<h3>${data.question}</h3>`)
      $('#user-answer').hide();
      $('#submit-answer-button').hide();
      $('#show-tenframe').hide();
    } else if (data.question === "End of Quiz!") {
      $('#quiz-question').append(`<h3>${data.question}</h3>`)
      $('#user-answer').hide();
      $('#submit-answer-button').hide();
      $('#show-tenframe').hide();
      $('#quiz-question').append(`<p>You answered ${data.current_correct} questions correctly!</p>`);
      $('#quiz-question').append(`<p>You answered ${data.current_incorrect} questions incorrectly.</p>`);
    } else {
      $("#quiz-question").append(`<h3>${data.question} = ?</h3>`);
      const quizNumbers = splitOnOperator($.trim($('#quiz-question').text()).split(" = ")[0]);
      if (useTenframes(quizNumbers, data.question) === true) {
        $('#show-tenframe').show();
      } else {
        $('#show-tenframe').hide();
      }
    };
  });
  $('#user-answer-text').focus();
};

//Detect user touch
//window.addEventListener('touchstart', function onFirstTouch() {
//  userSessionStorage.setItem('touch_enable', 'true');
//  console.log(userSessionStorage.getItem('touch_enable'));
//  window.removeEventListener('touchstart', onFirstTouch, false);
//}, false);

$(document).ready( function() {
    var messages = "{{ get_flashed_messages() }}";
    console.log(typeof messages);
    console.log(messages.length);
    if (messages !== '{{ get_flashed_messages() }}') {
        $('#msgModal').modal('show');
    };
});

//Get and display quiz question
$.ajax({url:"/question", dataType:"json"}).then( data => {
  emptyTenframe();
  if (data.question === "You haven't started a quiz!" || data.question === "End of Quiz!") {
    $('#quiz-question').append(`<h3>${data.question}</h3>`);
    $('#user-answer').hide();
    $('#submit-answer-button').hide();
    $('#show-tenframe').hide();
  } else {
    $('#quiz-question').append(`<h3>${data.question} = ?</h3>`);
    $('#get-next-btn').hide();
    const quizNumbers = splitOnOperator($.trim($('#quiz-question').text()).split(" = ")[0]);
    if (useTenframes(quizNumbers, data.question) === false) {
      $('#show-tenframe').hide();
    }
  }
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
    $('#adminCheck').prop("checked", false);
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
$('#user-answer').submit( evt => {
  evt.preventDefault();
  $('#show-tenframe').hide();
  const url = $(evt.target).attr('action');
  const question = $('h3').text().slice(0, -4);
  const userAnswer = $('#user-answer-text').val();
  $.ajax(url, {
    dataType: "json",
    data: {"question": question, "userAnswer": userAnswer},
    type: "POST",
  }).then( data => {
    if (data.answer === "Try again! Please enter a number.") {
      $('#quiz-answer').empty();
      $("#quiz-answer").append(data.answer);
      $('#user-answer-text').val("");
    } else if (data.answer === "CORRECT!") {
      $('#game-container').css("background-color", "mediumseagreen");
      $('#quiz-question').hide();
      $('#quiz-answer').empty();
      $("#quiz-answer").append(`<h3>${data.answer} ${question} = ${userAnswer}.</h3>`);
      $('#user-answer').hide();
      $('#submit-answer-button').hide();
      $('#user-answer-text').val("");
      $('#tenframes').prop('hidden', true);
      setTimeout(nextQuestion, 2000);
    } else if (data.answer === "Sorry! That's not the right answer.") {
      $('#game-container').css("background-color", "indianred");
      $('#quiz-question').hide();
      $('#quiz-answer').empty();
      $("#quiz-answer").append(`<h3>${data.answer} ${question} does not equal ${userAnswer}.</h3>`);
      $('#user-answer').hide();
      $('#submit-answer-button').hide();
      $('#user-answer-text').val("");
      $('#tenframes').prop('hidden', true);
      setTimeout(nextQuestion, 2000);
    }
  });
});

//Show and hide the ten frame for the current quiz question when button clicked
$('#show-tenframe').click( evt => {
  const quizQuestion = $('#quiz-question').text()
  const quizNumbers = splitOnOperator($.trim($('#quiz-question').text()).split(" = ")[0]);
  const tenframeBtn = $(evt.target);
  const btnText = tenframeBtn.text();
  if (btnText === 'Show Ten Frame') {
    $('#tenframes').prop('hidden', false);
    $('#show-tenframe').html('Hide Ten Frame');
    fillTenframe(quizNumbers, quizQuestion);
  } else if (btnText === 'Hide Ten Frame') {
    $('#tenframes').prop('hidden', true);
    $('#show-tenframe').html('Show Ten Frame');
  }
});

//Make profile image show profile pic modal
$('#profile-pic').click( evt => {
  $('#profileModal').modal('show');
});

//Makes remove pic button function
$('#remove-pic').click( evt => {
  location.href = '/removeimage';
});