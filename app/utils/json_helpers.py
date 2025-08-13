"""
JSON serialization helpers for PostgreSQL JSON fields
"""
import json
from typing import Dict, Any, List, Optional, Union


def serialize_json_fields(data: Dict[str, Any], json_fields: List[str]) -> Dict[str, Any]:
    """
    Convert Python dict/list fields to JSON strings for PostgreSQL storage.
    
    Args:
        data: Dictionary containing the data to process
        json_fields: List of field names that should be JSON serialized
    
    Returns:
        Modified dictionary with JSON fields serialized to strings
    """
    for field in json_fields:
        if field in data:
            value = data.get(field)
            if value is None:
                data[field] = '{}'  # Default empty JSON object
            elif isinstance(value, (dict, list)):
                data[field] = json.dumps(value)
            elif isinstance(value, str):
                # Already a string, validate it's valid JSON
                try:
                    json.loads(value)
                    data[field] = value
                except json.JSONDecodeError:
                    # Invalid JSON string, wrap in empty object
                    data[field] = '{}'
            else:
                # Other types, convert to empty object
                data[field] = '{}'
    
    return data


def ensure_json_fields(data: Dict[str, Any], json_fields: List[str]) -> Dict[str, Any]:
    """
    Ensure JSON fields exist with at least empty JSON objects.
    Used before inserting new records.
    
    Args:
        data: Dictionary containing the data to process
        json_fields: List of field names that should have JSON values
    
    Returns:
        Modified dictionary with JSON fields guaranteed to exist
    """
    for field in json_fields:
        if field not in data or data.get(field) is None:
            data[field] = '{}'
        elif isinstance(data[field], (dict, list)):
            data[field] = json.dumps(data[field])
    
    return data


def deserialize_json_fields(row: Any, json_fields: List[str]) -> Dict[str, Any]:
    """
    Convert a database row to a dictionary and parse JSON fields.
    
    Args:
        row: Database row object
        json_fields: List of field names that contain JSON data
    
    Returns:
        Dictionary with JSON fields parsed to Python objects
    """
    # Convert row to dict
    if hasattr(row, '_mapping'):
        result = dict(row._mapping)
    elif hasattr(row, '__dict__'):
        result = row.__dict__.copy()
    else:
        result = dict(row)
    
    # Parse JSON fields
    for field in json_fields:
        if field in result and result[field]:
            if isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = {}
            elif result[field] is None:
                result[field] = {}
    
    return result


# Common JSON fields across different models
SHOW_JSON_FIELDS = ['social_links', 'api_keys', 'settings']
ORGANIZATION_JSON_FIELDS = ['settings']
SEGMENT_JSON_FIELDS = ['metadata', 'settings']
EPISODE_JSON_FIELDS = ['metadata', 'settings']
USER_JSON_FIELDS = ['preferences', 'settings']