const form = document.querySelector("#diagnosis-form");
const question = document.querySelector("#question");
const status = document.querySelector("#status");
const answer = document.querySelector("#answer");
const answerText = document.querySelector("#answer-text");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.textContent = "Thinking...";
  answer.hidden = true;
  try {
    const response = await fetch("/api/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question.value }),
    });
    if (!response.ok) throw new Error("The diagnosis request failed.");
    const data = await response.json();
    answerText.textContent = data.answer;
    answer.hidden = false;
    status.textContent = "";
  } catch (error) {
    status.textContent = error.message;
  }
});
