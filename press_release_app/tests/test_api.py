import pytest
import json
from press_release_app.app import app as flask_app # Renamed to avoid confusion
from press_release_app.models import db, User, Project, PressRelease

@pytest.fixture
def client():
    # Configure the app for testing
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    
    with flask_app.app_context():
        db.create_all() # Create all tables
        
        # Create a mock user for tests that require a user context
        # This is similar to get_or_create_mock_user in app.py
        # but ensures it's done within the test app context.
        test_user = User.query.get(1)
        if not test_user:
            test_user = User(id=1, username='testuser', email='test@example.com')
            db.session.add(test_user)
            db.session.commit()
            
        yield flask_app.test_client() # Provide the test client to the tests
        
        db.session.remove() # Ensure session is properly closed
        db.drop_all()     # Drop all tables after the test

def test_create_project_api(client):
    """Test API endpoint for creating a new project."""
    sample_project_data = {
        "project_name": "Test Project Alpha",
        "key_messages": "Message A, Message B",
        "target_audience_keywords": "Alpha, Test, API"
    }
    response = client.post('/projects', json=sample_project_data)
    
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data['project_name'] == sample_project_data['project_name']
    assert response_data['key_messages'] == sample_project_data['key_messages']
    assert response_data['target_audience_keywords'] == sample_project_data['target_audience_keywords']
    assert 'id' in response_data
    assert response_data['user_id'] == 1 # Assuming mock user ID 1

    # Verify in DB
    with flask_app.app_context():
        project = Project.query.get(response_data['id'])
        assert project is not None
        assert project.project_name == sample_project_data['project_name']

def test_get_projects_api(client):
    """Test API endpoint for retrieving a list of projects."""
    # First, create a project to ensure there's data
    sample_project_data = {
        "project_name": "Test Project Beta",
        "key_messages": "Message C",
        "target_audience_keywords": "Beta, Test"
    }
    create_response = client.post('/projects', json=sample_project_data)
    assert create_response.status_code == 201
    created_project_id = create_response.get_json()['id']
    created_project_name = create_response.get_json()['project_name']

    # Now, get all projects
    response = client.get('/projects')
    assert response.status_code == 200
    response_data = response.get_json()
    assert isinstance(response_data, list)
    
    # Check if the created project is in the list
    found = False
    for project in response_data:
        if project['id'] == created_project_id and project['project_name'] == created_project_name:
            found = True
            break
    assert found, f"Project Beta (ID: {created_project_id}) not found in GET /projects response."
