import os
import re
import logging
from datetime import datetime
from dateutil import parser as dateutilparser
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




class ModelUtil:

    @staticmethod
    def parse_model_fields(modeldata, fields):
        if isinstance(modeldata, (list,tuple)):
            fetched_data = []
            fetched_data_append = fetched_data.append
            for data in modeldata:
                row = data.__dict__
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
            if not fields:
                return row
            newrow = {}
            for field in fields:
                newrow[field] = row.get(field)
            return newrow
        
    
    @staticmethod
    def parse_kwargs(kwargs: dict, availkwargs: list|tuple, ignore_if_empty = False):
        data = {}
        for kwarg in availkwargs:
            keydata = kwargs.get(kwarg)
            if ignore_if_empty and not bool(keydata):
                continue
            data[kwarg] = keydata
        return data
    



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
        
        fieldyear = round((datetime.now() - dateutilparser(field.data, fuzzy = True)).total_seconds()/31536000,0)

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
        
        if not isinstance(field.data, FileStorage):
            message = "Invalid File"
            field.errors.append(message)
            self._success.append(False) 
            if error == "raise":
                raise FormValidationError(message)
            return False
        
        filename = secure_filename(field.data.filename)
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
        if field.data is None or secure_filename(field.data.filename) == '':
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
