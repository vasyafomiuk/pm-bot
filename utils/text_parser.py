"""
Text parsing utilities for the Project Management Bot
"""

import re
from typing import Dict, List, Optional, Any


def parse_epic_from_text(text: str) -> Dict[str, Any]:
    """
    Parse epic details from structured text input
    
    Args:
        text: Raw text from user input
        
    Returns:
        Dictionary containing parsed epic data
    """
    epic_data = {}
    
    # Clean up the text
    text = text.strip()
    
    # Split into lines and process each line
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines or lines without colons
        if not line or ':' not in line:
            continue
        
        # Split on first colon only
        parts = line.split(':', 1)
        if len(parts) != 2:
            continue
        
        key = parts[0].strip().lower()
        value = parts[1].strip()
        
        # Parse different fields
        if key in ['title', 'name', 'epic title', 'epic name']:
            epic_data['title'] = value
        elif key in ['description', 'desc', 'summary']:
            epic_data['description'] = value
        elif key in ['features', 'feature', 'preferred features']:
            # Parse comma-separated features
            features = [f.strip() for f in value.split(',') if f.strip()]
            epic_data['preferred_features'] = features
        elif key in ['priority', 'prio']:
            # Normalize priority
            priority = normalize_priority(value)
            if priority:
                epic_data['priority'] = priority
        elif key in ['labels', 'label', 'tags', 'tag']:
            # Parse comma-separated labels
            labels = [l.strip() for l in value.split(',') if l.strip()]
            epic_data['labels'] = labels
    
    return epic_data


def normalize_priority(priority: str) -> Optional[str]:
    """
    Normalize priority string to standard values
    
    Args:
        priority: Raw priority string
        
    Returns:
        Normalized priority or None if invalid
    """
    if not priority:
        return None
    
    priority = priority.strip().lower()
    
    priority_mapping = {
        'low': 'Low',
        'l': 'Low',
        'minor': 'Low',
        'medium': 'Medium',
        'med': 'Medium',
        'm': 'Medium',
        'normal': 'Medium',
        'high': 'High',
        'h': 'High',
        'important': 'High',
        'critical': 'Critical',
        'crit': 'Critical',
        'urgent': 'Critical',
        'blocker': 'Critical'
    }
    
    return priority_mapping.get(priority, 'Medium')


def extract_jira_keys(text: str) -> List[str]:
    """
    Extract Jira issue keys from text
    
    Args:
        text: Text that may contain Jira keys
        
    Returns:
        List of found Jira keys
    """
    # Pattern for Jira keys (PROJECT-123 format)
    pattern = r'\b[A-Z][A-Z0-9_]*-\d+\b'
    return re.findall(pattern, text)


def format_feature_list(features: List[str]) -> str:
    """
    Format a list of features for display
    
    Args:
        features: List of feature strings
        
    Returns:
        Formatted feature list string
    """
    if not features:
        return "No features specified"
    
    formatted = []
    for i, feature in enumerate(features, 1):
        formatted.append(f"{i}. {feature}")
    
    return '\n'.join(formatted)


def clean_text_for_jira(text: str) -> str:
    """
    Clean text for Jira compatibility
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text suitable for Jira
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove or escape problematic characters
    text = text.replace('\r', '\n')
    
    # Limit length (Jira has field length limits)
    if len(text) > 32000:  # Jira description limit
        text = text[:32000] + "... [truncated]"
    
    return text


def parse_acceptance_criteria(text: str) -> List[str]:
    """
    Parse acceptance criteria from text
    
    Args:
        text: Text containing acceptance criteria
        
    Returns:
        List of acceptance criteria
    """
    criteria = []
    
    # Look for numbered or bulleted lists
    patterns = [
        r'^\d+\.\s*(.+)$',  # Numbered list (1. item)
        r'^[-*•]\s*(.+)$',  # Bullet list (- item, * item, • item)
        r'^AC\d*\s*[:-]\s*(.+)$',  # AC1: item or AC: item
    ]
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                criteria.append(match.group(1).strip())
                break
        else:
            # If no pattern matches but line is substantial, add it as is
            if len(line) > 10:
                criteria.append(line)
    
    return criteria[:10]  # Limit to 10 criteria


def validate_epic_data(epic_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate epic data and return validation errors
    
    Args:
        epic_data: Epic data dictionary
        
    Returns:
        Dictionary of validation errors (empty if valid)
    """
    errors = {}
    
    # Required fields
    if not epic_data.get('title'):
        errors['title'] = "Title is required"
    elif len(epic_data['title']) < 5:
        errors['title'] = "Title must be at least 5 characters long"
    elif len(epic_data['title']) > 200:
        errors['title'] = "Title must be less than 200 characters"
    
    if not epic_data.get('description'):
        errors['description'] = "Description is required"
    elif len(epic_data['description']) < 20:
        errors['description'] = "Description must be at least 20 characters long"
    
    # Optional field validation
    features = epic_data.get('preferred_features', [])
    if features and len(features) > 10:
        errors['features'] = "Maximum 10 features allowed"
    
    labels = epic_data.get('labels', [])
    if labels and len(labels) > 5:
        errors['labels'] = "Maximum 5 labels allowed"
    
    return errors


def format_validation_errors(errors: Dict[str, str]) -> str:
    """
    Format validation errors for display
    
    Args:
        errors: Dictionary of validation errors
        
    Returns:
        Formatted error message
    """
    if not errors:
        return ""
    
    formatted_errors = []
    for field, error in errors.items():
        formatted_errors.append(f"• {field.title()}: {error}")
    
    return "Validation errors:\n" + '\n'.join(formatted_errors) 