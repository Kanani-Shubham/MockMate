from flask import Flask, render_template, request, jsonify, redirect, url_for
import uuid
import json
import os
from dotenv import load_dotenv
from model import generate_questions, evaluate_answers

# Load environment variables from .env file
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ANSWERS_FILE = os.path.join(APP_DIR, "answers.json")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET", "dev-secret")


def read_answers():
    if not os.path.exists(ANSWERS_FILE):
        return {}
    with open(ANSWERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def write_answers(data):
    with open(ANSWERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/", methods=["GET"])
def index():
    return render_template("filldata.html")


@app.route("/start", methods=["POST"])
def start():
    """Start session: receive form, generate questions, save session, redirect to interview page"""
    data = request.form
    role = data.get("role", "").strip()
    position = data.get("position", "").strip()
    extra = data.get("extra", "").strip()
    try:
        num_q = int(data.get("num_questions", 5))
        if num_q <= 0:
            num_q = 5
    except:
        num_q = 5

    prompt_meta = {"role": role, "position": position, "extra": extra, "num_questions": num_q}
    try:
        questions = generate_questions(
            role=role, 
            position=position, 
            extra=extra, 
            num_questions=num_q
        )
    except Exception as e:
        return f"Error generating questions: {e}", 500

    # create session id and store
    session_id = str(uuid.uuid4())
    store = read_answers()
    store[session_id] = {
        "meta": prompt_meta,
        "questions": questions,
        "answers": [],
        "current_index": 0,
        "evaluation": None
    }
    write_answers(store)

    return redirect(url_for("interview", session_id=session_id))


@app.route("/interview/<session_id>", methods=["GET"])
def interview(session_id):
    store = read_answers()
    session = store.get(session_id)
    if not session:
        return "Session not found.", 404

    idx = session.get("current_index", 0)
    total = len(session.get("questions", []))
    question = session["questions"][idx] if idx < total else ""
    return render_template("interview.html",
                           session_id=session_id,
                           question=question,
                           index=idx + 1,
                           total=total)


@app.route("/answer/<session_id>", methods=["POST"])
def answer(session_id):
    """AJAX endpoint to receive an answer, store it, and return next question or final evaluation."""
    payload = request.get_json() or {}
    answer_text = payload.get("answer", "").strip()

    store = read_answers()
    session = store.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    idx = session.get("current_index", 0)
    questions = session.get("questions", [])
    total = len(questions)

    # Store answer paired with question
    q_text = questions[idx] if idx < total else ""
    session["answers"].append({"question": q_text, "answer": answer_text})
    session["current_index"] = idx + 1

    if session["current_index"] < total:
        # Save and return next question
        write_answers(store)
        next_q = questions[session["current_index"]]
        return jsonify({
            "next_question": next_q,
            "index": session["current_index"] + 1,
            "total": total,
            "done": False
        })
    else:
        # All questions answered — call evaluation
        try:
            evaluation = evaluate_answers(
                session["meta"], 
                session["answers"]
            )
        except Exception as e:
            return jsonify({"error": f"Evaluation error: {e}"}), 500

        session["evaluation"] = evaluation
        write_answers(store)
        return jsonify({"done": True, "result_url": url_for("result", session_id=session_id)})


@app.route("/result/<session_id>", methods=["GET"])
def result(session_id):
    store = read_answers()
    session = store.get(session_id)
    if not session:
        return "Session not found.", 404
    if not session.get("evaluation"):
        return "Evaluation not ready.", 400

    return render_template("result.html",
                           meta=session["meta"],
                           answers=session["answers"],
                           evaluation=session["evaluation"])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    host = "0.0.0.0"
    print(f"Starting app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
