/* EduGenie frontend logic - talks to the FastAPI endpoints. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);

// ---------- tiny helpers ----------
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(s) {
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*\w])\*([^*\s][^*]*?)\*(?!\*)/g, "$1<em>$2</em>");
  return s;
}

/* Minimal, safe Markdown renderer (headings, bold/italic, code, nested lists). */
function renderMarkdown(md) {
  const lines = md.replace(/\r/g, "").split("\n");
  let html = "";
  let para = [];
  const stack = [];

  const flushPara = () => {
    if (para.length) { html += "<p>" + inline(para.join(" ")) + "</p>"; para = []; }
  };
  const closeLists = (toIndent) => {
    while (stack.length && stack[stack.length - 1].indent > toIndent) {
      html += "</li></" + stack.pop().tag + ">";
    }
  };

  for (const raw of lines) {
    const line = raw.replace(/\t/g, "    ");
    if (!line.trim()) { flushPara(); continue; }

    if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
      flushPara(); closeLists(-1); html += "<hr>"; continue;
    }
    const h = line.match(/^\s*(#{1,4})\s+(.*)$/);
    if (h) {
      flushPara(); closeLists(-1);
      const level = Math.min(h[1].length + 2, 5);
      html += `<h${level}>${inline(h[2])}</h${level}>`;
      continue;
    }
    const li = line.match(/^(\s*)([*\-+]|\d+\.)\s+(.*)$/);
    if (li) {
      flushPara();
      const indent = li[1].length;
      const tag = /\d/.test(li[2]) ? "ol" : "ul";
      closeLists(indent);
      const top = stack[stack.length - 1];
      if (top && top.indent === indent && top.tag === tag) {
        html += "</li><li>" + inline(li[3]);
      } else {
        if (top && top.indent === indent) { html += "</li></" + stack.pop().tag + ">"; }
        html += `<${tag}><li>` + inline(li[3]);
        stack.push({ indent, tag });
      }
      continue;
    }
    if (stack.length && /^\s+/.test(line)) { html += " " + inline(line.trim()); continue; }
    flushPara(); closeLists(-1);
    para.push(line.trim());
  }
  flushPara(); closeLists(-1);
  return html;
}

async function api(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch (e) {
    throw new Error("Cannot reach the EduGenie server. Is uvicorn still running?");
  }
  let data = {};
  try { data = await res.json(); } catch (_) { /* non-JSON body */ }
  if (!res.ok) {
    const msg = typeof data.error === "string" ? data.error
      : typeof data.detail === "string" ? data.detail
      : "The request was not valid.";
    throw new Error(msg);
  }
  return data;
}

function postJSON(url, body) {
  return api(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function showLoading(box, message) {
  box.hidden = false;
  box.className = "output loading";
  box.textContent = message;
}

function showError(box, message) {
  box.hidden = false;
  box.className = "output error";
  box.textContent = message;
}

function showResult(box, title, content, { markdown = true } = {}) {
  box.hidden = false;
  box.className = "output";
  box.innerHTML = "";
  box.appendChild(el("h3", "result-title", title));
  const body = el("div", markdown ? "" : "plain");
  if (markdown) body.innerHTML = renderMarkdown(content); else body.textContent = content;
  box.appendChild(body);
}

/* Backend modules return strings starting with the warning sign on failure. */
function isBackendError(text) {
  return typeof text === "string" && text.trim().startsWith("\u26A0");
}

/* Wrap a form submit handler: disables the button and handles errors. */
function handleForm(formId, run) {
  const form = $(formId);
  const button = $("button[type='submit']", form);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const label = button.textContent;
    button.disabled = true;
    try {
      await run();
    } catch (err) {
      console.error(err);
    } finally {
      button.disabled = false;
      button.textContent = label;
    }
  });
}

// ---------- tabs ----------
function setupTabs() {
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => {
        const active = t === tab;
        t.classList.toggle("is-active", active);
        t.setAttribute("aria-selected", String(active));
      });
      document.querySelectorAll(".panel").forEach((p) => {
        const show = p.id === "panel-" + tab.dataset.panel;
        p.hidden = !show;
        p.classList.toggle("is-active", show);
      });
    });
  });
}

// ---------- features ----------
function setupQA() {
  const box = $("#qaResult");
  handleForm("#qaForm", async () => {
    const question = $("#question").value.trim();
    showLoading(box, "Thinking...");
    try {
      const data = await api("/qa?question=" + encodeURIComponent(question));
      if (isBackendError(data.answer)) return showError(box, data.answer);
      showResult(box, "Answer", data.answer);
    } catch (e) { showError(box, e.message); }
  });
}

function setupExplain() {
  const box = $("#explainResult");
  handleForm("#explainForm", async () => {
    const topic = $("#topic").value.trim();
    showLoading(box, "Writing an explanation... (the first run loads the local model and can take a minute)");
    try {
      const data = await postJSON("/explain", { topic });
      if (isBackendError(data.explanation)) return showError(box, data.explanation);
      showResult(box, "Explanation: " + data.topic, data.explanation, { markdown: false });
    } catch (e) { showError(box, e.message); }
  });
}

function setupSummary() {
  const box = $("#summaryResult");
  handleForm("#summaryForm", async () => {
    const text = $("#summaryText").value.trim();
    showLoading(box, "Summarizing...");
    try {
      const data = await postJSON("/summarize", { text });
      if (isBackendError(data.summary)) return showError(box, data.summary);
      showResult(box, "Summary", data.summary);
    } catch (e) { showError(box, e.message); }
  });
}

function setupPath() {
  const box = $("#pathResult");
  handleForm("#pathForm", async () => {
    const topic = $("#pathTopic").value.trim();
    showLoading(box, "Building your learning path...");
    try {
      const data = await api("/learn/recommendations?topic=" + encodeURIComponent(topic));
      if (isBackendError(data.recommendation)) return showError(box, data.recommendation);
      showResult(box, `Learning path for "${data.topic}"`, data.recommendation);
    } catch (e) { showError(box, e.message); }
  });
}

function renderQuiz(box, quiz) {
  box.hidden = false;
  box.className = "output";
  box.innerHTML = "";
  box.appendChild(el("h3", "result-title", "Quiz"));

  let answered = 0;
  let correctCount = 0;
  const score = el("p", "score");
  score.hidden = true;

  quiz.forEach((q, i) => {
    const fs = el("fieldset", "q");
    fs.appendChild(el("legend", "", `Q${i + 1}. ${q.question}`));

    const labels = q.options.map((option) => {
      const label = el("label", "opt");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "quiz-q" + i;
      radio.value = option;
      label.appendChild(radio);
      label.appendChild(el("span", "", option));
      fs.appendChild(label);
      return label;
    });

    const feedback = el("p", "feedback");
    const btn = el("button", "check-btn", "Check answer");
    btn.type = "button";
    btn.addEventListener("click", () => {
      const chosen = fs.querySelector("input:checked");
      if (!chosen) {
        feedback.className = "feedback bad";
        feedback.textContent = "Choose an option first.";
        return;
      }
      const isCorrect = chosen.value === q.answer;
      labels.forEach((label) => {
        const input = $("input", label);
        input.disabled = true;
        if (input.value === q.answer) label.classList.add("correct");
        else if (input === chosen) label.classList.add("wrong");
      });
      feedback.className = "feedback " + (isCorrect ? "good" : "bad");
      feedback.textContent = isCorrect ? "Correct!" : "Incorrect. Correct answer: " + q.answer;
      btn.disabled = true;

      answered += 1;
      if (isCorrect) correctCount += 1;
      if (answered === quiz.length) {
        score.hidden = false;
        score.textContent = `Score: ${correctCount} / ${quiz.length}`;
      }
    });

    fs.appendChild(btn);
    fs.appendChild(feedback);
    box.appendChild(fs);
  });
  box.appendChild(score);
}

function setupQuiz() {
  const box = $("#quizResult");
  handleForm("#quizForm", async () => {
    const text = $("#quizText").value.trim();
    showLoading(box, "Writing your quiz...");
    try {
      const data = await postJSON("/quiz", { text });
      renderQuiz(box, data.quiz);
    } catch (e) { showError(box, e.message); }
  });
}

async function checkHealth() {
  const status = $("#status");
  try {
    const health = await api("/health");
    if (!health.gemini_key_configured) {
      status.classList.add("warn");
      status.textContent = "Gemini API key missing. Add it to .env and restart the server.";
    } else {
      status.textContent = "Connected. Model: " + health.gemini_model;
    }
  } catch (_) {
    status.textContent = "";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupQA();
  setupExplain();
  setupSummary();
  setupQuiz();
  setupPath();
  checkHealth();
});
