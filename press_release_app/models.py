from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, Table, Column, Integer, ForeignKey # Ensure Table, Column, Integer, ForeignKey are imported
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Association Table for Project and Contact (Many-to-Many)
project_contacts_table = Table('project_contacts', db.metadata,
    Column('project_id', Integer, ForeignKey('project.id'), primary_key=True),
    Column('contact_id', Integer, ForeignKey('contact.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    projects = db.relationship('Project', backref='author', lazy=True)
    # User's own publications and contacts
    publications = db.relationship('Publication', backref='owner', lazy=True, cascade="all, delete-orphan")
    contacts = db.relationship('Contact', backref='owner', lazy=True, cascade="all, delete-orphan")


    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    key_messages = db.Column(Text, nullable=True)
    target_audience_keywords = db.Column(Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    press_releases = db.relationship('PressRelease', backref='project', lazy=True, cascade="all, delete-orphan")
    # Many-to-many relationship with Contact
    target_contacts = db.relationship('Contact', secondary=project_contacts_table,
                                      backref=db.backref('projects', lazy='dynamic'), 
                                      lazy='dynamic')

    def __repr__(self):
        return f'<Project {self.project_name}>'

class PressRelease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    generated_content = db.Column(Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='draft')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PressRelease {self.id} - Status: {self.status}>'

class Publication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    notes = db.Column(Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Owner of this publication record
    contacts = db.relationship('Contact', backref='publication', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Publication {self.name}>'

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True) 
    role = db.Column(db.String(100), nullable=True)
    notes = db.Column(Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Owner of this contact record
    publication_id = db.Column(db.Integer, db.ForeignKey('publication.id'), nullable=True)

    def __repr__(self):
        return f'<Contact {self.name} - {self.email}>'
