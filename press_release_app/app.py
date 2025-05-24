from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from .models import db, User, Project, PressRelease, Publication, Contact, TONE_CHOICES, STYLE_CHOICES # Relative import
from .ai_services import generate_text_with_gemini, clarify_story_with_gemini, refine_text_with_gemini # Relative import

from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, HiddenField 
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from wtforms_sqlalchemy.fields import QuerySelectField 
from sqlalchemy.exc import IntegrityError 
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

# Context processor to make datetime available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# --- Forms ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user: raise ValidationError('That username is taken. Please choose a different one.')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user: raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProjectForm(FlaskForm): 
    project_name = StringField('Project Name', validators=[DataRequired(), Length(max=100)])
    key_messages = TextAreaField('Key Messages (Original)', validators=[Optional()])
    target_audience_keywords = TextAreaField('Target Audience Keywords (Original)', validators=[Optional()])
    main_takeaway_input = TextAreaField('Main Takeaway for Story Brief', validators=[Optional()])
    primary_audience_input = TextAreaField('Primary Audience for Story Brief', validators=[Optional()])
    audience_benefit_input = TextAreaField('Audience Benefit/Impact for Story Brief', validators=[Optional()])
    differentiator_input = TextAreaField('Key Differentiator for Story Brief', validators=[Optional()])
    desired_outcome_input = TextAreaField('Desired Outcome for Story Brief', validators=[Optional()])
    tone = SelectField('Tone', choices=TONE_CHOICES, default='neutral', validators=[Optional()])
    style = SelectField('Style', choices=STYLE_CHOICES, default='standard_pr', validators=[Optional()])
    submit = SubmitField('Save Project')

class StoryClarificationForm(FlaskForm): 
    main_takeaway_input = TextAreaField('Main Takeaway', validators=[DataRequired()])
    primary_audience_input = TextAreaField('Primary Audience', validators=[DataRequired()])
    audience_benefit_input = TextAreaField('Why This Audience Should Care (Benefit/Impact)', validators=[DataRequired()])
    differentiator_input = TextAreaField('Key Differentiator/Uniqueness', validators=[DataRequired()])
    desired_outcome_input = TextAreaField('Desired Outcome of the Press Release', validators=[DataRequired()])
    submit = SubmitField('Generate/Update Core Narrative Brief')

class EditPressReleaseForm(FlaskForm):
    generated_content = TextAreaField('Content', validators=[DataRequired()])
    status_choices = [
        ('draft', 'Draft'), ('draft_from_ai', 'Draft (from AI)'),
        ('draft_from_stub_web', 'Draft (from Web Stub)'), ('draft_from_stub_api', 'Draft (from API Stub)'),
        ('generation_failed', 'Generation Failed'), ('final_review', 'Final Review'), ('published', 'Published')
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
    publication = QuerySelectField('Publication (Optional)', query_factory=publication_query_factory, 
                                 get_label='name', allow_blank=True, blank_text='-- Select a Publication --', validators=[Optional()])
    notes = TextAreaField('Notes (Optional)')
    submit = SubmitField('Save Contact')
    def __init__(self, *args, **kwargs): super(ContactForm, self).__init__(*args, **kwargs); self._obj = kwargs.get('obj') 
    def validate_email(self, email_field): 
        query = Contact.query.filter_by(email=email_field.data) 
        if self._obj and hasattr(self._obj, 'id'): query = query.filter(Contact.id != self._obj.id)
        if query.first(): raise ValidationError('This email address is already in use globally.')

def contact_query_factory(): 
    return Contact.query.filter_by(user_id=current_user.id).order_by(Contact.name)

class AddContactToProjectForm(FlaskForm):
    contact = QuerySelectField('Select Contact to Add', query_factory=contact_query_factory, 
                               get_label=lambda c: f"{c.name} ({c.email})", allow_blank=False, validators=[DataRequired()])
    submit = SubmitField('Add Contact to Project')

class TextRefinementForm(FlaskForm):
    text_to_refine_manual = TextAreaField('Text Snippet to Refine', validators=[DataRequired(), Length(min=10, max=2000)])
    refinement_type_choices = [
        ('concise', 'Make Concise'),
        ('alternative_phrasing', 'Suggest Alternatives'),
        ('simplify_jargon', 'Simplify Jargon')
    ]
    refinement_type = SelectField('Refinement Type', choices=refinement_type_choices, validators=[DataRequired()])
    original_pr_content = HiddenField('Original PR Content') 
    submit = SubmitField('Get Refinement Suggestion')


with app.app_context():
    db.create_all()

@app.route('/')
def home_redirect():
    if current_user.is_authenticated: return redirect(url_for('dashboard_web'))
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
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.last_modified.desc()).all()
    return render_template('index.html', projects=projects)

@app.route('/ui/projects/new', methods=['GET', 'POST'])
@login_required
def create_new_project_web():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(
            project_name=form.project_name.data, key_messages=form.key_messages.data,
            target_audience_keywords=form.target_audience_keywords.data,
            main_takeaway_input=form.main_takeaway_input.data, primary_audience_input=form.primary_audience_input.data,
            audience_benefit_input=form.audience_benefit_input.data, differentiator_input=form.differentiator_input.data,
            desired_outcome_input=form.desired_outcome_input.data, tone=form.tone.data, style=form.style.data,
            user_id=current_user.id
        )
        db.session.add(new_project); db.session.commit()
        flash(f'Project "{new_project.project_name}" created successfully!', 'success')
        return redirect(url_for('project_detail_web', project_id=new_project.id))
    return render_template('create_project.html', title="Create New Project", form=form)

@app.route('/ui/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = ProjectForm(obj=project) 
    if form.validate_on_submit():
        form.populate_obj(project) 
        db.session.commit()
        flash(f'Project "{project.project_name}" updated successfully!', 'success')
        return redirect(url_for('project_detail_web', project_id=project.id))
    return render_template('edit_project.html', title=f"Edit Project: {project.project_name}", form=form, project=project)

@app.route('/ui/projects/<int:project_id>')
@login_required
def project_detail_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    add_contact_form = AddContactToProjectForm()
    existing_contact_ids = {contact.id for contact in project.target_contacts}
    add_contact_form.contact.query = Contact.query.filter(Contact.user_id == current_user.id, ~Contact.id.in_(existing_contact_ids)).order_by(Contact.name)
    story_form_data = {
        'main_takeaway_input': project.main_takeaway_input, 'primary_audience_input': project.primary_audience_input,
        'audience_benefit_input': project.audience_benefit_input, 'differentiator_input': project.differentiator_input,
        'desired_outcome_input': project.desired_outcome_input
    }
    story_clarification_form = StoryClarificationForm(data=story_form_data)
    return render_template('project_detail.html', project=project, title=project.project_name, 
                           add_contact_form=add_contact_form, story_clarification_form=story_clarification_form,
                           tone_choices=dict(TONE_CHOICES), style_choices=dict(STYLE_CHOICES))

@app.route('/ui/projects/<int:project_id>/clarify_story_web', methods=['POST'])
@login_required
def clarify_story_project_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = StoryClarificationForm() 
    if form.validate_on_submit(): 
        story_elements = {
            'main_takeaway': form.main_takeaway_input.data, 'primary_audience': form.primary_audience_input.data,
            'audience_benefit': form.audience_benefit_input.data, 'differentiator': form.differentiator_input.data,
            'desired_outcome': form.desired_outcome_input.data
        }
        project.main_takeaway_input = form.main_takeaway_input.data
        project.primary_audience_input = form.primary_audience_input.data
        project.audience_benefit_input = form.audience_benefit_input.data
        project.differentiator_input = form.differentiator_input.data
        project.desired_outcome_input = form.desired_outcome_input.data
        clarified_brief = clarify_story_with_gemini(story_elements)
        if clarified_brief.startswith("Error:") or clarified_brief.startswith("ERROR:"):
            flash(f"Failed to generate Core Narrative Brief: {clarified_brief}", 'danger')
        else:
            project.core_narrative_brief = clarified_brief
            flash("Core Narrative Brief generated/updated successfully!", 'success')
        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors: flash(f"Error in '{getattr(form, field).label.text}': {error}", 'danger')
    return redirect(url_for('project_detail_web', project_id=project.id))

@app.route('/ui/projects/<int:project_id>/generate', methods=['POST'])
@login_required
def generate_press_release_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    project_data_for_ai = {
        'project_name': project.project_name, 'core_narrative_brief': project.core_narrative_brief,
        'main_takeaway_input': project.main_takeaway_input, 'primary_audience_input': project.primary_audience_input,
        'audience_benefit_input': project.audience_benefit_input, 'differentiator_input': project.differentiator_input,
        'desired_outcome_input': project.desired_outcome_input, 'key_messages': project.key_messages,
        'target_audience_keywords': project.target_audience_keywords, 'tone': project.tone, 'style': project.style
    }
    generated_content = generate_text_with_gemini(project_data_for_ai)
    status = "draft_from_ai" if not generated_content.startswith("Error:") else "generation_failed"
    new_pr = PressRelease(project_id=project.id, status=status, generated_content=generated_content)
    db.session.add(new_pr); db.session.commit()
    flash_msg = f"AI-generated PR (ID: {new_pr.id}) for '{project.project_name}' - Status: {status}."
    flash(flash_msg, "success" if status == "draft_from_ai" else "danger")
    return redirect(url_for('project_detail_web', project_id=project.id))

@app.route('/ui/press_releases/<int:pr_id>', methods=['GET']) 
@login_required
def view_press_release_web(pr_id): 
    press_release = PressRelease.query.get_or_404(pr_id)
    if press_release.project.user_id != current_user.id: return redirect(url_for('dashboard_web')) 
    refinement_form = TextRefinementForm(original_pr_content=press_release.generated_content)
    refinement_suggestion = request.args.get('refinement_suggestion', None)
    return render_template('view_press_release.html', press_release=press_release, project=press_release.project, 
                           title=f"View PR: {press_release.id}", refinement_form=refinement_form, 
                           refinement_suggestion=refinement_suggestion)

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

@app.route('/ui/press_releases/<int:pr_id>/refine_text_action', methods=['POST'])
@login_required
def refine_text_action_web(pr_id):
    press_release = PressRelease.query.get_or_404(pr_id)
    if press_release.project.user_id != current_user.id: return redirect(url_for('dashboard_web')) 
    form = TextRefinementForm() 
    refinement_suggestion_text = None 
    if form.validate_on_submit():
        text_to_refine = form.text_to_refine_manual.data
        refinement_type = form.refinement_type.data
        original_context = form.original_pr_content.data 
        refinement_suggestion_text = refine_text_with_gemini(text_to_refine, refinement_type, original_context)
        if refinement_suggestion_text.startswith("Error:") or refinement_suggestion_text.startswith("ERROR:"):
            flash(f"AI Refinement Error: {refinement_suggestion_text}", 'danger')
            refinement_suggestion_text = None 
        else:
            flash("AI refinement suggestion received.", 'info')
    else: 
        for field, errors in form.errors.items():
            for error in errors: flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('view_press_release_web', pr_id=pr_id, refinement_suggestion=refinement_suggestion_text))

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
    form.publication.query = Publication.query.filter_by(user_id=current_user.id).order_by(Publication.name)
    if form.validate_on_submit():
        publication_instance = form.publication.data
        new_contact = Contact(name=form.name.data, email=form.email.data, role=form.role.data,
                              notes=form.notes.data, user_id=current_user.id,
                              publication_id=publication_instance.id if publication_instance else None)
        try:
            db.session.add(new_contact); db.session.commit()
            flash(f"Contact '{new_contact.name}' created successfully!", 'success')
        except IntegrityError: 
            db.session.rollback()
            flash(f"Error: Email '{new_contact.email}' already exists globally. Could not create contact.", 'danger')
        return redirect(url_for('contacts_web'))
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.name).all()
    return render_template('contacts.html', contacts=contacts, form=form, title="My Contacts")

@app.route('/ui/projects/<int:project_id>/add_contact', methods=['POST'])
@login_required
def project_add_contact_web(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = AddContactToProjectForm() 
    existing_contact_ids = {contact.id for contact in project.target_contacts}
    form.contact.query = Contact.query.filter( Contact.user_id == current_user.id, ~Contact.id.in_(existing_contact_ids) ).order_by(Contact.name)
    if form.validate_on_submit():
        contact_to_add = form.contact.data 
        if contact_to_add not in project.target_contacts:
            project.target_contacts.append(contact_to_add)
            db.session.commit()
            flash(f"Contact '{contact_to_add.name}' added to project '{project.project_name}'.", 'success')
        else:
            flash(f"Contact '{contact_to_add.name}' is already in project '{project.project_name}'.", 'info')
    else:
        for field, errors in form.errors.items():
            for error in errors: flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
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
# ... (All API Endpoints from previous tasks are assumed to be here and correct) ...

if __name__ == '__main__':
    app.run(debug=True)
