from enum import Enum
from dotenv import load_dotenv

load_dotenv()


LOGO = """
           __  __  _____ 
     /\   |  \/  |/ ____|
    /  \  | \  / | (___  
   / /\ \ | |\/| |\___ \ 
  / ____ \| |  | |____) |
 /_/    \_\_|  |_|_____/      
       """


class GenderEnum(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class DayEnum(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ShiftEnum(Enum):
    DAY = "day"
    NIGHT = "night"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    MORNING = "morning"