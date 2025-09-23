# tests/test_app.py
import pytest
import tempfile
import os
from app import app

@pytest.fixture
def client():
    # Crear una base de datos temporal para tests
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            # Aquí podrías inicializar la DB de test si fuera necesario
            pass
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def test_homepage(client):
    """Test que la página principal carga correctamente"""
    rv = client.get('/')
    assert rv.status_code == 200

def test_dashboard_redirect(client):
    """Test que el dashboard está disponible"""
    rv = client.get('/dashboard')
    # Debe redirigir o mostrar contenido (dependiendo de tu auth)
    assert rv.status_code in [200, 302]

def test_api_health(client):
    """Test básico de API"""
    rv = client.get('/api/health')  # Si tienes un endpoint de health
    # Si no tienes health endpoint, puedes probar otro
    if rv.status_code == 404:
        assert True  # Endpoint no existe, pero app funciona
    else:
        assert rv.status_code == 200
