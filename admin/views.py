from flask import render_template, redirect, flash, url_for, request, session
from flask.views import MethodView
from flask_login import login_required, logout_user, login_user, current_user
from utils.errors import FormDataViolationError
from utils.utilities import FlaskUtil
from admin.forms import SigninForm, StaffForm, ScheduleForm, TimeLogForm
from admin.models import AdminModel, StaffModel, TimeLogModel, ScheduleModel



class IndexView(MethodView):

    def get(self):
        if current_user.is_authenticated:
            if getattr(current_user,"isadmin",False):
                return redirect(url_for("admin.adminindex"))
            else:
                return redirect(url_for("staff.staffindex"))

        return render_template("index.html")



class AdminIndexView(MethodView):

    @FlaskUtil.manager_required(redirecturl="admin.signin")
    def get(self):
        return render_template("admin/aindex.html")
    


class AdminSignin(MethodView):
    
    def get(self):
        if current_user.is_authenticated:
            if getattr(current_user,"isadmin",False):
                return redirect(url_for("admin.signin"))
            else:
                flash("logout the current active employee session before signin to admin!")
                return redirect(url_for("staff.signin"))

        form = SigninForm()
        return render_template("admin/signin.html",form = form)
    

    def post(self):
        try:
            if request.form.get("_method") == "DELETE":
                return self.delete()
            
            form = SigninForm()
            if form.validate_on_submit():
                admin = AdminModel.query.filter_by(email = form.email.data, password = form.password.data).first()
                if not bool(admin):
                    flash(message="Incorrect UserEmail or Password", category="error")
                    return redirect(url_for("admin.signin"))
                else:
                    login_user(admin)
                    session["_user_type_model"] = "admin"
                    flash(message=f"Welcome {admin.name}", category="success")
                    return redirect(url_for("admin.adminindex"))                   
            else:
                flash(message="Failed to Login Admin", category="warning")
                return render_template("admin/signin.html", form = form)
        except Exception as e:
            flash(message="Failed to Login", category=getattr(e, "category", "error"))
            return render_template("admin/signin.html", form = form)



    def delete(self):
        try:
            if current_user is not None:
                if getattr(current_user,"is_admin", False):
                    logout_user()
                    session.pop("_user_type_model", None)
                    flash(message=f"Successfully Logged Out Admin", category="success")
                    return redirect(url_for("index"))
            else:
                flash(message=f"The Current User already logged out", category="warning")
                return redirect(url_for("index"))
        except Exception as e:
            flash(message="Failed to logout", category=getattr(e, "category", "error"))
            return render_template("admin/signin.html")



class AddStaff(MethodView):

    def __init__(self):
        super().__init__()
        self.form = StaffForm()


    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def get(self):
        self.form.reset_defaults()
        schedules = ScheduleModel.list_schedule()
        schedules = list(map(lambda x: (x['id'], f"{x['name']} ({x['shift_start']} - {x['shift_ends']})"), schedules))
        self.form.update_default(default_schedule = schedules, repeat_default_schedule = False, allow_empty_schedule_choice = True)
        return render_template("admin/addstaff.html", form = self.form)


    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def post(self):
        try:
            if self.form.validate_on_submit(request=request, errors="coerce"):
                member = StaffModel.fetch_staff(aadhar = self.form.aadhar.data, email = self.form.email.data, filter_type = "or", first_only = True)
                if bool(member):
                    if self.form.aadhar.data == member.aadhar:
                        self.form.aadhar.errors.append("Aadhar is already registered to the other staff member")
                        raise FormDataViolationError(field="aadhar", entity="staff member", category="warning")
                    else:
                        self.form.email.errors.append("Email is already registered to the other staff member")
                        raise FormDataViolationError(field="email", entity="staff member", category="warning")

                
                StaffModel.add_staff(**self.form.get_submitted_data())
                flash(message="Successfully Added Staff Member", category="success")
                return redirect(url_for("admin.viewstaff"))
            else:
                flash(message="Failed to Add Staff Member", category="warning")
                return render_template("admin/addstaff.html", form = self.form)
        except Exception as e:
            flash(message="Failed to Add Staff Member", category=getattr(e, "category", "error"))
            return render_template("admin/addstaff.html", form = self.form)




class AddSchedule(MethodView):

    def __init__(self):
        super().__init__()
        self.form = ScheduleForm()


    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def get(self):
        return render_template("admin/addschedule.html", form = self.form)

    
    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def post(self):
        try:
            if self.form.validate_on_submit():
                schedule = ScheduleModel.fetch_schedule(name = self.form.name.data)
                if bool(schedule):
                    self.form.name.errors.append("Schedule Name is already associated with the other schedule")
                    raise FormDataViolationError(field="name", entity="schedule name", category="warning")
                
                ScheduleModel.add_schedule(**self.form.data)
                flash(message="Successfully Added Schedule Entry", category="success")
                return redirect(url_for("admin.viewschedule"))
            else:
                flash(message="Failed to Add Schedule Entry", category="warning")
                return render_template("admin/addschedule.html", form = self.form)
        except Exception as e:
            flash(message="Failed to Add Schedule Entry", category=getattr(e, "category", "error"))
            return render_template("admin/addschedule.html", form = self.form)




class ViewStaff(MethodView):

    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def get(self):
        staff = StaffModel.list_staff(get_references = True)
        return render_template("admin/viewstaff.html", staff = staff)


    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def post(self):
        if request.form.get("_method") == "DELETE":
            return self.delete()
        elif request.form.get("_method") == "PUT":
            return self.put()
        else:
            form = StaffForm()
            if form.validate_on_update(request=request, errors="coerce"):
                member = StaffModel.fetch_staff(aadhar = form.aadhar.data, fields = ["id"])
                if bool(member) and member[0]['id']!=form.id.data:
                    form.aadhar.errors.append("Aadhar is already registered to the other staff member")
                    flash(message="Failed to Edit Staff Member", category="warning")
                    return render_template("admin/editstaff.html", form = form)
                
                StaffModel.update_staff(**form.get_updated_data())
                flash(message="Successfully Updated Staff Member", category="success")
                return redirect(url_for("admin.viewstaff"))
            else:
                flash(message="Failed to Edit Staff Member", category="warrning")
                return render_template("admin/editstaff.html", form = form)


    def delete(self):
        try:
            StaffModel.remove_staff(id = request.form["id"])
            flash("Successfully deleted staff member",category="success")
            return redirect(url_for("admin.viewstaff"))
        except:
            flash("Failed to delete staff member", category="error")
            return redirect(url_for("admin.viewstaff"))
            


    def put(self):
        staff = StaffModel.fetch_staff(id = request.form["id"])
        if staff is None:
            flash("Staff member doesn't exists", category="warning")
            return redirect(url_for("admin.viewstaff"))
        form = StaffForm()
        schedules = ScheduleModel.list_schedule()
        schedules = list(map(lambda x: (x['id'], f"{x['name']} ({x['shift_start']} - {x['shift_ends']})"), schedules))
        form.update_default(default_schedule = schedules, repeat_default_schedule = False, allow_empty_schedule_choice = True)
        form.frefill_form_for_update(staff)
        return render_template("admin/editstaff.html", form = form)




class ViewSchedule(MethodView):

    @login_required
    def get(self, id = None):
        if id:
            schedules = ScheduleModel.fetch_schedule(get_references = True, id = id)
        else:
            schedules = ScheduleModel.list_schedule(get_references = True)
        return render_template("admin/viewschedule.html", schedules = schedules)


    @FlaskUtil.manager_required(redirecturl="staff.signin")
    def post(self):
        if request.form.get("_method") == "DELETE":
            return self.delete()
        elif request.form.get("_method") == "PUT":
            return self.put()
        else:
            form = ScheduleForm()
            if form.validate_on_submit():
                schedule = ScheduleModel.fetch_schedule(name = form.name.data, fields = ["id"])
                if bool(schedule) and schedule[0]['id']!=form.id.data:
                    self.form.name.errors.append("Schedule Name is already associated with the other schedule")
                    flash(message="Failed to Edit Schedule Entry", category="warning")
                    return render_template("admin/editschedule.html", form = form)
                
                ScheduleModel.update_schedule(**form.data)
                flash(message="Successfully Updated Schedule Entry", category="success")
                return redirect(url_for("admin.viewschedule"))
            else:
                flash(message="Failed to Edit Schedule Entry", category="warning")
                return render_template("admin/editschedule.html", form = form)


    def delete(self):
        try:
            ScheduleModel.remove_schedule(id = request.form["id"])
            flash("Successfully deleted schedule entry",category="success")
            return redirect(url_for("admin.viewschedule"))
        except:
            flash("Failed to delete schedule entry", category="error")
            return redirect(url_for("admin.viewschedule"))
            


    def put(self):
        schedule = ScheduleModel.fetch_schedule(id = request.form["id"], get_references = True)
        if schedule is None:
            flash("Schedule entry doesn't exists", category="warning")
            return redirect(url_for("admin.viewschedule"))
        form = ScheduleForm()
        form.frefill_form_for_update(schedule)
        return render_template("admin/editschedule.html", form = form)




class ViewTimeLogs(MethodView):

    @FlaskUtil.manager_required(redirecturl="staff.staffindex")
    def get(self, id):
        timelogs = TimeLogModel.fetch_timelog(get_references = True, staff_id = id)
        return render_template("admin/viewtimelog.html", timelogs = timelogs, staff_id = id)


    @FlaskUtil.admin_required(redirecturl="staff.signin")
    def post(self, id):
        if request.form.get("_method") == "DELETE":
            return self.delete(id)
        elif request.form.get("_method") == "PUT":
            return self.put(id)
        else:
            form = TimeLogForm()
            if form.validate_on_submit(request = request):
                TimeLogModel.update_timelog(**form.data)
                flash(message="Successfully Updated Schedule Entry", category="success")
                return redirect(url_for("admin.viewtimelogs", id = id))
            else:
                flash(message="Failed to Edit Schedule Entry", category="warning")
                return render_template("admin/edittimelog.html", form = form)


    def delete(self, id):
        try:
            TimeLogModel.remove_timelog(id = request.form["id"])
            flash("Successfully deleted timelog entry",category="success")
            return redirect(url_for("admin.viewtimelogs", id = id))
        except:
            flash("Failed to delete schedule entry", category="error")
            return redirect(url_for("admin.viewtimelogs"))
            


    def put(self, id):
        timelog = TimeLogModel.fetch_timelog(id = request.form["id"])
        if timelog is None:
            flash("Schedule entry doesn't exists", category="warning")
            return redirect(url_for("admin.viewtimelogs", id = id))
        form = TimeLogForm()
        form.frefill_form_for_update(timelog)
        return render_template("admin/edittimelog.html", form = form, staff_id = id)

