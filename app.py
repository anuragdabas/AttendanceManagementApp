import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from admin.controller import admin
from staff.controller import staff
from admin.models import db, migrate
from admin.models import AdminModel, StaffModel
from admin.views import IndexView


basedir = os.path.abspath(os.path.dirname(__file__))
loginmanager = LoginManager()
csrf = CSRFProtect()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(30).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')



db.init_app(app)
migrate.init_app(app)
loginmanager.init_app(app)
csrf.init_app(app)


app.add_url_rule("/", view_func = IndexView.as_view("index"))

app.register_blueprint(blueprint=admin, url_prefix='/admin')
app.register_blueprint(blueprint=staff, url_prefix='/staff')

@loginmanager.user_loader
def load_user(user_id):
    admin = AdminModel.query.get(int(user_id))
    if admin:
        return admin
    staff = StaffModel.query.get(int(user_id))
    if staff:
        return staff
    return



if __name__ == "__main__":
    app.run(debug=True)