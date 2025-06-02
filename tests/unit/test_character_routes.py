"""Unit tests for character routes."""
import pytest
from unittest.mock import MagicMock, patch
from app.game.unified_models import CharacterTemplateModel, BaseStatsModel, ProficienciesModel
from app.repositories.character_template_repository import CharacterTemplateMetadata


@pytest.fixture
def client():
    """Create a test client."""
    from run import create_app
    
    app = create_app({
        'GAME_STATE_REPO_TYPE': 'memory',
        'TTS_PROVIDER': 'disabled',
        'RAG_ENABLED': False,
        'TESTING': True
    })
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_character_template():
    """Create a mock character template."""
    return CharacterTemplateModel(
        id="test-template-1",
        name="Test Character",
        race="Human",
        char_class="Fighter",
        level=1,
        alignment="Neutral Good",
        background="Soldier",
        base_stats=BaseStatsModel(
            STR=15,
            DEX=14,
            CON=13,
            INT=12,
            WIS=10,
            CHA=8
        ),
        proficiencies=ProficienciesModel(
            skills=["Athletics", "Intimidation"],
            armor=["Light", "Medium", "Heavy", "Shields"],
            weapons=["Simple", "Martial"],
            tools=[],
            saving_throws=["Strength", "Constitution"]
        ),
        languages=["Common", "Orcish"],
        racial_traits=[],
        class_features=[],
        feats=[],
        spells_known=[],
        cantrips_known=[],
        starting_equipment=[],
        starting_gold=100,
        personality_traits=["I am always polite"],
        ideals=["Honor"],
        bonds=["My weapon is my life"],
        flaws=["I am too trusting"]
    )


def test_get_character_templates(client, mock_character_template):
    """Test getting all character templates."""
    # Create metadata object that get_all_templates returns
    mock_metadata = CharacterTemplateMetadata(
        id="test-template-1",
        name="Test Character",
        race="Human",
        char_class="Fighter",
        level=1,
        description="A test character template",
        file="test-template-1.json",
        portrait_path=None
    )
    
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get_all_templates.return_value = [mock_metadata]
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.get('/api/character_templates')
        
    assert response.status_code == 200
    data = response.get_json()
    assert 'templates' in data
    assert len(data['templates']) == 1
    assert data['templates'][0]['name'] == 'Test Character'


def test_get_character_template_by_id(client, mock_character_template):
    """Test getting a specific character template."""
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get_template.return_value = mock_character_template
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.get('/api/character_templates/test-template-1')
        
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Test Character'
    assert data['id'] == 'test-template-1'


def test_get_character_template_not_found(client):
    """Test getting a non-existent character template."""
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get_template.return_value = None
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.get('/api/character_templates/non-existent')
        
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_create_character_template(client):
    """Test creating a new character template."""
    template_data = {
        "name": "New Character",
        "race": "Elf",
        "char_class": "Wizard",
        "level": 1,
        "alignment": "Chaotic Good",
        "background": "Sage",
        "base_stats": {
            "STR": 8,
            "DEX": 14,
            "CON": 12,
            "INT": 16,
            "WIS": 13,
            "CHA": 10
        },
        "skill_proficiencies": ["Arcana", "History"],
        "languages": ["Common", "Elvish", "Draconic"]
    }
    
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.save_template.return_value = True
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.post('/api/character_templates', json=template_data)
        
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New Character'
    assert data['race'] == 'Elf'
    assert data['char_class'] == 'Wizard'


def test_update_character_template(client, mock_character_template):
    """Test updating an existing character template."""
    update_data = {
        "name": "Updated Character",
        "race": "Half-Elf",
        "char_class": "Paladin",
        "level": 2,
        "alignment": "Lawful Good",
        "background": "Noble",
        "base_stats": {
            "STR": 16,
            "DEX": 12,
            "CON": 14,
            "INT": 10,
            "WIS": 13,
            "CHA": 15
        },
        "skill_proficiencies": ["Athletics", "Persuasion"],
        "languages": ["Common", "Elvish"]
    }
    
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get_template.return_value = mock_character_template
        mock_repo.save_template.return_value = True
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.put('/api/character_templates/test-template-1', json=update_data)
        
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Character'
    assert data['race'] == 'Half-Elf'
    assert data['char_class'] == 'Paladin'
    assert data['level'] == 2


def test_update_character_template_not_found(client):
    """Test updating a non-existent character template."""
    update_data = {"name": "Updated Character"}
    
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get_template.return_value = None
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.put('/api/character_templates/non-existent', json=update_data)
        
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'not found' in data['error']


def test_update_character_template_no_data(client, mock_character_template):
    """Test updating character template with no data."""
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get_template.return_value = mock_character_template
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.put('/api/character_templates/test-template-1', 
                             data='',
                             content_type='application/json')
        
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'No template data provided' in data['error']


def test_delete_character_template(client):
    """Test deleting a character template."""
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.delete_template.return_value = True
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.delete('/api/character_templates/test-template-1')
        
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'deleted successfully' in data['message']


def test_delete_character_template_failure(client):
    """Test failing to delete a character template."""
    with patch('app.routes.character_routes.get_container') as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.delete_template.return_value = False
        
        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container
        
        response = client.delete('/api/character_templates/test-template-1')
        
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data