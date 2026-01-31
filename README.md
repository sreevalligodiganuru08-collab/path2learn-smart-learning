# Path2Learn – Smart Learning Platform 🚀

Path2Learn is a smart learning web application that helps students learn topics from their syllabus and attempt quizzes created by faculty.

## ✨ Features
- Student Signup & Login
- Faculty Login & Quiz Creation
- Upload syllabus (.txt) to extract topics
- Topic-wise quiz display
- Interactive student dashboard
- FastAPI backend + HTML/CSS frontend

## 🛠 Tech Stack
- Python (FastAPI)
- HTML, CSS, JavaScript
- SQLite (or file-based storage)
- GitHub for version control

## ⚙️ How to Run the Project

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
