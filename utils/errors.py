from wtforms.validators import ValidationError


class PositionalArgumentError(Exception):

    def __init__(self, funcname, posargs):
        self.message = f"{funcname}() missing {len(posargs)} required positional argument: {','.join(posargs)}"
        super().__init__(funcname, posargs)


    def __str__(self):
        return self.message



class InvalidValueError(Exception):

    def __init__(self, paramname, value, expectedvalue):
        self.message = f"invalid value: '{value}' of parameter: '{paramname}'! Expects: {','.join(expectedvalue)}"
        super().__init__(paramname, value, expectedvalue)


    def __str__(self):
        return self.message
    


class RequestArgumentError(Exception):

    def __init__(self, paramname, location):
        self.name = "Bad Request"
        self.message = f"Missing '{paramname}' from the {location} of the Request Body"
        super().__init__(paramname, location)


    def __str__(self):
        return self.message
    


class MemberNotFoundError(Exception):

    def __init__(self, memberparam, memberparamval, membertype = "Member"):
        self.message = f"{membertype} with {memberparam}: {memberparamval} doesn't exists!"
        super().__init__(memberparam, memberparamval, membertype)


    def __str__(self):
        return self.message
    


class UnexpectedArgumentError(Exception):

    def __init__(self, funcname, posargs):
        self.message = f"{funcname}() got {len(posargs)} unexpected keyword argument: {','.join(posargs)}"
        super().__init__(funcname, posargs)


    def __str__(self):
        return self.message



class DBNotFoundError(Exception):

    def __init__(self, dbname, dbtype):
        self.dbname = dbname
        self.dbtype = dbtype.title()
        self.message = f"{self.dbtype}: Database: {self.dbname} does not exists!!"
        super.__init__(self.dbname, self.dbtype)

    def __str__(self):
        return self.message
    


class FormDataViolationError(Exception):

    def __init__(self, field, entity = "entry", category = "error"):
        self.message = f"{field} is already associated with the other {entity}"
        super.__init__(field, entity, category)

    def __str__(self):
        return self.message
    


class FormValidationError(ValidationError):
    pass