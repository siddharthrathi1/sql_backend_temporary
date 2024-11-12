Clone the repo
Move into the root directory

Create and activate a virtual environment (optional but recommended):
Run the commands below in terminal-
-python -m venv venv

-source venv/bin/activate  # On Linux/Mac
-venv\Scripts\activate  # On Windows

-pip install -r requirements.txt
-uvicorn app:app --host 0.0.0.0 --port 8001 --reload
