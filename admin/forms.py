from uuid import uuid4
from string import ascii_lowercase
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, IntegerField, TextAreaField, StringField, SelectField, DateField, TelField, FileField
from wtforms.validators import DataRequired, Length, Email, InputRequired, Optional, ValidationError
from wtforms.widgets import HiddenInput
from werkzeug.datastructures import ImmutableMultiDict
from datetime import datetime
from random import choices
from utils.utilities import FormUtil
from utils.consts import GenderEnum



class SigninForm(FlaskForm):
    email = EmailField(label="email",validators=[DataRequired(), Email(message="Enter a valid Email"), Length(max = 155, message="Email Do not exceed Till 155 Characters")], name="email")
    password = PasswordField(label="password", validators=[DataRequired()], name="password")
    submit = SubmitField(label="submit")



class StaffForm(FlaskForm):
    id = IntegerField(label="staff id", validators=[Optional()], name="id", render_kw={'disabled':'disabled'} , widget=HiddenInput())
    name = StringField(label="name", validators=[InputRequired(), Length(min=3, max = 100, message= "Name must be 3 Character Long and Do not exceed Till 100 Characters")], name="name")
    registration_id = StringField(label="registration id", validators=[DataRequired()], name="registration_id", default=f"STF-{uuid4().hex}", render_kw={'disabled':'disabled'})
    registration_date = DateField(label="registration date", validators=[DataRequired()], default=(datetime.now()).date(), name="registrationdate", render_kw={'disabled':'disabled'}) 
    gender = SelectField(label="gender", validators=[InputRequired()], choices=list(map(lambda x:(x,x), GenderEnum._value2member_map_.keys())), name="gender")
    dob = DateField(label="dob", validators=[InputRequired()], name="dob")
    email = EmailField(label="email",validators=[DataRequired(), Email(message="Enter a valid Email"), Length(max = 155, message="Email Do not exceed Till 155 Characters")], name="email")
    mobile = TelField(label="mobile", validators=[InputRequired()], name="mobile")
    alternate_mobile = TelField(label="alternate mobile", name="alternatemobile")
    aadhar = StringField(label="aadhar", validators=[InputRequired()], name="aadhar")
    address = TextAreaField(label="address", validators=[DataRequired(), Length(min=0, max=255, message="Length shouldn't be greater than 255 Characters")], name="address")
    pincode = IntegerField(label="pincode",validators=[InputRequired()], name="pincode")
    city = StringField(label="city", validators = [Length( min=0, max=100, message="Length shouldn't be greater than 100 Characters")] ,name="city")
    password = StringField(label="password",validators=[DataRequired()], default=''.join(choices(ascii_lowercase, k=10)), name="password", render_kw={'disabled':'disabled'})
    picture = FileField(label="picture", name="picture")
    submit = SubmitField(label="submit")


    def validate_after_submit(self, errors = "coerce"):
        try:
            success = True
            formutil = FormUtil()
            formutil.regexp(field=self.mobile, regex=r"^(\+\d{1,2}\s)?\d{10}$", message="Enter a valid mobile number", error=errors)
            formutil.regexp(field=self.alternate_mobile, regex=r"^(\+\d{1,2}\s)?\d{10}$", message="Enter a valid alternate mobile number", error=errors)
            formutil.regexp(field=self.aadhar, regex=r"^\d{12}$", message="Enter a valid aadhar number", error=errors)
            formutil.regexp(field=self.pincode, regex=r"^\d{6}$",message="Enter a valid pincode", error=errors)
            formutil.fileext(field=self.picture, exts=['jpg','jpeg','png','webp'], error=errors)
            formutil.filesize(field=self.picture, size=2, error=errors)
            formutil.dateyear(field=self.dob, minyear=20, maxyear= 90, message="Age should be between 20 and 90")
            success = all(formutil._success)
        except ValidationError as ve:
            success = False

        finally:
            return success
        
 
    def validate_on_submit(self, request, extra_validators=None, errors = "coerce"):
        formdata = ImmutableMultiDict({**request.form, **request.files})
        self.process(formdata=formdata)
        return super().validate_on_submit(extra_validators) and self.validate_after_submit(errors=errors)
