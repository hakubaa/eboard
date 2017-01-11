from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy.types import TypeDecorator

# SQLAlchemy - Custom Types
# http://docs.sqlalchemy.org/en/latest/core/custom_types.html

class BooleanString(TypeDecorator):
    '''
    Augmented Boolean type providing automatic conversion from string to 
    bool.
    '''
    impl = Boolean

    def process_literal_param(self, value, dialect):
        if isinstance(value, str):
            return value.upper() in ("T", "TRUE", "Y", "YES")
        return bool(value)

    process_bind_param = process_literal_param


class DateTimeString(TypeDecorator):
    '''
    Augmented DateTime type providing automatic conversion from string to 
    datetime.
    '''
    impl = DateTime    

    def __init__(self, *args, dtformat="%Y-%m-%d %H:%M", **kwargs):
        super().__init__(*args, **kwargs)
        self.dtformat = dtformat

    def process_literal_param(self, value, dialect):
        if isinstance(value, str):
            return datetime.strptime(value, self.dtformat)
        return value

    process_bind_param = process_literal_param