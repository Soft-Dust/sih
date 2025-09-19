import pytest
import json
from tests.conftest import login_user

def test_login_success(client, admin_user):
    """Test successful login"""
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['username'] == 'admin'

def test_login_failure(client):
    """Test login with invalid credentials"""
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'wrong'
    })
    assert response.status_code == 401

def test_logout(client, admin_user):
    """Test logout"""
    # Login first
    login_user(client, 'admin', 'password')

    # Then logout
    response = client.post('/api/logout')
    assert response.status_code == 200

def test_current_user(client, admin_user):
    """Test getting current user info"""
    # Login first
    login_user(client, 'admin', 'password')

    response = client.get('/api/current-user')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user']['username'] == 'admin'

def test_teachers_crud(client, admin_user):
    """Test teachers CRUD operations"""
    # Login as admin
    login_user(client, 'admin', 'password')

    # Create teacher
    teacher_data = {
        'username': 'newteacher',
        'full_name': 'New Teacher',
        'email': 'new@teacher.com',
        'password': 'password123',
        'department': 'Computer Science'
    }
    response = client.post('/api/teachers', json=teacher_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    teacher_id = data['id']

    # Get teachers
    response = client.get('/api/teachers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1

    # Update teacher
    update_data = {
        'full_name': 'Updated Teacher Name',
        'department': 'Mathematics'
    }
    response = client.put(f'/api/teachers/{teacher_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['full_name'] == 'Updated Teacher Name'

    # Delete teacher
    response = client.delete(f'/api/teachers/{teacher_id}')
    assert response.status_code == 200

def test_sections_crud(client, admin_user):
    """Test sections CRUD operations"""
    # Login as admin
    login_user(client, 'admin', 'password')

    # Create section
    section_data = {
        'name': 'TEST-SECTION',
        'year_level': 1
    }
    response = client.post('/api/sections', json=section_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    section_id = data['id']

    # Get sections
    response = client.get('/api/sections')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1

    # Update section
    update_data = {
        'name': 'UPDATED-SECTION',
        'year_level': 2
    }
    response = client.put(f'/api/sections/{section_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'UPDATED-SECTION'

    # Delete section
    response = client.delete(f'/api/sections/{section_id}')
    assert response.status_code == 200

def test_subjects_crud(client, admin_user):
    """Test subjects CRUD operations"""
    # Login as admin
    login_user(client, 'admin', 'password')

    # Create subject
    subject_data = {
        'name': 'Test Subject',
        'code': 'TEST101',
        'periods_per_week': 3,
        'is_lab': False,
        'is_elective': False
    }
    response = client.post('/api/subjects', json=subject_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    subject_id = data['id']

    # Get subjects
    response = client.get('/api/subjects')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1

    # Update subject
    update_data = {
        'name': 'Updated Test Subject',
        'periods_per_week': 4
    }
    response = client.put(f'/api/subjects/{subject_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Updated Test Subject'

    # Delete subject
    response = client.delete(f'/api/subjects/{subject_id}')
    assert response.status_code == 200

def test_classrooms_crud(client, admin_user):
    """Test classrooms CRUD operations"""
    # Login as admin
    login_user(client, 'admin', 'password')

    # Create classroom
    classroom_data = {
        'name': 'TEST-ROOM',
        'room_type': 'lecture',
        'capacity': 50
    }
    response = client.post('/api/classrooms', json=classroom_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    classroom_id = data['id']

    # Get classrooms
    response = client.get('/api/classrooms')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1

    # Update classroom
    update_data = {
        'name': 'UPDATED-ROOM',
        'capacity': 60
    }
    response = client.put(f'/api/classrooms/{classroom_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'UPDATED-ROOM'

    # Delete classroom
    response = client.delete(f'/api/classrooms/{classroom_id}')
    assert response.status_code == 200

def test_timetable_slots_generation(client, admin_user):
    """Test timetable slots generation"""
    # Login as admin
    login_user(client, 'admin', 'password')

    # Generate slots
    slots_config = {
        'working_days': ['Monday', 'Tuesday', 'Wednesday'],
        'start_time': '08:00',
        'end_time': '12:00',
        'period_duration': 60,
        'break_periods': [2]
    }
    response = client.post('/api/timetable-slots/generate', json=slots_config)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'slots' in data
    assert len(data['slots']) > 0

    # Get slots
    response = client.get('/api/timetable-slots')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0

def test_authorization_admin_only(client, teacher_user):
    """Test that admin-only endpoints require admin role"""
    # Login as teacher
    login_user(client, 'teacher1', 'password')

    # Try to create a teacher (admin only)
    teacher_data = {
        'username': 'newteacher',
        'full_name': 'New Teacher',
        'password': 'password123'
    }
    response = client.post('/api/teachers', json=teacher_data)
    assert response.status_code == 403

def test_authorization_teacher_access(client, teacher_user):
    """Test teacher access to allowed endpoints"""
    # Login as teacher
    login_user(client, 'teacher1', 'password')

    # Teachers can view teachers
    response = client.get('/api/teachers')
    assert response.status_code == 200

    # Teachers can view subjects
    response = client.get('/api/subjects')
    assert response.status_code == 200

def test_authorization_student_access(client, student_user):
    """Test student access restrictions"""
    # Login as student
    login_user(client, 'student1', 'password')

    # Students cannot view teachers
    response = client.get('/api/teachers')
    assert response.status_code == 403

    # Students cannot create anything
    response = client.post('/api/sections', json={'name': 'TEST'})
    assert response.status_code == 403

def test_dashboard_stats(client, admin_user):
    """Test dashboard statistics endpoint"""
    # Login as admin
    login_user(client, 'admin', 'password')

    response = client.get('/api/dashboard/stats')
    assert response.status_code == 200
    data = json.loads(response.data)

    # Check required fields
    required_fields = [
        'total_teachers', 'total_students', 'total_sections',
        'total_subjects', 'total_classrooms', 'scheduled_periods',
        'available_slots'
    ]
    for field in required_fields:
        assert field in data

def test_timetable_viewing_permissions(client, student_user, sample_data):
    """Test timetable viewing permissions"""
    from app.models import db

    # Login as student
    login_user(client, 'student1', 'password')

    # Student should be able to view their own section's timetable
    section_id = student_user.student.section_id
    response = client.get(f'/api/timetable/section/{section_id}')
    assert response.status_code == 200

    # Student should not be able to view other sections
    # (We'd need another section for this test)
    response = client.get('/api/timetable/section/999')
    assert response.status_code == 404  # or 403 if section exists but access denied

def test_invalid_endpoints(client, admin_user):
    """Test invalid API endpoints"""
    login_user(client, 'admin', 'password')

    # Non-existent endpoint
    response = client.get('/api/nonexistent')
    assert response.status_code == 404

    # Invalid resource ID
    response = client.get('/api/teachers/999999')
    assert response.status_code == 404

def test_missing_authentication(client):
    """Test endpoints without authentication"""
    # Try to access protected endpoint without login
    response = client.get('/api/teachers')
    assert response.status_code == 401

def test_malformed_requests(client, admin_user):
    """Test malformed API requests"""
    login_user(client, 'admin', 'password')

    # Missing required fields
    response = client.post('/api/subjects', json={'name': 'Test'})  # Missing required fields
    assert response.status_code == 400 or response.status_code == 500

    # Invalid JSON
    response = client.post('/api/subjects',
                         data='invalid json',
                         headers={'Content-Type': 'application/json'})
    assert response.status_code == 400