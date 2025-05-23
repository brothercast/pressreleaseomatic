from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from models import db, User, Project, PressRelease # Import models
from press_release_app.ai_services import generate_text_with_gemini # Import the stub function

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///press_release.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Necessary for flash messages

# Initialize SQLAlchemy with the app
db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# --- API Endpoints (from previous task) ---
@app.route('/')
def hello():
    return "Hello, Press Release App! Database and models should be initialized. API and UI active."

def get_or_create_mock_user():
    user = User.query.get(1)
    if not user:
        user = User(id=1, username='mockuser', email='mock@example.com')
        db.session.add(user)
        db.session.commit()
    return user

@app.route('/projects', methods=['POST'])
def create_project_api():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    project_name = data.get('project_name')
    if not project_name:
        return jsonify({"error": "Project name is required"}), 400
    mock_user = get_or_create_mock_user()
    new_project = Project(
        project_name=project_name,
        key_messages=data.get('key_messages'),
        target_audience_keywords=data.get('target_audience_keywords'),
        user_id=mock_user.id
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify({
        "id": new_project.id, "project_name": new_project.project_name,
        "key_messages": new_project.key_messages,
        "target_audience_keywords": new_project.target_audience_keywords,
        "user_id": new_project.user_id
    }), 201

@app.route('/projects', methods=['GET'])
def get_projects_api():
    projects = Project.query.all()
    projects_data = [{"id": p.id, "project_name": p.project_name} for p in projects]
    return jsonify(projects_data), 200

@app.route('/projects/<int:project_id>', methods=['GET'])
def get_project_api(project_id):
    project = Project.query.get(project_id)
    if project:
        return jsonify({
            "id": project.id, "project_name": project.project_name,
            "key_messages": project.key_messages,
            "target_audience_keywords": project.target_audience_keywords,
            "user_id": project.user_id
        }), 200
    else:
        return jsonify({"error": "Project not found"}), 404

@app.route('/projects/<int:project_id>/generate_press_release', methods=['POST'])
def generate_project_press_release_api(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    prompt = f"Generate a press release about {project.project_name}. Key messages: {project.key_messages}. Target audience keywords: {project.target_audience_keywords}"
    generated_content = generate_text_with_gemini(prompt)
    
    new_press_release = PressRelease(
        project_id=project.id, 
        status="draft_from_stub_api", # Updated status
        generated_content=generated_content # Save stubbed content
    )
    db.session.add(new_press_release)
    db.session.commit()
    return jsonify({
        "message": f"Press release generation (stubbed) complete for project_id {project.id}",
        "press_release_id": new_press_release.id,
        "status": new_press_release.status,
        "stubbed_content_preview": generated_content[:100] # Include preview
    }), 201

# --- Web UI Routes ---
@app.route('/ui/dashboard')
def dashboard_web():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/ui/projects/new', methods=['GET', 'POST'])
def create_new_project_web():
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        key_messages = request.form.get('key_messages')
        target_audience_keywords = request.form.get('target_audience_keywords')

        if not project_name:
            flash('Project name is required!', 'error')
            return render_template('create_project.html')

        mock_user = get_or_create_mock_user()
        new_project = Project(
            project_name=project_name,
            key_messages=key_messages,
            target_audience_keywords=target_audience_keywords,
            user_id=mock_user.id
        )
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project "{project_name}" created successfully!', 'success')
        return redirect(url_for('dashboard_web'))
    return render_template('create_project.html')

@app.route('/ui/projects/<int:project_id>')
def project_detail_web(project_id):
    project = Project.query.get_or_404(project_id) 
    return render_template('project_detail.html', project=project)

@app.route('/ui/projects/<int:project_id>/generate', methods=['POST'])
def generate_press_release_web(project_id):
    project = Project.query.get_or_404(project_id)
    
    prompt = f"Generate a press release for the project: '{project.project_name}'. Key messages include: '{project.key_messages}'. Target audience keywords: '{project.target_audience_keywords}'."
    generated_content = generate_text_with_gemini(prompt)
    
    new_press_release = PressRelease(
        project_id=project.id,
        status="draft_from_stub_web", # Updated status
        generated_content=generated_content # Save stubbed content
    )
    db.session.add(new_press_release)
    db.session.commit()
    
    flash(f"Stubbed press release generated for '{project.project_name}'. (ID: {new_press_release.id})", 'info')
    return redirect(url_for('project_detail_web', project_id=project.id))

if __name__ == '__main__':
    app.run(debug=True)
