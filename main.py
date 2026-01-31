from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PyPDF2 import PdfReader
import shutil, os, re, uuid

app = FastAPI(title="Path2Learn")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= IN-MEMORY DATABASE =================
users_db = {}     # { username: password }
files_db = {}     # { username: {syllabus: path, notes: path} }
quiz_db = {}      # { topic: [ {id, question, options, correct} ] }

# ================= TOPIC EXTRACTION =================
def extract_topics_from_syllabus(file_path):
    topics = []
    ext = file_path.split('.')[-1].lower()

    try:
        if ext == "pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + " "
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            return [], "unsupported"

        raw_parts = text.split(",")

        for part in raw_parts:
            clean = part.strip()
            clean = re.sub(r"(unit|chapter)\s*\d+[:\-]?", "", clean, flags=re.I)
            clean = re.sub(r"[^A-Za-z0-9 ()\-]", "", clean)
            if 3 <= len(clean) <= 60:
                topics.append(clean)

    except Exception as e:
        print("Extraction failed:", e)
        return [], "error"

    if not topics:
        return [], "empty"

    return list(dict.fromkeys(topics))[:25], "ok"

# ================= ROUTES =================

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/login", status_code=303)

# ---------- SIGNUP ----------
@app.get("/signup", response_class=HTMLResponse)
def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "message": ""})

@app.post("/signup", response_class=HTMLResponse)
def signup_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "message": "❌ Username already exists"
        })
    users_db[username] = password
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "✅ Account created successfully. Please login."
    })

# ---------- LOGIN ----------
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "message": ""})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if users_db.get(username) == password:
        return RedirectResponse(url=f"/dashboard?username={username}", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "❌ Invalid username or password"
    })

# ---------- FACULTY LOGIN ----------
@app.get("/faculty", response_class=HTMLResponse)
def faculty_login(request: Request):
    return templates.TemplateResponse("faculty_login.html", {
        "request": request,
        "error": ""
    })

@app.post("/faculty-login", response_class=HTMLResponse)
def faculty_login_post(request: Request, faculty_id: str = Form(...), pin: str = Form(...)):
    if faculty_id == "faculty" and pin == "1234":
        return RedirectResponse(url="/faculty-dashboard", status_code=303)

    return templates.TemplateResponse("faculty_login.html", {
        "request": request,
        "error": "❌ Invalid Faculty Credentials"
    })

# ---------- FACULTY DASHBOARD ----------
@app.get("/faculty-dashboard", response_class=HTMLResponse)
def faculty_dashboard(request: Request):
    return templates.TemplateResponse("faculty_dashboard.html", {
        "request": request
    })

@app.post("/add-quiz")
def add_quiz(
    topic: str = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...)
):
    quiz = {
        "id": str(uuid.uuid4()),
        "question": question,
        "options": {
            "A": option_a,
            "B": option_b,
            "C": option_c,
            "D": option_d
        },
        "correct": correct_option
    }

    quiz_db.setdefault(topic.lower().strip(), []).append(quiz)
    return RedirectResponse(url="/faculty-dashboard", status_code=303)

# ---------- DASHBOARD ----------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, username: str):
    record = files_db.get(username)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "syllabus_file": record["syllabus"] if record else None,
        "notes_file": record["notes"] if record else None
    })

# ---------- UPLOAD ----------
@app.post("/upload", response_class=HTMLResponse)
async def upload(
    request: Request,
    username: str = Form(...),
    syllabus: UploadFile = File(...),
    notes: UploadFile = File(...)
):
    syllabus_ext = syllabus.filename.split('.')[-1]
    notes_ext = notes.filename.split('.')[-1]

    syllabus_path = f"{UPLOAD_FOLDER}/{username}_syllabus.{syllabus_ext}"
    notes_path = f"{UPLOAD_FOLDER}/{username}_notes.{notes_ext}"

    with open(syllabus_path, "wb") as f:
        shutil.copyfileobj(syllabus.file, f)
    with open(notes_path, "wb") as f:
        shutil.copyfileobj(notes.file, f)

    files_db[username] = {"syllabus": syllabus_path, "notes": notes_path}

    topics, status = extract_topics_from_syllabus(syllabus_path)

    if status == "unsupported":
        topics = ["⚠ Unsupported syllabus file"]
    elif status == "error":
        topics = ["⚠ Error extracting topics"]
    elif status == "empty":
        topics = ["⚠ No comma-separated topics found"]

    return templates.TemplateResponse("study_plan.html", {
        "request": request,
        "username": username,
        "topics": topics,
        "syllabus_file": syllabus_path,
        "notes_file": notes_path
    })

# ---------- QUIZ ----------
@app.get("/quiz", response_class=HTMLResponse)
def quiz(request: Request, topic: str):
    questions = quiz_db.get(topic.lower().strip(), [])
    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "topic": topic,
        "questions": questions
    })

@app.post("/submit-quiz", response_class=HTMLResponse)
async def submit_quiz(request: Request):
    form = await request.form()
    topic = form.get("topic")

    questions = quiz_db.get(topic.lower().strip(), [])
    score = 0

    for q in questions:
        user_ans = form.get(q["id"])
        if user_ans == q["correct"]:
            score += 1

    return templates.TemplateResponse("quiz_result.html", {
    "request": request,
    "topic": topic,
    "score": score,
    "total": len(questions),
    "username": form.get("username")  # pass username
})

# ---------- PREVIEW ----------
@app.get("/preview/{username}/{filetype}")
def preview(username: str, filetype: str):
    record = files_db.get(username)
    if not record:
        return HTMLResponse("File not found")

    path = record.get(filetype)
    if not path or not os.path.exists(path):
        return HTMLResponse("File missing")

    ext = path.split('.')[-1].lower()

    if ext in ["jpg", "jpeg", "png"]:
        return FileResponse(path)
    elif ext == "pdf":
        return FileResponse(path, media_type="application/pdf")
    elif ext == "txt":
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(f"<pre>{content}</pre>")
    else:
        return HTMLResponse("Unsupported file type")
