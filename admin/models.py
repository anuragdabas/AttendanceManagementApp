import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import desc as sqlalchemydesc, or_ as sqlalchemyor
from werkzeug.datastructures import FileStorage
from utils.utilities import BaseUtil, ModelUtil, Logger, MinioDB
from utils.errors import MemberNotFoundError



db = SQLAlchemy()
migrate = Migrate(db = db)
minio = MinioDB()
logger = Logger.getLogger(sub_name="admin: Model")


class AdminModel(db.Model, UserMixin):

    __tablename__ = "admin"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(155), nullable=False)
    password = db.Column(db.String(100), nullable = False)


    @classmethod
    def add_admin(cls, **kwargs):
        try:
            
            logger.info("Attempting to add admin in TimeScale")
            BaseUtil.perform_argument_check(data = kwargs,requiredargs = ["name","email","password"], callback_name = "AdminMoidel.add_admin")
            
            cols = cls.__table__.columns.keys()
            admin = cls(**ModelUtil.parse_kwargs(kwargs, cols))
            db.session.add(admin)
            db.session.commit()
            logger.info(f"Successfully added admin in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to add admin in TimeScale")
            raise e



class StaffModel(db.Model, UserMixin):
    
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.String(100), nullable=False, unique = True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(155), nullable=False)
    dob = db.Column(db.DateTime, nullable=False, default = datetime.utcnow())
    gender = db.Column(db.String(6), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    alternate_mobile = db.Column(db.String(15), nullable=True)
    password = db.Column(db.String(100), nullable = False)
    address = db.Column(db.String(255), nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    city = db.Column(db.String(100), nullable = False)
    picture = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable = True)
    registration_date = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())
    aadhar = db.Column(db.String(15), nullable=False, unique = True)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())
    is_manager = db.Column(db.Boolean, nullable = False, default = False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=True)
    timelogs = db.relationship('TimeLogModel', backref='staff', lazy=True, cascade="all,delete" , passive_deletes=True, uselist = True)


    @classmethod
    def add_staff(cls, **kwargs):
        try:
            
            logger.info("Attempting to add staff in TimeScale")
            requiredargs = ["name","registration_id","aadhar","password","dob","gender","email","mobile", "role", "address", "city", "pincode"]
            BaseUtil.perform_argument_check(data = kwargs,requiredargs = requiredargs, callback_name = "StaffModel.add_staff")
            kwargs["is_manager"] = (kwargs.pop("role", None)=="Manager")

            if bool(kwargs.get("picture")):
                kwargs["picture"] = FilesModel.add_file(file = kwargs.pop("picture"), bucket = "images")
            else:
                kwargs.pop("picture", None)

            if kwargs.get("schedule"):
                kwargs["schedule_id"] = int(kwargs.pop("schedule"))
            
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

            if bool(kwargs.get("picture")):
                kwargs["picture"] = FilesModel.add_file(file = kwargs["picture"], bucket = "images")
            else:
                kwargs.pop("picture",None)
                

            if kwargs.get("schedule"):
                kwargs["schedule_id"] = int(kwargs.pop("schedule"))


            if bool(kwargs.get("role")):
                kwargs["is_manager"] = (kwargs.pop("role")=="Manager")

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
            filter_cond = kwargs.pop("filter_type", 'and')

            if not kwargs:
                return {}

            if first_only:
                if filter_cond=="and":
                    staff = StaffModel.query.filter_by(**kwargs).first()
                else:
                    staff = StaffModel.query.filter(sqlalchemyor(*[getattr(StaffModel, k) == v for k, v in kwargs.items() if hasattr(StaffModel, k)])).first()
            else:
                if filter_cond=="and":
                    staff = StaffModel.query.filter_by(**kwargs).all()
                else:
                    staff = StaffModel.query.filter(sqlalchemyor(*[getattr(StaffModel, k) == v for k, v in kwargs.items() if hasattr(StaffModel, k)])).all()
            logger.info("Successfully fetch staff in TimeScale")
            return ModelUtil.parse_model_fields(modeldata = staff, fields = fields)
    
        except Exception as e:
            logger.error("Failed to fetch staff in TimeScale")
            raise e



    @staticmethod
    def list_staff(**kwargs):
            
            get_references = kwargs.pop("get_references", False)
            logger.info("Attempting to list staff in TimeScale")
            
            if get_references:
                
                staff = (db.session.query(StaffModel,FilesModel)
                                  .join(FilesModel, StaffModel.picture == FilesModel.id, isouter=True).all())
 
                logger.info("Successfully list staff in TimeScale")

                return ModelUtil.parse_join_fields(staff,
                                                    aliases = ["staff","picture"],
                                                    fetchedkeys = {"staff": ["id","name","registration_id","registration_date","gender","dob","email","mobile","alternate_mobile","aadhar","address","pincode","city","password","qualifications","about","subjects","role","updated_at","schedule_id","is_manager"],
                                                                    "picture": ["file_uri", "file_name", "bucket_name","file_path","file_type","expired_at","created_at","id"],
                                                                  },
                                                    renames = {"picture": {"file_uri":"picture", "file_name": "picture_name", "bucket_name": "picture_bucket_name", "file_path": "picture_file_path", "file_type":"picture_file_type", "expired_at": "picture_expired_at", "created_at": "picture_created_at", "id": "picture_id"}}
                                                    )
            else:
                staff = StaffModel.query.all()
                logger.info("Successfully list staff in TimeScale")
                return ModelUtil.parse_model_fields(modeldata = staff, fields = None)




class ScheduleModel(db.Model):

    __tablename__ = "schedule"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(55), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=True)
    shift_type = db.Column(db.String(10), nullable=False)
    shift_start = db.Column(db.Time, nullable = False)
    shift_ends = db.Column(db.Time, nullable = False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())
    dayoffs = db.relationship('WeekOffModel', backref='staff', lazy=True, cascade="all,delete" , passive_deletes=True, uselist = True)


    @classmethod
    def add_schedule(cls, **kwargs):
        try:
            
            logger.info("Attempting to add schedule in TimeScale")
            BaseUtil.perform_argument_check(data = kwargs,requiredargs = ["name","shift_type","shift_start","shift_ends","dayoffs"], callback_name = "ScheduleModel.add_schedule")
            
            cols = cls.__table__.columns.keys()
            schedule = cls(**ModelUtil.parse_kwargs(kwargs, cols))
            for dayoff in kwargs.pop("dayoffs"):
                doff = WeekOffModel(name = dayoff)
                schedule.dayoffs.append(doff)
            db.session.add(schedule)
            db.session.commit()
            logger.info(f"Successfully added schedule in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to add schedule in TimeScale")
            raise e



    @classmethod
    def update_schedule(cls, **kwargs):
        try:
            logger.info("Attempting to update schedule in TimeScale")

            BaseUtil.perform_argument_check(data = kwargs, requiredargs = ["id"], callback_name = "ScheduleModel.update_schedule")

            schedule = cls.query.filter_by(id=kwargs["id"]).first()

            if schedule is None:
                raise MemberNotFoundError(memberparam = "id", memberparamval=kwargs["id"], membertype="Schedule")
            
            del kwargs["id"]

            if not bool(kwargs):
                logger.warning("No info to be updated in the student")
                return


            if bool(kwargs.get("dayoffs")):
                for dayoff in schedule.dayoffs:
                    db.session.delete(dayoff)
            
                for dayoff in kwargs.pop("dayoffs"):
                    doff = WeekOffModel(name = dayoff)
                    schedule.dayoffs.append(doff)


            for param in kwargs:
                if hasattr(schedule,param):
                    setattr(schedule,param,kwargs[param])

            db.session.commit()

            logger.info("Successfully updated schedule in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to update schedule in TimeScale")
            raise e



    @staticmethod
    def fetch_schedule(**kwargs):
        try:
            logger.info("Attempting to fetch schedule in TimeScale")
            fields = kwargs.pop("fields", None)
            first_only = kwargs.pop("first_only", False)
            get_references = kwargs.pop("get_references", False)

            if not kwargs:
                return {}

            if first_only:
                schedule = ScheduleModel.query.filter_by(**kwargs).first()
                logger.info("Successfully fetch schedule in TimeScale")
                if get_references:
                    return ModelUtil.parse_model_fields(modeldata = schedule, fields = None, relationship_info={"relationship": ["dayoffs"], "fields": ["name"], "value_only": True})    
            else:
                schedule = ScheduleModel.query.filter_by(**kwargs).all()
                logger.info("Successfully fetch schedule in TimeScale")
                if get_references:
                    return ModelUtil.parse_model_fields(modeldata = schedule, fields = None, relationship_info={"relationship": ["dayoffs"], "fields": ["name"], "value_only": True})    
            
            logger.info("Successfully fetch schedule in TimeScale")
            return ModelUtil.parse_model_fields(modeldata = schedule, fields = fields)    

    
        except Exception as e:
            logger.error("Failed to fetch schedule in TimeScale")
            raise e



    @staticmethod
    def list_schedule(**kwargs):
            get_references = kwargs.pop("get_references", False)
            logger.info("Attempting to list schedule in TimeScale")
            

            if get_references:
                schedules = ScheduleModel.query.all()
                logger.info("Successfully list schedule in TimeScale")
                return ModelUtil.parse_model_fields(modeldata = schedules, fields = None, relationship_info={"relationship": ["dayoffs"], "fields": ["name"], "value_only": True})
            
            else:
                schedules = ScheduleModel.query.all()
                logger.info("Successfully list schedule in TimeScale")
                return ModelUtil.parse_model_fields(modeldata = schedules, fields = None)



    @classmethod
    def remove_schedule(cls, **kwargs):
        try:
            logger.info("Attempting to remove schedule in TimeScale")
            BaseUtil.perform_argument_check(data = kwargs, requiredargs = ["id"], callback_name = "ScheduleModel.remove_schedule")
            staff = cls.query.filter_by(id=kwargs["id"]).first()

            if staff is None:
                raise MemberNotFoundError(memberparam = "id", memberparamval=kwargs["id"], membertype="Staff")
            
            db.session.delete(staff)
            db.session.commit()
            logger.info(f"Successfully deleted staff: {kwargs['id']} in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete staff: {kwargs['id']} in TimeScale")
            raise e



class WeekOffModel(db.Model):

    __tablename__ = "weekoff"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())



class OffDayModel(db.Model):
    
    __tablename__ = "offday"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    off_type = db.Column(db.String(15), nullable = False)
    is_half_day = db.Column(db.Boolean, nullable = False, default = False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    requested_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())
    approved_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())
    approver_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())
    



class TimeLogModel(db.Model):
    
    __tablename__ = "timelogs"
    
    id = db.Column(db.Integer, primary_key=True)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    picture = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable = True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    updated_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow())


    @classmethod
    def add_timelog(cls, **kwargs):
        try:
            
            logger.info("Attempting to add timelog in TimeScale")
            BaseUtil.perform_argument_check(data = kwargs,requiredargs = ["staff_id"], callback_name = "TimelogModel.add_timelog")
            
            if bool(kwargs.get("picture")):
                kwargs["picture"] = FilesModel.add_file(file = kwargs["picture"], bucket = "images")
            else:
                kwargs.pop("picture",None)

            cols = cls.__table__.columns.keys()
            timelog = cls(**ModelUtil.parse_kwargs(kwargs, cols))
            db.session.add(timelog)
            db.session.commit()
            logger.info(f"Successfully added timelog in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to add timelog in TimeScale")
            raise e


    @staticmethod
    def fetch_timelog(**kwargs):
        try:
            logger.info("Attempting to fetch timelogs in TimeScale")
            fields = kwargs.pop("fields", None)
            current = kwargs.pop("current", False)
            get_references = kwargs.pop("get_references", False)
            
            if not kwargs:
                return {}
            
            if current:
                if get_references:
                    staff = (db.session.query(TimeLogModel,FilesModel)
                                  .join(FilesModel, TimeLogModel.picture == FilesModel.id, isouter=True)
                                  .filter(*[getattr(TimeLogModel, k) == v for k, v in kwargs.items() if hasattr(TimeLogModel, k)]).order_by(sqlalchemydesc(TimeLogModel.updated_at)).first())
                    return ModelUtil.parse_join_fields(staff,
                                    aliases = ["timelog","picture"],
                                    fetchedkeys = {"timelog": ["id","clock_in","clock_out","picture","updated_at","staff_id"],
                                                    "picture": ["file_uri", "file_name", "id"],
                                                    },
                                    renames = {"picture": {"file_uri":"picture", "file_name": "picture_name", "id": "picture_id"}}
                                    )
                staff = TimeLogModel.query.filter_by(**kwargs).order_by(sqlalchemydesc(TimeLogModel.updated_at)).first()  
            else:
                if get_references:
                    staff = (db.session.query(TimeLogModel,FilesModel)
                                  .join(FilesModel, TimeLogModel.picture == FilesModel.id, isouter=True)
                                  .filter(*[getattr(TimeLogModel, k) == v for k, v in kwargs.items() if hasattr(TimeLogModel, k)]).order_by(sqlalchemydesc(TimeLogModel.updated_at)).all())
                    return ModelUtil.parse_join_fields(staff,
                                    aliases = ["timelog","picture"],
                                    fetchedkeys = {"timelog": ["id","clock_in","clock_out","picture","updated_at","staff_id"],
                                                    "picture": ["file_uri", "file_name", "id"],
                                                    },
                                    renames = {"picture": {"file_uri":"picture", "file_name": "picture_name", "id": "picture_id"}}
                                    )
                staff = TimeLogModel.query.filter_by(**kwargs).all()
            logger.info("Successfully fetch timelogs in TimeScale")
            return ModelUtil.parse_model_fields(modeldata = staff, fields = fields)
    
        except Exception as e:
            logger.error("Failed to fetch timelogs in TimeScale")
            raise e




    @classmethod
    def update_timelog(cls, **kwargs):
        try:
            logger.info("Attempting to update timelog in TimeScale")

            BaseUtil.perform_argument_check(data = kwargs, requiredargs = ["id"], callback_name = "TimelogModel.update_timelog", default_behaviour="any")

            staff = cls.query.filter_by(id=kwargs["id"]).first()

            if staff is None:
                raise MemberNotFoundError(memberparam = "id", memberparamval=kwargs["id"], membertype="Timelog")
            
            del kwargs["id"]
            if not bool(kwargs):
                logger.warning("No info to be updated in the timelog")
                return

            if bool(kwargs.get("picture")):
                kwargs["picture"] = FilesModel.add_file(file = kwargs["picture"], bucket = "images")

            kwargs.pop("picture",None)
            
            for param in kwargs:
                if hasattr(staff,param):
                    setattr(staff,param,kwargs[param])

            db.session.commit()

            logger.info("Successfully updated timelog in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to update timelog in TimeScale")
            raise e
        

    @classmethod
    def remove_timelog(cls, **kwargs):
        try:
            logger.info("Attempting to remove timelog in TimeScale")
            BaseUtil.perform_argument_check(data = kwargs, requiredargs = ["id"], callback_name = "TimelogModel.remove_timelog")
            staff = cls.query.filter_by(id=kwargs["id"]).first()

            if staff is None:
                raise MemberNotFoundError(memberparam = "id", memberparamval=kwargs["id"], membertype="Timelog")
            
            db.session.delete(staff)
            db.session.commit()
            logger.info(f"Successfully deleted timelog: {kwargs['id']} in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete timelog: {kwargs['id']} in TimeScale")
            raise e




class FilesModel(db.Model):

    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key = True)
    bucket_name = db.Column(db.String(100), nullable = False)
    file_path = db.Column(db.String(155), nullable = True)
    file_name = db.Column(db.String(155), nullable = False)
    file_uri = db.Column(db.String(1055), nullable = False)
    file_type = db.Column(db.String(25), nullable = False)
    expired_at = db.Column(db.DateTime,nullable = False)
    created_at = db.Column(db.DateTime,nullable = False, default = datetime.utcnow())

    @staticmethod
    def add_file(file, bucket, file_path=""):
        try:
            if not (isinstance(file, FileStorage) and bool(file)):
                return
            
            logger.info("Attempting to files in TimeScale")

            file_name = secure_filename(file.filename)
            if file.content_length:
                filesize = file.content_length
            else:
                file.seek(0, os.SEEK_END)
                filesize = file.tell()
                file.seek(0, os.SEEK_SET) 
            
            if file_name == "" and filesize == 0:
                return None
            file_type = file_name.rsplit('.', 1)[1].lower()
            file_name =  datetime.strftime(datetime.utcnow(),"%Y%m%d%H%M%S%f") + "." + file_type
            minio_resp = minio.upload_object(bucket, os.path.join(file_path,file_name), file, -1)
            file_uri = minio.get_object_link(bucket,os.path.join(file_path,file_name),"GET")
            expired_at = datetime.utcnow() + timedelta(days = 7)
            filesobj = FilesModel(file_name = file_name, file_path = file_path, file_uri = file_uri, bucket_name = bucket, file_type = file_type, expired_at = expired_at)
            db.session.add(filesobj)
            
            logger.info("Successfully added files in Minio")

            db.session.commit()

            logger.info("Successfully added files info in TimeScale")
            return filesobj.id

        except Exception as e:
            db.session.rollback()
            logger.error("Unable to add user files in Minio/TimeScale")
            raise e



            
    @staticmethod
    def update_file(operation = 'refresh', **kwargs):
        try:
            logger.info(f"Attempting to update(mode = {operation}) user files in TimeScale")

            BaseUtil.perform_value_check(operation, ['add','remove','refresh'], 'operation')
            BaseUtil.perform_argument_check(kwargs, requiredargs=["id"], callback_name="FilesModel.update_image")
            
            files = FilesModel.query.filter_by(userid = kwargs["id"]).all()
            current_time = datetime.utcnow()
            check_time =  current_time + timedelta(days = 1)


            if bool(kwargs.get("userfiles")) and operation == 'add':
                return FilesModel.add_file(**kwargs)
            
            elif bool(kwargs.get("userdeletedfiles")) and operation == 'remove':
                return FilesModel.remove_file(uid = kwargs["uid"], deletedimagenames = kwargs["userdeletedimage"])
            

            logger.info(f"Attempting to refresh files(quantity: {len(files)}) in Minio and update the info in TimeScale")

            for file in files:
                if check_time > file.expired_at:
                    file.file_uri = minio.get_object_link(os.getenv("MINIO_IMAGES_BUCKET"),file.file_name)
                    file.expired_at = current_time + timedelta(days=7)

            db.session.commit()

            logger.info(f"Successfully refresh files(quantity: {len(files)}) in Minio and update the info in TimeScale")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update(mode = {operation}) user images in TimeScale")
            raise e
        
    
    @staticmethod
    def remove_file(id, deletedimagenames):
        try:
            logger.info("Attempting to remove files from TimeScale")

            files = FilesModel.query.filter(FilesModel.file_name.in_(tuple(deletedimagenames))).all()
            
            if not bool(files):
                logger.warning("Couldn't found the files associated with the user. Hence skipping!!")
                return
            
            logger.info("Attempting to remove files from Minio")

            for image in files:
                db.session.delete(image)
                minio.delete_file(os.getenv("MINIO_IMAGES_BUCKET"), files.file_name)

            logger.info("Successfully removed the files from Minio")

            db.session.commit()

            logger.info("Successfully removed files from TimeScale")

        except Exception as e:
            db.session.rollback()
            logger.error("Failed to remove files from Minio/TimeScale")
            raise e
