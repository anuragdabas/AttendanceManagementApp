import os
import click
from flask import Flask, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from admin.controller import admin
from staff.controller import staff
from admin.models import db, migrate
from admin.models import AdminModel, StaffModel
from admin.views import IndexView
from admin.admin import SuperUser



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
app.register_blueprint(blueprint=staff, url_prefix='/employee')

@loginmanager.user_loader
def load_user(user_id):
    if session.get("_user_type_model") == "admin":
        admin = db.session.get(AdminModel, int(user_id))
        admin.is_admin = True
        return admin
    elif session.get("_user_type_model") == "staff":
        staff = db.session.get(StaffModel, int(user_id))
        staff.is_admin = False
        return staff
    else:
        return


@app.cli.command('superuser')
@click.option('--name', prompt='SuperUser name', help='The name of the superuser.')
@click.option('--email', prompt='SuperUser email', help='The email of the superuser.')
@click.option('--password', prompt='SuperUser password', help='The password of the superuser.')
def superuser(name, email, password):
    try:
        SuperUser.process_args(name, email, password)
        click.echo('SuperUser created successfully!')
    except Exception as e:
        click.echo(f'Error: {e}')


if __name__ == "__main__":
    app.run(debug=True)