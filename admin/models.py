from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin
from datetime import datetime, UTC
from utils.utilities import BaseUtil, ModelUtil, Logger
from utils.errors import MemberNotFoundError



db = SQLAlchemy()
migrate = Migrate(db = db)
logger = Logger.getLogger(sub_name="admin: Model")


class AdminModel(db.Model, UserMixin):

    __tablename__ = "admin"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(155), nullable=False)
    gender = db.Column(db.String(6), nullable=False)
    password = db.Column(db.String(100), nullable = False)



class StaffModel(db.Model, UserMixin):
    
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.String(100), nullable=False, unique = True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(155), nullable=False)
    dob = db.Column(db.DateTime, nullable=False, default = datetime.now(UTC))
    gender = db.Column(db.String(6), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(100), nullable = False)
    address = db.Column(db.String(255), nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    city = db.Column(db.String(100), nullable = False)
    picture = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable = True)
    registration_date = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))
    aadhar = db.Column(db.String(15), nullable=False, unique = True)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))
    is_manager = db.Column(db.Boolean, nullable = False, default = False)
    schedule = db.relationship('ScheduleModel', backref='staff', lazy=True, cascade="all,delete" , passive_deletes=True)
    timelogs = db.relationship('OffDayModel', backref='staff', lazy=True, cascade="all,delete" , passive_deletes=True, uselist = True)


    @classmethod
    def add_staff(cls, **kwargs):
        try:
            
            logger.info("Attempting to add staff in TimeScale")
            requiredargs = ["name","registration_id","aadhar","password","dob","gender","email","mobile", "role", "address", "city", "pincode"]
            BaseUtil.perform_argument_check(data = kwargs,requiredargs = requiredargs, callback_name = "StaffModel.add_staff")

            kwargs["picture"] = FilesModel.add_file(file = kwargs.get("picture"), bucket = "images")
            kwargs["resume"] = FilesModel.add_file(file = kwargs.get("resume"), bucket = "documents")
            
            cols = cls.__table__.columns.keys()
            staff = cls(**ModelUtil.parse_kwargs(kwargs, cols))
            db.session.add(staff)
            db.session.commit()
            logger.info(f"Successfully added staff in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to add staff in TimeScale")
            raise e
        

    @classmethod
    def remove_staff(cls, **kwargs):
        try:
            logger.info("Attempting to remove staff in TimeScale")
            BaseUtil.perform_argument_check(data = kwargs, requiredargs = ["id","registration_id"], callback_name = "StaffModel.remove_student", default_behaviour="any")
            if "id" in kwargs:
                staffkey = "id"
                staff = cls.query.filter_by(id=kwargs["id"]).first()
            else:
                staffkey = "registration_id"
                staff = cls.query.filter_by(registration_id=kwargs["registration_id"]).first()

            if staff is None:
                raise MemberNotFoundError(memberparam = staffkey, memberparamval=kwargs[staffkey], membertype="Staff")
            
            db.session.delete(staff)
            db.session.commit()
            logger.info(f"Successfully deleted staff: {kwargs[staffkey]} in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete staff: {kwargs[staffkey]} in TimeScale")
            raise e


    @classmethod
    def update_staff(cls, **kwargs):
        try:
            logger.info("Attempting to update staff in TimeScale")

            BaseUtil.perform_argument_check(data = kwargs, requiredargs = ["id", "registration_id"], callback_name = "StaffModel.update_staff", default_behaviour="any")

            if "id" in kwargs:
                staffkey = "id"
                staff = cls.query.filter_by(id=kwargs.pop("id")).first()
            else:
                staffkey = "registration_id"
                staff = cls.query.filter_by(admission_no=kwargs.pop("registration_id")).first()

            if staff is None:
                raise MemberNotFoundError(memberparam = staffkey, memberparamval=kwargs[staffkey], membertype="Staff")
            
            if not bool(kwargs):
                logger.warning("No info to be updated in the student")
                return

            if bool(kwargs.pop("picture",None)):
                kwargs["picture"] = FilesModel.add_file(file = kwargs["picture"], bucket = "images")

            for param in kwargs:
                if hasattr(staff,param):
                    setattr(staff,param,kwargs[param])

            db.session.commit()

            logger.info("Successfully updated student in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to update student in TimeScale")
            raise e



    @staticmethod
    def fetch_staff(**kwargs):
        try:
            logger.info("Attempting to fetch staff in TimeScale")
            fields = kwargs.pop("fields", None)
            first_only = kwargs.pop("first_only", False)

            if not kwargs:
                return {}

            if first_only:
                staff = StaffModel.query.filter_by(**kwargs).first()
            else:
                staff = StaffModel.query.filter_by(**kwargs).all()
            logger.info("Successfully fetch staff in TimeScale")
            return ModelUtil.parse_model_fields(modeldata = staff, fields = fields)
    
        except Exception as e:
            logger.error("Failed to fetch staff in TimeScale")
            raise e




class ScheduleModel(db.Model):

    __tablename__ = "schedule"

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)
    shift_type = db.Column(db.String(10), nullable=False)
    shift_start = db.Column(db.DateTime, nullable = False)
    shift_ends = db.Column(db.DateTime, nullable = False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))



class OffDayModel(db.Model):
    
    __tablename__ = "offday"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    off_type = db.Column(db.String(15), nullable = False)
    is_half_day = db.Column(db.Boolean, nullable = False, default = False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    requested_at = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))
    approved_at = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))
    approver_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))
    



class TimeLogModel(db.Model):
    
    __tablename__ = "timelogs"
    
    id = db.Column(db.Integer, primary_key=True)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    picture = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable = True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.now(UTC))



class FilesModel(db.Model):

    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key = True)
    bucket_name = db.Column(db.String(100), nullable = False)
    file_path = db.Column(db.String(155), nullable = True)
    file_name = db.Column(db.String(155), nullable = False)
    file_uri = db.Column(db.String(1055), nullable = False)
    file_type = db.Column(db.String(25), nullable = False)
    expired_at = db.Column(db.DateTime,nullable = False)
    created_at = db.Column(db.DateTime,nullable = False, default = datetime.now(UTC))