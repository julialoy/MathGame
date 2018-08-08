const fillTenframe = () => {
  const testNumOne = $.trim($('#quiz-question').text());
  const numOne = testNumOne.split(" + ");
  const tableOne = document.getElementById('tenframe-table-one');
  const tableTwo = document.getElementById('tenframe-table-two');
  const tableOneCells = tableOne.getElementsByTagName("td");
  const tableTwoCells = tableTwo.getElementsByTagName("td");

  for (i = 0; i < parseInt(numOne[0]); i++) {
    const redSphereOne = tableOneCells[i].firstChild;
    redSphereOne.setAttribute("style", "background-color:#17a2b8");
  }

  for (i = 0; i <parseInt(numOne[1]); i++) {
    const redSphereTwo = tableTwoCells[i].firstChild;
    redSphereTwo.setAttribute("style", "background-color:#17a2b8");
  }
  //Need to loop through table cells and change color of sphere
  //for (i = 0; i < tableCells.length; i++) {
  //
  //}
};

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

$.ajax({url:"/question", dataType:"json"}).then( data => {
  emptyTenframe();
  $('#quiz-question').append(`<h3>${data.question}</h3>`);
  $('#get-next-btn').hide();
  if (data.question === "You haven't started a quiz!" || data.question === "End of Quiz!") {
    $('#user-answer').hide();
    $('#show-tenframe').hide();
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
  $('#game-container').addClass('bg-primary');
  $('#quiz-question').empty();
  $('#quiz-answer').empty();
  $('#user-answer').show();
  emptyTenframe();
  $.ajax({url:"/question", dataType:"json"}).then( data => {
    $("#quiz-question").append(`<h3>${data.question}</h3>`);
    $('#get-next-btn').hide();
    if (data.question === "You haven't started a quiz!") {
      $('#user-answer').hide();
      $('#show-tenframe').hide();
    } else if (data.question === "End of Quiz!") {
      $('#user-answer').hide();
      $('#show-tenframe').hide();
      $('#quiz-question').append(`<p>You answered ${data.correct} questions correctly!</p>`);
      $('#quiz-question').append(`<p>You answered ${data.wrong} questions incorrectly.</p>`);
    } else {
      $('#show-tenframe').show();
    };
  });
  $('#user-answer-text').focus();
};

$('#user-answer').submit( evt => {
  evt.preventDefault();
  $('#show-tenframe').hide();
  const url = $(evt.target).attr('action');
  const question = $('h3').text();
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
      $('#game-container').removeClass("bg-primary");
      $('#game-container').css("background-color", "mediumseagreen");
      $('#quiz-answer').empty();
      $("#quiz-answer").append(data.answer);
      $('#user-answer').hide();
      $('#user-answer-text').val("");
      $('#tenframes').prop('hidden', true);
      setTimeout(nextQuestion, 2000);
    } else if (data.answer === "Sorry! That's not the right answer.") {
      $('#game-container').removeClass("bg-primary");
      $('#game-container').css("background-color", "indianred");
      $('#quiz-answer').empty();
      $("#quiz-answer").append(data.answer);
      $('#user-answer').hide();
      $('#user-answer-text').val("");
      $('#tenframes').prop('hidden', true);
      setTimeout(nextQuestion, 2000);
    }

  });
});

$('#show-tenframe').click( evt => {
  const tenframeBtn = $(evt.target);
  const btnText = tenframeBtn.text();
  if (btnText === 'Show Tenframe') {
    $('#tenframes').prop('hidden', false);
    $('#show-tenframe').html('Hide Tenframe');
    fillTenframe();
  } else if (btnText === 'Hide Tenframe') {
    $('#tenframes').prop('hidden', true);
    $('#show-tenframe').html('Show Tenframe');
  }
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