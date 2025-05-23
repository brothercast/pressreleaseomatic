from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text # Import Text type

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    projects = db.relationship('Project', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    key_messages = db.Column(Text, nullable=True)
    target_audience_keywords = db.Column(Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    press_releases = db.relationship('PressRelease', backref='project', lazy=True)

    def __repr__(self):
        return f'<Project {self.project_name}>'

class PressRelease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    generated_content = db.Column(Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='draft') # e.g., "draft", "final", "sent"
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    def __repr__(self):
        return f'<PressRelease {self.id} - Status: {self.status}>'
