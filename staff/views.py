from flask import redirect, flash, render_template, url_for
from flask.views import MethodView
from flask_login import login_user, logout_user, login_required, current_user
from admin.forms import SigninForm
from admin.models import StaffModel




class StaffSignin(MethodView):
    
    def get(self):
        form = SigninForm()
        return render_template("staff/signin.html", form = form)
    

    def post(self):
        try:
            form = SigninForm()
            if form.validate_on_submit():
                staff = StaffModel.fetch_staff(email = form.email.data, password = form.password.data)
                if not bool(staff):
                    flash(message="Incorrect UserEmail or Password", category="error")
                    return redirect(url_for("staff.signin"))
                else:    
                    staff.is_admin = False
                    login_user(staff)
                    flash(message=f"Welcome {staff.name}", category="success")
                    return redirect(url_for("staff.index"))
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
                    flash(message=f"Successfully Logged Out {current_user.name}", category="success")
                    return redirect(url_for("index"))
                else:
                    flash(message=f"The Current User is not a staff", category="error")
                    return redirect(url_for("index"))
            else:
                flash(message=f"The Current User already logged out", category="warning")
                return redirect(url_for("index"))
        except Exception as e:
            flash(message="Failed to logout", category=getattr(e, "category", "error"))
            return render_template("staff/signin.html")
