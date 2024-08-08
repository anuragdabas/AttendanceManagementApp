import os
from flask import Blueprint
from staff import views


PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

staff = Blueprint("staff", __name__, static_folder="static", template_folder="templates")

staff.add_url_rule("/", view_func=views.StaffIndexView.as_view("staffindex"))
staff.add_url_rule("/signin", view_func=views.StaffSignin.as_view("signin"))
staff.add_url_rule("/timelog/add", view_func=views.AddTimeLog.as_view("addtimelog"))