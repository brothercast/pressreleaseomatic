from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from models import db, User, Project, PressRelease, Publication, Contact # Added Publication, Contact
from press_release_app.ai_services import generate_text_with_gemini

from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from wtforms_sqlalchemy.fields import QuerySelectField # For selecting existing model objects
from sqlalchemy.exc import IntegrityError # For handling unique constraint errors
from datetime import datetime

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///press_release.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_super_secret_key_for_production_env_var'

# Initialize Extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_web'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Forms ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EditPressReleaseForm(FlaskForm):
    generated_content = TextAreaField('Content', validators=[DataRequired()])
    status_choices = [
        ('draft', 'Draft'), 
        ('draft_from_ai', 'Draft (from AI)'),
        ('draft_from_stub_web', 'Draft (from Web Stub)'),
        ('draft_from_stub_api', 'Draft (from API Stub)'),
        ('generation_failed', 'Generation Failed'),
        ('final_review', 'Final Review'), 
        ('published', 'Published')
    ]
    status = SelectField('Status', choices=status_choices, validators=[DataRequired()])
    submit = SubmitField('Save Changes')

class PublicationForm(FlaskForm):
    name = StringField('Publication Name', validators=[DataRequired(), Length(max=200)])
    website = StringField('Website (Optional)', validators=[Optional(), Length(max=200)]) 
    notes = TextAreaField('Notes (Optional)')
    submit = SubmitField('Save Publication')

def publication_query_factory(): 
    return Publication.query.filter_by(user_id=current_user.id).order_by(Publication.name)

class ContactForm(FlaskForm):
    name = StringField('Contact Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role = StringField('Role (Optional)', validators=[Optional(), Length(max=100)])
    publication = QuerySelectField('Publication (Optional)', 
                                 query_factory=publication_query_factory, 
                                 get_label='name', 
                                 allow_blank=True, 
                                 blank_text='-- Select a Publication --',
                                 validators=[Optional()])
    notes = TextAreaField('Notes (Optional)')
    submit = SubmitField('Save Contact')

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self._obj = kwargs.get('obj') 

    def validate_email(self, email_field): 
        query = Contact.query.filter_by(email=email_field.data) # Check global uniqueness for Contact email
        if self._obj and hasattr(self._obj, 'id'): 
            query = query.filter(Contact.id != self._obj.id)
        existing_contact = query.first()
        if existing_contact:
            raise ValidationError('This email address is already in use globally by another contact.')

def contact_query_factory(): 
    return Contact.query.filter_by(user_id=current_user.id).order_by(Contact.name)

class AddContactToProjectForm(FlaskForm):
    contact = QuerySelectField('Select Contact to Add', 
                               query_factory=contact_query_factory, 
                               get_label=lambda c: f"{c.name} ({c.email})",
                               allow_blank=False,
                               validators=[DataRequired()])
    submit = SubmitField('Add Contact to Project')


with app.app_context():
    db.create_all()

@app.route('/')
def home_redirect():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_web'))
    return redirect(url_for('login_web'))

# --- Web UI Routes ---
@app.route('/ui/register', methods=['GET', 'POST'])
def register_web():
    if current_user.is_authenticated: return redirect(url_for('dashboard_web'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user); db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login_web'))
    return render_template('register.html', title='Register', form=form)

@app.route('/ui/login', methods=['GET', 'POST'])
def login_web():
    if current_user.is_authenticated: return redirect(url_for('dashboard_web'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard_web'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/ui/logout')
@login_required
def logout_web():
    logout_user(); flash('You have been logged out.', 'info')
    return redirect(url_for('login_web'))

@app.route('/ui/dashboard')
@login_required
def dashboard_web():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', projects=projects)

@app.route('/ui/projects/new', methods=['GET', 'POST'])
@login_required
def create_new_project_web():
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        if not project_name:
            flash('Project name is required!', 'error')
            return render_template('create_project.html', title="Create Project")
        new_project = Project(project_name=project_name, key_messages=request.form.get('key_messages'),
                              target_audience_keywords=request.form.get('target_audience_keywords'), user_id=current_user.id)
        db.session.add(new_project); db.session.commit()
        flash(f'Project "{project_name}" created successfully!', 'success')
        return redirect(url_for('dashboard_web'))
    return render_template('create_project.html', title="Create Project")

@app.route('/ui/projects/<int:project_id>')
@login_required
def project_detail_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    add_contact_form = AddContactToProjectForm()
    # Dynamically set the query for the contact field, excluding already added contacts
    existing_contact_ids = {contact.id for contact in project.target_contacts}
    add_contact_form.contact.query = Contact.query.filter(
        Contact.user_id == current_user.id,
        ~Contact.id.in_(existing_contact_ids)
    ).order_by(Contact.name)
    return render_template('project_detail.html', project=project, title=project.project_name, add_contact_form=add_contact_form)

@app.route('/ui/projects/<int:project_id>/generate', methods=['POST'])
@login_required
def generate_press_release_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    prompt = f"Generate a compelling press release for project '{project.project_name}'. Key messages: '{project.key_messages}'. Target audience: '{project.target_audience_keywords}'."
    generated_content = generate_text_with_gemini(prompt)
    status = "draft_from_ai" if not generated_content.startswith("Error:") else "generation_failed"
    new_pr = PressRelease(project_id=project.id, status=status, generated_content=generated_content)
    db.session.add(new_pr); db.session.commit()
    flash_msg = f"AI-generated PR (ID: {new_pr.id}) for '{project.project_name}' - Status: {status}."
    flash(flash_msg, "success" if status == "draft_from_ai" else "danger")
    return redirect(url_for('project_detail_web', project_id=project.id))

@app.route('/ui/press_releases/<int:pr_id>')
@login_required
def view_press_release_web(pr_id):
    pr = PressRelease.query.get_or_404(pr_id)
    if pr.project.user_id != current_user.id: return redirect(url_for('dashboard_web')) # Basic auth check
    return render_template('view_press_release.html', press_release=pr, project=pr.project, title=f"View PR: {pr.id}")

@app.route('/ui/press_releases/<int:pr_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_press_release_web(pr_id):
    pr = PressRelease.query.get_or_404(pr_id)
    if pr.project.user_id != current_user.id: return redirect(url_for('dashboard_web'))
    form = EditPressReleaseForm(obj=pr)
    if form.validate_on_submit():
        pr.generated_content = form.generated_content.data; pr.status = form.status.data
        pr.last_modified = datetime.utcnow()
        db.session.commit(); flash('Press release updated!', 'success')
        return redirect(url_for('view_press_release_web', pr_id=pr.id))
    return render_template('edit_press_release.html', form=form, press_release=pr, project=pr.project, title=f"Edit PR: {pr.id}")

@app.route('/ui/press_releases/<int:pr_id>/delete', methods=['POST'])
@login_required
def delete_press_release_web(pr_id):
    pr = PressRelease.query.get_or_404(pr_id)
    if pr.project.user_id != current_user.id: return redirect(url_for('dashboard_web'))
    project_id = pr.project_id
    db.session.delete(pr); db.session.commit()
    flash(f'PR (ID: {pr_id}) deleted.', 'success')
    return redirect(url_for('project_detail_web', project_id=project_id))

# --- Publication & Contact Management Web UI Routes ---
@app.route('/ui/publications', methods=['GET', 'POST'])
@login_required
def publications_web():
    form = PublicationForm()
    if form.validate_on_submit():
        new_publication = Publication(name=form.name.data, website=form.website.data, 
                                      notes=form.notes.data, user_id=current_user.id)
        db.session.add(new_publication); db.session.commit()
        flash(f"Publication '{new_publication.name}' created successfully!", 'success')
        return redirect(url_for('publications_web'))
    publications = Publication.query.filter_by(user_id=current_user.id).order_by(Publication.name).all()
    return render_template('publications.html', publications=publications, form=form, title="My Publications")

@app.route('/ui/contacts', methods=['GET', 'POST'])
@login_required
def contacts_web():
    form = ContactForm()
    # Dynamically set the query for the publication field
    form.publication.query = Publication.query.filter_by(user_id=current_user.id).order_by(Publication.name)
    
    if form.validate_on_submit():
        publication_instance = form.publication.data # This is the Publication object from QuerySelectField
        new_contact = Contact(name=form.name.data, email=form.email.data, role=form.role.data,
                              notes=form.notes.data, user_id=current_user.id,
                              publication_id=publication_instance.id if publication_instance else None)
        try:
            db.session.add(new_contact); db.session.commit()
            flash(f"Contact '{new_contact.name}' created successfully!", 'success')
        except IntegrityError:
            db.session.rollback()
            flash(f"Error: Email '{new_contact.email}' already exists. Could not create contact.", 'danger')
        return redirect(url_for('contacts_web'))
        
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.name).all()
    return render_template('contacts.html', contacts=contacts, form=form, title="My Contacts")

@app.route('/ui/projects/<int:project_id>/add_contact', methods=['POST'])
@login_required
def project_add_contact_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = AddContactToProjectForm() # Create an instance of the form to validate
    
    # Dynamically set the query for the contact field for validation purposes
    existing_contact_ids = {contact.id for contact in project.target_contacts}
    form.contact.query = Contact.query.filter(
        Contact.user_id == current_user.id,
        ~Contact.id.in_(existing_contact_ids) # Exclude contacts already in the project for selection
    ).order_by(Contact.name)

    if form.validate_on_submit():
        contact_to_add = form.contact.data # This is the Contact object from QuerySelectField
        if contact_to_add not in project.target_contacts:
            project.target_contacts.append(contact_to_add)
            db.session.commit()
            flash(f"Contact '{contact_to_add.name}' added to project '{project.project_name}'.", 'success')
        else:
            flash(f"Contact '{contact_to_add.name}' is already in project '{project.project_name}'.", 'info')
    else:
        # Handle form validation errors if any (though less likely for a single select field if choices are valid)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('project_detail_web', project_id=project.id))

@app.route('/ui/projects/<int:project_id>/remove_contact/<int:contact_id>', methods=['POST'])
@login_required
def project_remove_contact_web(project_id, contact_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    contact_to_remove = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()

    if contact_to_remove in project.target_contacts:
        project.target_contacts.remove(contact_to_remove)
        db.session.commit()
        flash(f"Contact '{contact_to_remove.name}' removed from project '{project.project_name}'.", 'success')
    else:
        flash(f"Contact '{contact_to_remove.name}' was not found in project '{project.project_name}'.", 'warning')
    return redirect(url_for('project_detail_web', project_id=project.id))


# --- API Endpoints ---
# (Previously defined API endpoints for projects, press releases, publications, contacts, project-contact associations)
# ... (These are correctly defined in the previous turn's app.py, so no change needed here) ...

if __name__ == '__main__':
    app.run(debug=True)
