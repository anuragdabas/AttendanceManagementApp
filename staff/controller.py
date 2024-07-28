import os
from flask import Blueprint
from staff import views


PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

staff = Blueprint("staff", __name__, static_folder="static", template_folder="templates")

staff.add_url_rule("/", view_func=views.StaffSignin.as_view("signin"))