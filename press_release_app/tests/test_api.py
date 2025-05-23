import pytest
import json
from unittest.mock import patch # Import patch
from press_release_app.app import app as flask_app # Renamed to avoid confusion
from press_release_app.models import db, User, Project, PressRelease, Publication, Contact # Import new models

@pytest.fixture
def client():
    """
    Provides a Flask test client configured for testing without a logged-in user.
    Handles app context and database setup/teardown.
    """
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    flask_app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for simpler API testing
    flask_app.config['SECRET_KEY'] = 'test_secret_key' # Consistent secret key for tests
    # Ensure LOGIN_DISABLED is not set globally if it affects specific auth tests
    # flask_app.config['LOGIN_DISABLED'] = False # Default for most tests

    with flask_app.app_context():
        db.create_all() # Create all tables
        yield flask_app.test_client() # Provide the test client to the tests
        db.session.remove() # Ensure session is properly closed
        db.drop_all()     # Drop all tables after the test

@pytest.fixture
def auth_client(client): # Depends on the unauthenticated client fixture
    """
    Provides a Flask test client that is logged in as a pre-defined test user.
    Also creates the user in the database.
    """
    with flask_app.app_context(): # Ensure we are in an app context for DB operations
        test_username = 'testuser'
        test_email = 'test@example.com'
        test_password = 'testpassword' # Not used for session creation here, but good to define
        
        user = User.query.filter_by(email=test_email).first()
        if not user:
            from flask_bcrypt import Bcrypt # Local import for bcrypt
            bcrypt_instance = Bcrypt(flask_app) # Use a temporary instance
            hashed_password = bcrypt_instance.generate_password_hash(test_password).decode('utf-8')
            user = User(username=test_username, email=test_email, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
        
        # Use the client to log in by setting the session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id) 
            sess['_fresh'] = True 
        
        flask_app.config['TEST_USER_ID'] = user.id 
        flask_app.config['TEST_USER_OBJECT'] = user 
        yield client 

# --- Initial Setup Tests ---
def test_unauthenticated_access_to_protected_api(client):
    response = client.get('/api/projects') 
    assert response.status_code == 401 

# --- Project API Tests ---
def test_create_project_api(auth_client):
    sample_project_data = {"project_name": "Test Project Alpha", "key_messages": "Msg A", "target_audience_keywords": "Alpha"}
    response = auth_client.post('/api/projects', json=sample_project_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['project_name'] == sample_project_data['project_name']
    assert data['user_id'] == flask_app.config['TEST_USER_ID']

def test_get_projects_api(auth_client):
    auth_client.post('/api/projects', json={"project_name": "Project Beta"})
    response = auth_client.get('/api/projects')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list); assert len(data) >= 1
    assert data[0]['project_name'] == "Project Beta"

# --- Press Release CRUD API Tests ---
def test_get_project_press_releases_api(auth_client):
    project_res = auth_client.post('/api/projects', json={"project_name": "PR List Project"})
    project_id = project_res.get_json()['id']
    with patch('press_release_app.ai_services.generate_text_with_gemini') as mock_gemini:
        mock_gemini.return_value = "Stubbed PR content for listing test."
        pr_gen_res = auth_client.post(f'/api/projects/{project_id}/generate_press_release')
        pr_id = pr_gen_res.get_json()['press_release_id']
    response = auth_client.get(f'/api/projects/{project_id}/press_releases')
    assert response.status_code == 200
    data = response.get_json(); assert isinstance(data, list); assert len(data) == 1
    assert data[0]['id'] == pr_id; assert "Stubbed PR content" in data[0]['truncated_content']

def test_get_specific_press_release_api(auth_client):
    project_res = auth_client.post('/api/projects', json={"project_name": "Specific PR Project"})
    project_id = project_res.get_json()['id']
    with patch('press_release_app.ai_services.generate_text_with_gemini') as mock_gemini:
        mock_gemini.return_value = "Detailed content for specific PR."
        pr_gen_res = auth_client.post(f'/api/projects/{project_id}/generate_press_release')
        pr_id = pr_gen_res.get_json()['press_release_id']
    response = auth_client.get(f'/api/press_releases/{pr_id}')
    assert response.status_code == 200
    data = response.get_json(); assert data['id'] == pr_id
    assert data['generated_content'] == "Detailed content for specific PR."

def test_update_press_release_api(auth_client):
    project_res = auth_client.post('/api/projects', json={"project_name": "Update PR Project"})
    project_id = project_res.get_json()['id']
    with patch('press_release_app.ai_services.generate_text_with_gemini') as mock_gemini:
        mock_gemini.return_value = "Initial content for update."
        pr_gen_res = auth_client.post(f'/api/projects/{project_id}/generate_press_release')
        pr_id = pr_gen_res.get_json()['press_release_id']
    update_data = {"generated_content": "Updated PR content.", "status": "final_review"}
    response = auth_client.put(f'/api/press_releases/{pr_id}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['generated_content'] == update_data['generated_content']
    assert data['status'] == update_data['status']

def test_delete_press_release_api(auth_client):
    project_res = auth_client.post('/api/projects', json={"project_name": "Delete PR Project"})
    project_id = project_res.get_json()['id']
    with patch('press_release_app.ai_services.generate_text_with_gemini') as mock_gemini:
        mock_gemini.return_value = "Content to be deleted."
        pr_gen_res = auth_client.post(f'/api/projects/{project_id}/generate_press_release')
        pr_id = pr_gen_res.get_json()['press_release_id']
    response = auth_client.delete(f'/api/press_releases/{pr_id}')
    assert response.status_code == 200
    get_response = auth_client.get(f'/api/press_releases/{pr_id}')
    assert get_response.status_code == 404

def test_press_release_ownership_api(client): 
    # User A setup
    user_a_email = 'usera_pr_own@example.com'; user_a_pw = 'passworda'
    with flask_app.app_context():
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(flask_app) # New bcrypt instance for this context
        user_a = User(username='usera_pr_own', email=user_a_email, password_hash=bcrypt.generate_password_hash(user_a_pw).decode('utf-8'))
        db.session.add(user_a); db.session.commit(); user_a_id = user_a.id
    with client.session_transaction() as sess_a: sess_a['_user_id'] = str(user_a_id); sess_a['_fresh'] = True
    project_res_a = client.post('/api/projects', json={"project_name": "User A Project for PR Ownership"})
    project_id_a = project_res_a.get_json()['id']
    with patch('press_release_app.ai_services.generate_text_with_gemini') as mock_gemini:
        mock_gemini.return_value = "User A PR content."
        pr_gen_res_a = client.post(f'/api/projects/{project_id_a}/generate_press_release')
        pr_id_a = pr_gen_res_a.get_json()['press_release_id']
    with client.session_transaction() as sess_a_logout: sess_a_logout.clear() # Log out User A

    # User B setup & login
    user_b_email = 'userb_pr_own@example.com'; user_b_pw = 'passwordb'
    with flask_app.app_context():
        from flask_bcrypt import Bcrypt
        bcrypt_b = Bcrypt(flask_app) # New bcrypt instance for this context
        user_b = User(username='userb_pr_own', email=user_b_email, password_hash=bcrypt_b.generate_password_hash(user_b_pw).decode('utf-8'))
        db.session.add(user_b); db.session.commit(); user_b_id = user_b.id
    with client.session_transaction() as sess_b: sess_b['_user_id'] = str(user_b_id); sess_b['_fresh'] = True
    
    # User B tries to access/modify User A's PR
    assert client.get(f'/api/press_releases/{pr_id_a}').status_code == 403
    assert client.put(f'/api/press_releases/{pr_id_a}', json={"content": "User B edit"}).status_code == 403
    assert client.delete(f'/api/press_releases/{pr_id_a}').status_code == 403
    assert client.get(f'/api/projects/{project_id_a}/press_releases').status_code == 404 # Project not found for User B

# --- Gemini API Call (Mocked) Test ---
@patch('press_release_app.ai_services.generate_text_with_gemini')
def test_generate_press_release_api_mocked_gemini(mock_generate_text, auth_client):
    mock_generate_text.return_value = "This is a successfully mocked Gemini response."
    
    project_res = auth_client.post('/api/projects', json={"project_name": "Mock Gemini Project"})
    project_id = project_res.get_json()['id']

    response = auth_client.post(f'/api/projects/{project_id}/generate_press_release')
    assert response.status_code == 201
    data = response.get_json()
    
    mock_generate_text.assert_called_once() # Check if the mock was called
    assert data['status'] == "draft_from_ai"
    assert "successfully mocked Gemini response" in data['generated_content_preview']
    
    with flask_app.app_context():
        pr = PressRelease.query.get(data['press_release_id'])
        assert pr is not None
        assert pr.generated_content == "This is a successfully mocked Gemini response."

@patch('press_release_app.ai_services.generate_text_with_gemini')
def test_generate_press_release_api_mocked_gemini_error(mock_generate_text, auth_client):
    mock_generate_text.return_value = "ERROR: Gemini API failed for testing."
    
    project_res = auth_client.post('/api/projects', json={"project_name": "Mock Gemini Error Project"})
    project_id = project_res.get_json()['id']

    response = auth_client.post(f'/api/projects/{project_id}/generate_press_release')
    assert response.status_code == 500 # As per current app.py logic
    data = response.get_json()
    
    mock_generate_text.assert_called_once()
    assert data['status'] == "generation_failed"
    assert "ERROR: Gemini API failed for testing." in data['generated_content_preview']

    with flask_app.app_context():
        pr = PressRelease.query.get(data['press_release_id'])
        assert pr is not None
        assert pr.generated_content == "ERROR: Gemini API failed for testing."

# --- Publication API Tests ---
def test_create_publication_api(auth_client):
    pub_data = {"name": "Test Pub Weekly", "website": "http://testpub.com", "notes": "Test notes"}
    response = auth_client.post('/api/publications', json=pub_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == pub_data['name']
    assert data['website'] == pub_data['website']
    assert 'id' in data

def test_get_publications_api(auth_client):
    auth_client.post('/api/publications', json={"name": "Tech Times"}) # Create one
    response = auth_client.get('/api/publications')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p['name'] == "Tech Times" for p in data)

# --- Contact API Tests ---
def test_create_contact_api(auth_client):
    # First, create a publication for this user to associate with
    pub_res = auth_client.post('/api/publications', json={"name": "Associated Pub"})
    pub_id = pub_res.get_json()['id']

    contact_data = {"name": "Jane Doe", "email": "jane.doe@example.com", "role": "Editor", "publication_id": pub_id}
    response = auth_client.post('/api/contacts', json=contact_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == contact_data['name']
    assert data['email'] == contact_data['email']
    assert data['publication_id'] == pub_id

def test_create_contact_api_duplicate_email_same_user_should_fail_in_model(auth_client):
    # Model defines Contact.email as globally unique, so this test is for global uniqueness.
    # If it were unique *per user*, this test would need adjustment.
    auth_client.post('/api/contacts', json={"name": "First John", "email": "john.unique@example.com"})
    response_fail = auth_client.post('/api/contacts', json={"name": "Second John", "email": "john.unique@example.com"})
    assert response_fail.status_code == 409 # Conflict due to globally unique email

def test_get_contacts_api(auth_client):
    auth_client.post('/api/contacts', json={"name": "List Contact", "email": "list.contact@example.com"})
    response = auth_client.get('/api/contacts')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert any(c['name'] == "List Contact" for c in data)

# --- Project-Contact Association API Tests ---
def test_project_contact_association_api(auth_client):
    # 1. Create Project, Publication, Contact
    project_res = auth_client.post('/api/projects', json={"project_name": "Assoc Project"})
    project_id = project_res.get_json()['id']
    contact_res = auth_client.post('/api/contacts', json={"name": "Assoc Contact", "email": "assoc.contact@example.com"})
    contact_id = contact_res.get_json()['id']

    # 2. Associate Contact with Project
    assoc_res = auth_client.post(f'/api/projects/{project_id}/contacts/{contact_id}')
    assert assoc_res.status_code == 200

    # 3. Get Project Contacts and verify
    list_res = auth_client.get(f'/api/projects/{project_id}/contacts')
    assert list_res.status_code == 200
    contacts_data = list_res.get_json()
    assert isinstance(contacts_data, list)
    assert len(contacts_data) == 1
    assert contacts_data[0]['id'] == contact_id

    # 4. Try to re-associate (should return 409 Conflict)
    re_assoc_res = auth_client.post(f'/api/projects/{project_id}/contacts/{contact_id}')
    assert re_assoc_res.status_code == 409


    # 5. Disassociate Contact from Project
    disassoc_res = auth_client.delete(f'/api/projects/{project_id}/contacts/{contact_id}')
    assert disassoc_res.status_code == 200

    # 6. Get Project Contacts and verify it's empty
    list_empty_res = auth_client.get(f'/api/projects/{project_id}/contacts')
    assert list_empty_res.status_code == 200
    assert len(list_empty_res.get_json()) == 0

    # 7. Try to disassociate again (should return 404 Not Found for the association)
    re_disassoc_res = auth_client.delete(f'/api/projects/{project_id}/contacts/{contact_id}')
    assert re_disassoc_res.status_code == 404

# --- Ownership tests for Publications and Contacts ---
def test_publication_contact_ownership(client): # Uses unauthenticated client
    # User A setup
    user_a_email = 'usera_pubcon@example.com'; user_a_pw = 'passworda'
    with flask_app.app_context():
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(flask_app)
        user_a = User(username='usera_pubcon', email=user_a_email, password_hash=bcrypt.generate_password_hash(user_a_pw).decode('utf-8'))
        db.session.add(user_a); db.session.commit(); user_a_id = user_a.id
    
    with client.session_transaction() as sess_a: sess_a['_user_id'] = str(user_a_id); sess_a['_fresh'] = True
    pub_a_res = client.post('/api/publications', json={"name": "User A Pub"})
    pub_a_id = pub_a_res.get_json()['id']
    contact_a_res = client.post('/api/contacts', json={"name": "User A Contact", "email": "contacta@example.com", "publication_id": pub_a_id})
    contact_a_id = contact_a_res.get_json()['id']
    project_a_res = client.post('/api/projects', json={"project_name": "User A Project for Contact Assoc"})
    project_a_id = project_a_res.get_json()['id']
    client.post(f'/api/projects/{project_a_id}/contacts/{contact_a_id}') # Associate

    with client.session_transaction() as sess_a_logout: sess_a_logout.clear()

    # User B setup & login
    user_b_email = 'userb_pubcon@example.com'; user_b_pw = 'passwordb'
    with flask_app.app_context():
        from flask_bcrypt import Bcrypt
        bcrypt_b = Bcrypt(flask_app)
        user_b = User(username='userb_pubcon', email=user_b_email, password_hash=bcrypt_b.generate_password_hash(user_b_pw).decode('utf-8'))
        db.session.add(user_b); db.session.commit(); user_b_id = user_b.id
    with client.session_transaction() as sess_b: sess_b['_user_id'] = str(user_b_id); sess_b['_fresh'] = True

    # User B tries to access User A's publications/contacts
    assert client.get('/api/publications').get_json() == [] # Should only see their own (none)
    assert client.get('/api/contacts').get_json() == []    # Should only see their own (none)

    # User B tries to associate User A's contact with their own project (or User A's project)
    project_b_res = client.post('/api/projects', json={"project_name": "User B Project"})
    project_b_id = project_b_res.get_json()['id']
    
    # User B cannot add User A's contact because it won't be found for User B
    response_assoc_foreign_contact = client.post(f'/api/projects/{project_b_id}/contacts/{contact_a_id}')
    assert response_assoc_foreign_contact.status_code == 404 # Contact not found for User B

    # User B cannot list contacts for User A's project
    response_list_foreign_project_contacts = client.get(f'/api/projects/{project_a_id}/contacts')
    assert response_list_foreign_project_contacts.status_code == 404 # Project not found for User B
