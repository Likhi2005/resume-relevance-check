from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .student import Student
from .resume import Resume
from .job import Job
from .evaluation import Evaluation

__all__ = ['db', 'Student', 'Resume', 'Job', 'Evaluation']