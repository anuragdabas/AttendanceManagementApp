import os
import re
import minio
import logging
from datetime import datetime
from dateutil import parser as dateutilparser
from functools import wraps
from flask import flash, url_for, redirect
from flask_login import current_user
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from utils.errors import PositionalArgumentError, UnexpectedArgumentError, InvalidValueError, FormValidationError




class Logger:
    
    def __init__(self, sub_name=""):
        self.name=os.getenv("APP_LOGGER_NAME", "AppLogger")
        self.level=os.getenv("APP_LOGGER_LEVEL", "error")
        self.view_logs = bool(int(os.getenv("APP_VIEW_LOGS", 0)))
        self.write_logs = bool(int(os.getenv("APP_WRITE_LOGS", 0)))
        self.log_path = os.getenv("APP_LOG_PATH", "logs/")
        self.sub_name = sub_name.strip()
        self.level=self._map_level()
        self.logger=logging.getLogger(self.name)
        self.logger.setLevel(self.level)
        
        if bool(self.sub_name):
            self.format = '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(sub_name)s: %(message)s'
            self.logger = logging.LoggerAdapter(self.logger, {"sub_name" : self.sub_name})
        else:
            self.format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s'

        self.formatter=logging.Formatter(self.format,datefmt='%Y-%m-%d %H:%M:%S')

        if self.view_logs:
            self.add_stream_handler()
        if self.write_logs:
            self.add_file_handler()




    def _map_level(self):
        levels={
        "info":logging.INFO,
        "debug":logging.DEBUG,
        "warning":logging.WARNING,
        "error":logging.ERROR,
        "critical":logging.CRITICAL
                }
        return levels[self.level.lower()]


    @classmethod
    def getLogger(cls,sub_name=""):
        logger=cls(sub_name)
        return logger.logger


    def add_stream_handler(self):
        sh=logging.StreamHandler()
        sh.setFormatter(self.formatter)
        sh.setLevel(self.level)
        
        if isinstance(self.logger,logging.LoggerAdapter):
            if not any([isinstance(handler,logging.StreamHandler) for handler in self.logger.logger.handlers]):
                self.logger.logger.addHandler(sh)
        else:
            if not any([isinstance(handler,logging.StreamHandler) for handler in self.logger.handlers]):
                self.logger.addHandler(sh)


    def add_file_handler(self):
        if not os.path.exists(os.path.join(os.getcwd(),self.log_path)):
            os.makedirs(self.log_path)
        
        logfile=f"{datetime.strftime(datetime.now(),'%Y-%h-%d %H%M%S')}.log"
        fh = logging.FileHandler(filename=os.path.join(self.log_path,logfile),mode="w",encoding='utf-8',delay=True)
        fh.setFormatter(self.formatter)
        fh.setLevel(self.level)
        
        if isinstance(self.logger,logging.LoggerAdapter):
          if not any([isinstance(handler,logging.FileHandler) for handler in self.logger.logger.handlers]):
              self.logger.logger.addHandler(fh)
        else:      
            if not any([isinstance(handler,logging.FileHandler) for handler in self.logger.handlers]):
                self.logger.addHandler(fh)


    def shutdown(self):
        if isinstance(self.logger,logging.LoggerAdapter):
            self.logger.logger.handlers.clear()
        else:
            self.logger.handlers.clear()
        logging.shutdown()






class MinioDB:

    def __init__(self):
        self.minioClient = self.get_minio_client()
        

    def get_minio_client(self):
        """Connects to MINIO and returns client."""

        # hardcoded to false https://github.com/minio/minio/issues/8161
        # secure = bool(str(os.getenv("MINIO_IS_SECURE")))

        minio_client = minio.Minio(endpoint=os.getenv("MINIO_URL").rsplit("/",1)[0],
                                access_key=os.getenv("MINIO_USER"),
                                secret_key=os.getenv("MINIO_PWD"),
                                secure=bool(int(os.getenv("MINIO_USE_SECURE",0))))
        return minio_client


    def create_bucket(self, bucket_name):
        """Creates bucket on MINIO.

        Default location given is eu-central-1.
        Locations available:
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'ca-central-1', 'eu-central-1', 'sa-east-1',
        'cn-north-1', 'ap-southeast-1', 'ap-southeast-2',
        'ap-northeast-1', 'ap-northeast-2'
        """
        self.minioClient.make_bucket(bucket_name, location='eu-central-1')


    def upload_file(self, bucket_name, object_name, file_path):
        """Uploads file from disk to MINIO."""
        self.minioClient.fput_object(bucket_name=bucket_name,
                                object_name=object_name,
                                file_path=file_path)


    def upload_object(self, bucket_name, object_name, data, length, content_type="application/octet-stream"):
        """Uploads data from memory to MINIO.

        Data must io.BytesIO object.
        """
        return self.minioClient.put_object(bucket_name=bucket_name,
                                object_name=object_name,
                                data=data,
                                length=length,
                                part_size = 10*1024*1024,
                                content_type= content_type)


    def delete_file(self, bucket_name, object_name):
        """Deletes file from MINIO."""
        self.minioClient.remove_object(bucket_name=bucket_name, object_name=object_name)



    def remove_bucket(self, bucket_name):
        """Removes bucket from MINIO."""
        self.minioClient.remove_bucket(bucket_name=bucket_name)



    def get_file_from_bucket(self, bucket_name, object_name, file_path):
        """Downloads object from MINIO and writes to disk."""
        try:
            self.minioClient.fget_object(bucket_name=bucket_name,
                                    object_name=object_name,
                                    file_path=file_path)
            return True
        except minio.error.NoSuchKey as e:
            return False


    def get_object_from_bucket(self, bucket_name, object_name):
        """Downloads object from MINIO."""
        try:
            object_from_minio = self.minioClient.get_object(bucket_name=bucket_name,
                                                        object_name=object_name)

            return object_from_minio
        except minio.error.NoSuchKey as e:

            return None
        
        finally:
            object_from_minio.close()
            object_from_minio.release_conn()
        
    
    def list_object_from_bucket(self, bucket_name, object_name, recursive = False):
        try:
            objects_from_minio = self.minioClient.list_objects(bucket_name= bucket_name, prefix= object_name, recursive= recursive)
            return objects_from_minio
        
        except Exception as e:
            return None


    def get_object_link(self, bucket_name, object_name, method = "HTTP"):
        """creates shareable public link of the object(valid till 7 days)"""
        object_link = self.minioClient.get_presigned_url(method = method, bucket_name=bucket_name, object_name= object_name)
        return object_link





class ModelUtil:

    @staticmethod
    def parse_model_fields(modeldata, fields, relationship_info: dict = {}):
        if bool(relationship_info):
            BaseUtil.perform_argument_check(data=relationship_info, requiredargs=["relationship"], callback_name="ModelUtil.parse_model_fields")

        if isinstance(modeldata, (list,tuple)):
            fetched_data = []
            fetched_data_append = fetched_data.append
            for data in modeldata:
                row = data.__dict__
                if bool(relationship_info):
                    rel = ModelUtil.parse_relationship(data, relationship_info['relationship'], relationship_info.get('fields', {}), relationship_info.get('renames',{}), relationship_info.get("value_only",False))
                    row.update(rel)
                
                if not fields:
                    fetched_data_append(row)
                else:
                    newrow = {}
                    for field in fields:
                        newrow[field] = row.get(field)
                    fetched_data_append(newrow)
            return fetched_data
        else:
            if modeldata is None:
                return
            
            row = modeldata.__dict__
            if bool(relationship_info):
                    rel = ModelUtil.parse_relationship(data, relationship_info['relationship'], relationship_info.get('fields', {}), relationship_info.get('renames',{}), relationship_info.get("value_only",False))
                    row.update(rel)
            
            if not fields:
                return row
            newrow = {}
            for field in fields:
                newrow[field] = row.get(field)
            return newrow



    @staticmethod
    def parse_relationship(row: object|dict, relationship: list|tuple, fields: dict = {} , renames: dict = {}, value_only: bool = False):
        if isinstance(row, dict):
            return {}
        
        allrelations = {}
        for relation in relationship:
            relationships = []
            rel = getattr(row, relation, None)
            renamekey = renames.get(relation, {})
            if rel:
                if isinstance(rel, (list,tuple)):
                    for r in rel:
                        newr = {}
                        r = r.__dict__
                        for field in fields:
                            if value_only:
                                relationships.append(r.get(field))
                            else:
                                aliasedkey = renamekey.get(field, field)
                                newr[aliasedkey] = r.get(field)
                                relationships.append(newr)
                else:
                    newrel = {}
                    rel = rel.__dict__
                    for field in fields:
                        if value_only:
                            relationships.append(rel.get(field))
                        else:
                            aliasedkey = renamekey.get(field, field)
                            newrel[aliasedkey] = rel.get(field)
                            relationships.append(newrel)
            allrelations[relation] = relationships
        return allrelations



    @staticmethod
    def parse_kwargs(kwargs: dict, availkwargs: list|tuple, ignore_if_empty = False):
        data = {}
        for kwarg in availkwargs:
            keydata = kwargs.get(kwarg)
            if ignore_if_empty and not bool(keydata):
                continue
            data[kwarg] = keydata
        return data
    
    
    @staticmethod
    def parse_join_fields(modeldata: list|tuple, aliases, fetchedkeys: dict = {}, renames: dict = {}, primaryalias: None|str = None):
        parsed_model_data = []
        parsed_model_data_append = parsed_model_data.append
        for joindata in modeldata:
            newdata = {}
            for idx,data in enumerate(joindata):
                alias = aliases[idx]
                renamedkey=renames.get(alias,{})
                if data is None:
                    if primaryalias and primaryalias == alias:
                        return parsed_model_data
                    else:
                        continue
                row = data.__dict__
                for key in row:
                    aliasedkey = renamedkey.get(key,key)
                    if bool(fetchedkeys.get(alias,{})):
                        if key in fetchedkeys[alias]:
                            newdata[aliasedkey] = row[key]
                    else:
                        newdata[aliasedkey] = row[key]
            
            parsed_model_data_append(newdata)
        
        return parsed_model_data
    




class BaseUtil:
    
    
    @staticmethod
    def perform_argument_check(data, requiredargs, callback_name, error = 'raise', default_behaviour = "all"):
        BaseUtil.perform_value_check(paramvalue = default_behaviour, expectedvalue=["all","any"], param_name="default_behaviour", error=error)
        currargs = [args for args in requiredargs if data.get(args) is not None]
        if default_behaviour == "all":
            if len(currargs) == len(requiredargs):
                return True
            else:
                if error=="raise":
                    missingargs = [args for args in requiredargs if args not in currargs]
                    raise PositionalArgumentError(funcname = callback_name, posargs = missingargs)
                return False
        else:
            if bool(currargs):
                return True
            else:
                if error=="raise":
                    raise PositionalArgumentError(funcname = callback_name, posargs = requiredargs)
                return False


    @staticmethod
    def perform_value_check(paramvalue, expectedvalue, param_name, error="raise"):
        if isinstance(expectedvalue,(list,tuple,set)):
            checkcond = paramvalue in expectedvalue
        else:
            checkcond = (paramvalue == expectedvalue)
        if not checkcond and error == "raise":
            raise InvalidValueError(paramname = param_name, value = paramvalue, expectedvalue = expectedvalue)
        return checkcond
    



class FormUtil:

    def __init__(self):
        self._success = []


    def length(self, field, min, max, message = "", error = "raise"):
        
        if not message:
            message = f"Field must be between {min} and {max} characters long."
        
        if not min<=len(str(field.data))<=max:
            field.errors.append(message)
            if error == "raise":
                raise FormValidationError(message)
            self._success.append(False)                                                          
            return False
        
        self._success.append(True)
        return True


    def dateyear(self, field, minyear, maxyear, message = "", error = "raise"):
        fielddata = dateutilparser.parse(str(field.data), fuzzy = True) if isinstance(field.data, (str,int)) else field.data
        fieldyear = round((datetime.now().date() - fielddata).total_seconds()/31536000,0)

        if minyear and maxyear and not minyear<=fieldyear<=maxyear:
            if not message:
                message = f"Date Year must be lies between {minyear} and {maxyear}."
            field.errors.append(message)
            if error == "raise":
                raise FormValidationError(message)
            self._success.append(False)                                                          
            return False
        elif minyear and not minyear<fieldyear:
            if not message:
                message = f"Date Year must be atleast than {minyear}."
            field.errors.append(message)
            if error == "raise":
                raise FormValidationError(message)
            self._success.append(False)                                                          
            return False
        elif maxyear and not maxyear>fieldyear:
            if not message:
                message = f"Date Year must be smaller than {maxyear}."
            field.errors.append(message)
            if error == "raise":
                raise FormValidationError(message)
            self._success.append(False)                                                          
            return False
        
        self._success.append(True)
        return True
        

    def regexp(self, field, regex, flags = 0, message = "", error = "raise"):

        regex = re.compile(regex, flags)
        match = regex.match(str(field.data) or "")
        if match or not bool(field.data):
            self._success.append(True)
            return True

        if not message:
            message = "Invalid Input"

        field.errors.append(message)
        if error == "raise":
            raise FormValidationError(message)
        
        self._success.append(False)
        return False
    

    def filenum(self, field, filenum = 1, message = "", error = "raise"):
        if not message:
            if filenum == 1:
                message = "Multiple files not allowed. Select a single file"
            else:
                message = f"Multiple files more than {filenum} not allowed"

        if len(field.data) > filenum:
            field.errors.append(message)
            self._success.append(False)
            if error=="raise":
                raise FormValidationError(message)
            return False
        
        self._success.append(True)
        return True
    

    def fileext(self, field, exts, filereq = False, message = "", error = "raise"):
        
        filename = secure_filename(getattr(field.data, "filename", ""))
        if field.data is None or filename == "":
            if filereq:
                message = "File Required. Pls upload a file"
                field.errors.append(message)
                self._success.append(False)
                if error == "raise":
                    raise FormValidationError(message)
                return False
            self._success.append(True) 
            return True


        if not isinstance(field.data, FileStorage):
            message = "Invalid File"
            field.errors.append(message)
            self._success.append(False) 
            if error == "raise":
                raise FormValidationError(message)
            return False
        

        if not message:
            message = "File({name}) with extension {ext} not allowed. Pls upload the file with following extensions: ({exts})"
        
        fileext = filename.rsplit('.', 1)[1].lower()
        if fileext not in exts:
            message = message.format(name = filename, ext = fileext, exts = ", ".join(exts))
            field.errors.append(message)
            self._success.append(False) 
            if error == "raise":
                raise FormValidationError(message)
            return False
        
        self._success.append(True) 
        return True

    
    def filesize(self, field, size, filereq = False, message = "", error = "raise"):
        if field.data is None or secure_filename(getattr(field.data, "filename", "")) == '':
            if filereq:
                message = "File Required. Pls upload a file"
                field.errors.append(message)
                self._success.append(False) 
                if error == "raise":
                    raise FormValidationError(message)
                return False
            self._success.append(True) 
            return True

        allowedsize = size * 1000 * 1000
        if not message:
            message = f"File Size should not be more than {size} MB"
        
        if field.data.content_length:
            filesize = field.data.content_length
        else:
            field.data.seek(0, os.SEEK_END)
            filesize = field.data.tell()
            field.data.seek(0, os.SEEK_SET) 

        if filesize == 0:
            message = "File Size should be more than 0 bytes"
            field.errors.append(message)
            self._success.append(False) 
            if error == "raise":
                raise FormValidationError(message)
            return False
        
        if filesize > allowedsize:
            field.errors.append(message)
            self._success.append(False) 
            if error == "raise":
                raise FormValidationError(message)
            return False
        
        self._success.append(True) 
        return True
    

    @staticmethod
    def parse_form_choices(choicesdata, choicekey, choicevalues, valsep = " "):
        if isinstance(choicevalues,(list,tuple)): 
            return list(map(lambda x: (x[choicekey], valsep.join([x[val] for val in choicevalues])), choicesdata))
        return list(map(lambda x: (x[choicekey], x[choicevalues]), choicesdata))



class FlaskUtil:

    @staticmethod
    def admin_required(redirecturl, message='Required permissions are missing.', messagecategory="error"):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                print(f"Decorator applied to function: {f.__name__}")
                if not getattr(current_user, "is_admin", False):
                    flash(message, category=messagecategory)
                    return redirect(url_for(redirecturl))
                return f(*args, **kwargs)
            return decorated_function
        return decorator



    @staticmethod
    def manager_required(redirecturl, message = 'Required permissions are missing.', messagecategory = "error"):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                print(f"Decorator applied to function: {f.__name__}")
                if not getattr(current_user,"is_admin",False):
                    if not getattr(current_user,"is_manager",False):
                        flash(message, category = messagecategory)
                        return redirect(url_for(redirecturl))
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    


class ImageUtil:


    @staticmethod
    def add_required_padding(base64_string):
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        return base64_string