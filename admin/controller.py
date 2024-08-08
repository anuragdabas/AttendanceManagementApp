import os
from flask import Blueprint
from admin import views


PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


admin = Blueprint("admin", __name__, template_folder=os.path.join(PATH, 'templates'), static_folder=os.path.join(PATH, 'static'))
admin.add_url_rule("/", view_func=views.AdminIndexView.as_view("adminindex"))
admin.add_url_rule("/signin", view_func=views.AdminSignin.as_view("signin"))
admin.add_url_rule("/employee", view_func=views.ViewStaff.as_view("viewstaff"))
admin.add_url_rule("/employee/add", view_func=views.AddStaff.as_view("addstaff"))
admin.add_url_rule("/employee/timelog/<int:id>", view_func=views.ViewTimeLogs.as_view("viewtimelogs"))
admin.add_url_rule("/schedule", view_func=views.ViewSchedule.as_view("viewschedule"))
admin.add_url_rule("/schedule/<int:id>", view_func=views.ViewSchedule.as_view("viewassignedschedule"))
admin.add_url_rule("/schedule/add", view_func=views.AddSchedule.as_view("addschedule"))