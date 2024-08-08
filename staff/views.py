from flask import redirect, flash, render_template, url_for, request, session
from flask.views import MethodView
from flask_login import login_user, logout_user, login_required, current_user
from admin.forms import SigninForm, TimeLogForm
from admin.models import StaffModel, TimeLogModel, ScheduleModel
from dateutil import parser as dateutilparser
from datetime import datetime




class StaffIndexView(MethodView):


    @login_required
    def get(self):
        return render_template("staff/sindex.html")



class StaffSignin(MethodView):
    
    def get(self):
        if current_user.is_authenticated:
            if not getattr(current_user,"isadmin",False):
                return redirect(url_for("staff.staffindex"))
            else:
                flash("logout the current active employee session before signin to admin!")
                return redirect(url_for("staff.signin"))
        form = SigninForm()
        return render_template("staff/signin.html", form = form)
    

    def post(self):
        try:
            if request.form.get("_method") == "DELETE":
                return self.delete()
            
            form = SigninForm()
            if form.validate_on_submit():
                staff = StaffModel.query.filter_by(email = form.email.data, password = form.password.data).first()
                if not bool(staff):
                    flash(message="Incorrect UserEmail or Password", category="error")
                    return redirect(url_for("staff.signin"))
                else:    
                    login_user(staff)
                    session["_user_type_model"] = "staff"
                    flash(message=f"Welcome {staff.name}", category="success")
                    return redirect(url_for("staff.staffindex"))
            else:
                flash(message="Failed to Login Admin", category="warning")
                return render_template("staff/signin.html", form = form)
        except Exception as e:
            flash(message="Failed to Login", category=getattr(e, "category", "error"))
            return render_template("staff/signin.html", form = form)


    def delete(self):
        try:
            if current_user is not None:
                if not current_user.is_admin:
                    logout_user()
                    session.pop("_user_type_model", None)
                    flash(message=f"Successfully Logged Out Staff", category="success")
                    return redirect(url_for("index"))
            else:
                flash(message=f"The Current User already logged out", category="warning")
                return redirect(url_for("index"))
        except Exception as e:
            flash(message="Failed to logout", category=getattr(e, "category", "error"))
            return render_template("staff/signin.html")




class AddTimeLog(MethodView):

    @login_required
    def get(self):
        clock_in_time = None
        clock_out_time = None
        if getattr(current_user,"schedule_id", None):
            schedule = ScheduleModel.fetch_schedule(id = current_user.schedule_id, first_only = True)
            hoursdelta = (datetime.now() - datetime.combine(datetime.now(), schedule['shift_start'])).total_seconds() / 3600
            blockcondition = abs(hoursdelta) > 1
            form = TimeLogForm()
            if bool(getattr(current_user, "is_admin", None)):
                return redirect(url_for("admin.signin"))
            
            timelog = TimeLogModel.fetch_timelog(staff_id = current_user.id, current = True)
            if timelog and timelog['clock_in'].date() == datetime.now().date():
                clock_in_time = timelog['clock_in']
                clock_out_time = timelog['clock_out']
            
            if blockcondition and clock_in_time is None:
                return render_template("staff/blocktimelog.html")
        return render_template("staff/addtimelog.html", form = form, clock_in_time = clock_in_time, clock_out_time = clock_out_time, blockcondition = blockcondition)


    @login_required
    def post(self):
        try:
            form = TimeLogForm()
            if form.validate_on_submit(request = request):
                timelog = TimeLogModel.fetch_timelog(staff_id = current_user.id, current = True)
                if timelog and timelog['clock_in'].date() == datetime.now().date():
                    updated_form_data = {**form.data, "id": timelog['id']}
                    TimeLogModel.update_timelog(**updated_form_data)
                else:
                    TimeLogModel.add_timelog(**form.data, staff_id = current_user.id)
                flash(message="Successfully Added Timelog Entry", category="success")
                return redirect(url_for("staff.staffindex"))
            else:
                flash(message="Failed to Add Timelog Entry", category="warning")
                return render_template("admin/addtimelog.html", form = form)
        except Exception as e:
            flash(message="Failed to Add Timelog Entry", category=getattr(e, "category", "error"))
            return render_template("staff/addtimelog.html", form = form)
        