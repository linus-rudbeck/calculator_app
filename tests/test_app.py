import pytest
from app import create_app, db
from app.models import User, Calculation
from werkzeug.security import generate_password_hash

@pytest.fixture
def test_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def create_user(username, password):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user

def test_register_user(test_client):
    response = test_client.post('/register', data={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 302  # Redirect efter registrering
    assert User.query.filter_by(username='testuser').first() is not None

def test_login_user(test_client):
    create_user('testuser', 'password123')
    response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 302  # Redirect efter inloggning
    assert 'Välkommen'.encode('utf-8') in test_client.get('/calculator').data

def test_calculator_save(test_client):
    user = create_user('testuser', 'password123')
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    response = test_client.post('/calculator', data={
        'expression': '2+2'
    })
    assert response.status_code == 200
    calculation = Calculation.query.filter_by(expression='2+2', user_id=user.id).first()
    assert calculation is not None
    assert calculation.result == '4'

def test_calculator_invalid_expression(test_client):
    create_user('testuser', 'password123')
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    response = test_client.post('/calculator', data={
        'expression': 'invalid_expression'
    })
    assert '????' in response.data.decode('utf-8')
