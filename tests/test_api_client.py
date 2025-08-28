"""
Tests for the GroupMe API client.
"""

import pytest
from unittest.mock import Mock, patch

from groupme_bot.utils.api_client import GroupMeConfig, GroupMeAPIClient


def test_groupme_config_validation():
    """Test GroupMeConfig validation."""
    # Valid config
    config = GroupMeConfig(api_key="test_key")
    assert config.api_key == "test_key"
    assert config.base_url == "https://api.groupme.com/v3"
    assert config.timeout == 30
    assert config.max_retries == 3
    
    # Test with custom values
    config = GroupMeConfig(
        api_key="test_key",
        timeout=60,
        max_retries=5,
        backoff_factor=0.5
    )
    assert config.timeout == 60
    assert config.max_retries == 5
    assert config.backoff_factor == 0.5


def test_api_client_creation():
    """Test API client creation."""
    config = GroupMeConfig(api_key="test_key")
    client = GroupMeAPIClient(config)
    
    assert client.config.api_key == "test_key"
    assert client.session is not None


@patch('groupme_bot.utils.api_client.requests.Session')
def test_api_client_make_request(mock_session):
    """Test API client request making."""
    config = GroupMeConfig(api_key="test_key")
    client = GroupMeAPIClient(config)
    
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "test"}
    mock_response.raise_for_status.return_value = None
    
    mock_session.return_value.request.return_value = mock_response
    
    # Test request
    response = client._make_request("GET", "groups")
    
    assert response.status_code == 200
    assert response.json() == {"response": "test"}
