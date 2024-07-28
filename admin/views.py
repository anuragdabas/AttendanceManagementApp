import os
from flask import render_template, redirect, flash, url_for
from flask.views import MethodView
from flask_login import login_required, logout_user, login_user, current_user
from admin.forms import SigninForm
from admin.models import AdminModel



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