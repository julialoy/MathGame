
$.ajax({url:"/question", dataType:"json"}).then( data => {
  $('#quiz-question').append(`<h3>${data.question}</h3>`);
  $('#get-next-btn').hide();
  if (data.question === "You haven't started a quiz!" || data.question === "End of Quiz!") {
    $('#user-answer').hide();
  }
});

$('#register-form').submit( evt => {
  const username = $('#createUsername').val();
  const password = $('#createPassword').val();
  const confirmPassword = $('#confirmPassword').val();
  if (password !== confirmPassword) {
    alert("Those passwords do not match.");
    $('#createUsername').val("");
    $('#createPassword').val("");
    $('#confirmPassword').val("");
    evt.preventDefault();
  }
});

const nextQuestion = () => {
  $('#quiz-question').empty();
  $('#quiz-answer').empty();
  $('#user-answer').show();
  $.ajax({url:"/question", dataType:"json"}).then( data => {
    $("#quiz-question").append(`<h3>${data.question}</h3>`);
    $('#get-next-btn').hide();
    if (data.question === "You haven't started a quiz!") {
      $('#user-answer').hide();
    } else if (data.question === "End of Quiz!") {
      $('#user-answer').hide();
      $('#quiz-question').append(`<p>You answered ${data.correct} questions correctly!</p>`);
      $('#quiz-question').append(`<p>You answered ${data.wrong} questions incorrectly.</p>`);
    };
  });
  $('#user-answer-text').focus();
};

$('#user-answer').submit( evt => {
  evt.preventDefault();
  const url = $(evt.target).attr('action');
  const question = $('h3').text();
  const userAnswer = $('#user-answer-text').val();
  $.ajax(url, {
    dataType: "json",
    data: {"question": question, "userAnswer": userAnswer},
    type: "POST",
  }).then( data => {
    $("#quiz-answer").append(data.answer);
    $('#user-answer').hide();
    $('#user-answer-text').val("");
    //$('#get-next-btn').show().focus();
    setTimeout(nextQuestion, 2000);
  });
});

// Turn div with answer green or red when answer is right or wrong
// Div goes back to blue when it goes to next question

//$('#get-next-btn').on('click', function() {
//  $('#quiz-question').empty();
//  $('#quiz-answer').empty();
//  $('#user-answer').show();
//  $.ajax({url:"/question", dataType:"json"}).then((data) => {
//    $("#quiz-question").append(`<h3>${data.question}</h3>`);
//    $('#get-next-btn').hide();
//    if (data.question === "You haven't started a quiz!") {
//      $('#user-answer').hide();
//    } else if (data.question === "End of Quiz!") {
//      $('#user-answer').hide();
//      $('#quiz-question').append(`<p>You answered ${data.correct} questions correctly!</p>`);
//      $('#quiz-question').append(`<p>You answered ${data.wrong} questions incorrectly.</p>`);
//    };
//  });
//  $('#user-answer-text').focus();
//});