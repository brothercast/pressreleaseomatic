from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, Table, Column, Integer, ForeignKey 
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Define choices for Tone and Style at the module level
TONE_CHOICES = [
    ('neutral', 'Neutral/Factual'), 
    ('formal', 'Formal'), 
    ('enthusiastic', 'Enthusiastic'), 
    ('thought_leader', 'Thought Leader/ 무게감 있게') # Example label
]

STYLE_CHOICES = [
    ('standard_pr', 'Standard Press Release'), 
    ('q_and_a', 'Q&A Format'), 
    ('story_lead', 'Feature Story Lead-in'), 
    ('bullet_points', 'Key Bullet Points Summary')
]

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
    publications = db.relationship('Publication', backref='owner', lazy=True, cascade="all, delete-orphan")
    contacts = db.relationship('Contact', backref='owner', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    key_messages = db.Column(Text, nullable=True) 
    target_audience_keywords = db.Column(Text, nullable=True) 
    
    main_takeaway_input = db.Column(Text, nullable=True)
    primary_audience_input = db.Column(Text, nullable=True)
    audience_benefit_input = db.Column(Text, nullable=True)
    differentiator_input = db.Column(Text, nullable=True)
    desired_outcome_input = db.Column(Text, nullable=True)
    
    core_narrative_brief = db.Column(Text, nullable=True) 
    
    # New fields for Tone and Style
    tone = db.Column(db.String(50), nullable=True, default='neutral')
    style = db.Column(db.String(50), nullable=True, default='standard_pr')
    
    press_releases = db.relationship('PressRelease', backref='project', lazy=True, cascade="all, delete-orphan")
    target_contacts = db.relationship('Contact', secondary=project_contacts_table,
                                      backref=db.backref('projects', lazy='dynamic'), 
                                      lazy='dynamic')
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    contacts = db.relationship('Contact', backref='publication', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Publication {self.name}>'

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True) 
    role = db.Column(db.String(100), nullable=True)
    notes = db.Column(Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    publication_id = db.Column(db.Integer, db.ForeignKey('publication.id'), nullable=True)

    def __repr__(self):
        return f'<Contact {self.name} - {self.email}>'
