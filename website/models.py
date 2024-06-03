from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tc_no = db.Column(db.String(11), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'teacher'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    department = db.Column(db.String(100), nullable=False)  # Yeni eklenen kolon

class ProgramOutcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

class LearningOutcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    relation_to_program_outcome = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)  
