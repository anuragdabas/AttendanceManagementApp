from sqlalchemy import or_ as sqlalchecmyor
from admin.models import AdminModel
from utils.errors import FormDataViolationError, PositionalArgumentError


class SuperUserArgs:

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password




class SuperUser:
    
    def __init__(self, args):
        self.args = args

    
    def validate_args(self):
        if all([self.args.name, self.args.email, self.args.password]):
            if len(self.args.email)>155:
                raise Exception("email length should be less than 155 characters")
        else:
            raise PositionalArgumentError("superuser" , ["name","email","password"])


    def create_superuser_via_args(self):
        admin = AdminModel.query.filter(sqlalchecmyor(AdminModel.name == self.args.name, AdminModel.email == self.args.email)).first()
        if bool(admin):
            raise FormDataViolationError("name/email","admin")
        AdminModel.add_admin(name = self.args.name, email = self.args.email, password = self.args.password)

    
    @classmethod
    def process_args(cls, name, email, password):
        args = SuperUserArgs(name, email, password)

        if not any([args.name, args.email, args.password]):
            return
        
        cls = cls(args)
        cls.validate_args()
        cls.create_superuser_via_args()