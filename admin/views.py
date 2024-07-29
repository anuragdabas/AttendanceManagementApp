from flask import render_template, redirect, flash, url_for, request
from flask.views import MethodView
from flask_login import login_required, logout_user, login_user, current_user
from utils.errors import FormDataViolationError
from admin.forms import SigninForm, StaffForm
from admin.models import AdminModel, StaffModel



class IndexView(MethodView):

    def get(self):
        return render_template("index.html")
    


class AdminSignin(MethodView):
    
    def get(self):
        form = SigninForm()
        return render_template("admin/signin.html",form = form)
    

    def post(self):
        try:
            form = SigninForm()
            if form.validate_on_submit():
                admin = AdminModel.query.filter_by(email = form.email.data, password = form.password.data).first()
                if not bool(admin):
                    flash(message="Incorrect UserEmail or Password", category="error")
                    return redirect(url_for("admin.signin"))
                else:
                    admin.is_admin = True
                    login_user(admin)
                    flash(message=f"Welcome {admin.name}", category="success")
                    return redirect(url_for("admin.viewstaff"))                   
            else:
                flash(message="Failed to Login Admin", category="warning")
                return render_template("admin/signin.html", form = form)
        except Exception as e:
            flash(message="Failed to Login", category=getattr(e, "category", "error"))
            return render_template("admin/signin.html", form = form)



    def delete(self):
        try:
            if current_user is not None:
                if current_user.is_admin:
                    logout_user()
                    flash(message=f"Successfully Logged Out {current_user.name}", category="success")
                    return redirect(url_for("index"))
                else:
                    flash(message=f"The Current User is not an admin", category="error")
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


    def get(self):
        self.form.reset_defaults()
        return render_template("admin/addstaff.html", form = self.form)

    
    def post(self):
        try:
            if self.form.validate_on_submit(request=request, errors="coerce"):
                member = StaffModel.fetch_staff(aadhar = self.form.aadhar.data)
                if bool(member):
                    self.form.aadhar.errors.append("Aadhar is already registered to the other staff member")
                    raise FormDataViolationError(field="aadhar", entity="staff member", category="warning")
                
                StaffModel.add_staff(**self.form.get_submitted_data())
                flash(message="Successfully Added Staff Member", category="success")
                return redirect(url_for("admin.viewstaff"))
            else:
                flash(message="Failed to Add Staff Member", category="warning")
                return render_template("admin/addstaff.html", form = self.form)
        except Exception as e:
            flash(message="Failed to Add Staff Member", category=getattr(e, "category", "error"))
            return render_template("admin/addstaff.html", form = self.form)
        
        


class ViewStaff(MethodView):


    def get(self):
        staff = StaffModel.list_staff(get_references = True)
        return render_template("admin/viewstaff.html", staff = staff)


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
                flash(message="Failed to Edit Staff Member", category="warning")
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
        form.frefill_form_for_update(staff)
        return render_template("staff/editstaff.html", form = form)
