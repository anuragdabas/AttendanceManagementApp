
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set FLASK_APP=app.py
flask db init
flask db migrate
flask db upgrade
flask superuser --name admin --email admin@roadcast.com --password admin12345
flask run