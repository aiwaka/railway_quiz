function check_answer() {
  const element_answers = document.getElementsByClassName('answertext');

  const element_correctanswer_box = document.getElementById('output_text');
  const element_correctness_text = document.getElementById('correctness');
  const element_submit_correctness = document.getElementById('submit_correctness');
  const element_next_button = document.getElementById('next_button');
  const element_correct_answers = document.getElementsByClassName('answer');

  let correctness_text = '不正解';
  if (element_answers[0].value === element_correct_answers[0].innerHTML) {
    correctness_text = '正解';
  }
  if (correctness_text === '正解') {
    element_correctness_text.classList.add('answer_correct');
  } else {
    element_correctness_text.classList.add('answer_incorrect');
  }
  element_correctness_text.innerHTML = correctness_text;
  element_submit_correctness.value = correctness_text;

  element_correctanswer_box.style.display = 'block';
  element_next_button.removeAttribute("disabled");
}

function display_answer() {
  const element_correctanswer_box = document.getElementById('output_text');
  const element_next_button = document.getElementById('next_button');
  element_correctanswer_box.style.display = 'block';
  element_next_button.removeAttribute("disabled");
}
