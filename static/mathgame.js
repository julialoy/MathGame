
$.ajax({url:"/question", dataType:"json"}).then((data) => {
  $('#quiz-question').append(`<h3>${data.question}</h3>`);
  $('#get-next-btn').hide();
  if (data.question === "You haven't started a quiz!" || data.question === "End of Quiz!") {
    $('#user-answer').hide();
  }
});

$('#register-form').submit(function(evt) {
  console.log("Registration submitted");
  var url = $(this).attr('action');
  var username = $('#createUsername').val();
  console.log(username);
  var password = $('#createPassword').val();
  console.log(password);
  var confirmPassword = $('#confirmPassword').val();
  if (password !== confirmPassword) {
    alert("Those passwords do not match.");
    $('#createUsername').val("");
    $('#createPassword').val("");
    $('#confirmPassword').val("");
    evt.preventDefault();
  }
});

$('#user-answer').submit(function(evt) {
  evt.preventDefault();
  var url = $(this).attr("action");
  var question = $('h3').text();
  var userAnswer = $('#user-answer-text').val();
  $.ajax(url, {
    dataType: "json",
    data: {"question": question, "userAnswer": userAnswer},
    type: "POST",
  }).then((data) => {
    $("#quiz-answer").append(data.answer);
    $('#user-answer').hide();
    $('#user-answer-text').val("");
    $('#get-next-btn').show().focus();
  });
});

$('#get-next-btn').on('click', function() {
  $('#quiz-question').empty();
  $('#quiz-answer').empty();
  $('#user-answer').show();
  $.ajax({url:"/question", dataType:"json"}).then((data) => {
    $("#quiz-question").append(`<h3>${data.question}</h3>`);
    $('#get-next-btn').hide();
    if (data.question === "You haven't started a quiz!") {
      $('#user-answer').hide();
    } else if (data.question === "End of Quiz!") {
      $('#user-answer').hide();
      $('#quiz-question').append(`<p>You have answered ${data.correct} questions correctly!</p>`);
      $('#quiz-question').append(`<p>You have answered ${data.wrong} questions incorrectly.</p>`);
    };
  });
  $('#user-answer-text').focus();
});