import json
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base


class JobModel(BaseModel):
    job_id: str
    task_name: str
    schedule_time: datetime
    created: datetime
    kwargs: dict


Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    job_id = Column(String, primary_key=True)
    task_name = Column(String, index=True)
    schedule_time = Column(DateTime)
    created = Column(DateTime)
    kwargs = Column(JSON)
    result = Column(Boolean, default=False)
    error_info = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)  # New column to mark archived jobs

    # Convert kwargs to and from JSON automatically
    @property
    def kwargs_dict(self):
        return json.loads(self.kwargs)

    @kwargs_dict.setter
    def kwargs_dict(self, value):
        self.kwargs = json.dumps(value)
