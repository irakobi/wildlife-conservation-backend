"""
Kobo Toolbox form parser utility
Converts Kobo form structures into mobile-friendly format
"""

import json
from typing import Dict, List, Any, Optional


class KoboFormParser:
    """Parser for Kobo form structures"""
    
    @staticmethod
    def parse_form_content(form_data: Dict) -> Dict[str, Any]:
        """
        Parse Kobo form structure into mobile-friendly format
        
        Args:
            form_data: Raw form data from Kobo API
            
        Returns:
            Simplified form structure for mobile app consumption
        """
        try:
            content = form_data.get('content', {})
            survey = content.get('survey', [])
            choices = content.get('choices', [])
            
            # Build choices lookup for select questions
            choices_map = {}
            for choice in choices:
                list_name = choice.get('list_name', '')
                if list_name not in choices_map:
                    choices_map[list_name] = []
                choices_map[list_name].append({
                    'name': choice.get('name', ''),
                    'label': KoboFormParser._get_label(choice)
                })
            
            # Parse survey questions
            questions = []
            for item in survey:
                question = KoboFormParser._parse_question(item, choices_map)
                if question:
                    questions.append(question)
            
            return {
                'form_id': form_data.get('uid', ''),
                'form_name': form_data.get('name', ''),
                'form_title': KoboFormParser._get_label(content.get('settings', {})),
                'questions': questions,
                'submission_url': f"/api/v1/submissions/",
                'created_at': form_data.get('date_created'),
                'modified_at': form_data.get('date_modified'),
                'deployment_status': form_data.get('deployment__active', False),
                'owner': form_data.get('owner__username', ''),
                'permissions': form_data.get('permissions', [])
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing form: {e}")
    
    @staticmethod
    def _parse_question(item: Dict, choices_map: Dict) -> Optional[Dict]:
        """Parse individual question from Kobo survey"""
        question_type = item.get('type', '')
        
        # Skip groups and notes for now (can be enhanced later)
        if question_type in ['begin_group', 'end_group', 'note', 'start', 'end']:
            return None
        
        question = {
            'name': item.get('name', ''),
            'label': KoboFormParser._get_label(item),
            'type': KoboFormParser._map_question_type(question_type),
            'required': item.get('required', False),
            'hint': KoboFormParser._get_hint(item),
            'constraint': item.get('constraint'),
            'constraint_message': KoboFormParser._get_label(item.get('constraint_message', {})),
            'relevant': item.get('relevant'),
            'default': item.get('default'),
            'readonly': item.get('readonly', False),
            'appearance': item.get('appearance', '')
        }
        
        # Add choices for select questions
        if question_type.startswith('select_'):
            choice_list = item.get('select_from_list_name', '')
            if choice_list in choices_map:
                question['choices'] = choices_map[choice_list]
                question['allow_other'] = 'other' in item.get('appearance', '')
        
        # Add specific attributes for different question types
        if question_type == 'integer':
            question['min_value'] = item.get('constraint', {}).get('min')
            question['max_value'] = item.get('constraint', {}).get('max')
        elif question_type == 'decimal':
            question['decimal_places'] = item.get('bind', {}).get('jr:constraintMsg', {}).get('decimal_places')
        elif question_type == 'text':
            question['max_length'] = item.get('bind', {}).get('jr:constraintMsg', {}).get('max_length')
        elif question_type == 'geopoint':
            question['accuracy_threshold'] = item.get('bind', {}).get('jr:preload', {}).get('accuracy')
        
        return question
    
    @staticmethod
    def _map_question_type(kobo_type: str) -> str:
        """Map Kobo question types to mobile app types"""
        type_mapping = {
            'text': 'text',
            'integer': 'number',
            'decimal': 'decimal',
            'date': 'date',
            'datetime': 'datetime',
            'time': 'time',
            'select_one': 'single_choice',
            'select_multiple': 'multiple_choice',
            'geopoint': 'location',
            'geotrace': 'line',
            'geoshape': 'area',
            'image': 'photo',
            'audio': 'audio',
            'video': 'video',
            'file': 'file',
            'barcode': 'barcode',
            'calculate': 'calculated',
            'acknowledge': 'acknowledge',
            'range': 'range'
        }
        return type_mapping.get(kobo_type, 'text')
    
    @staticmethod
    def _get_label(item: Dict) -> str:
        """Extract label from Kobo item (handles multiple languages)"""
        if not item:
            return ''
            
        label = item.get('label', '') if isinstance(item, dict) else item
        
        if isinstance(label, dict):
            # Multiple languages - get English first, then default, then first available
            return (label.get('English') or 
                   label.get('english') or 
                   label.get('default') or 
                   list(label.values())[0] if label else '')
        return str(label) if label else ''
    
    @staticmethod
    def _get_hint(item: Dict) -> str:
        """Extract hint/help text from Kobo item"""
        hint = item.get('hint', '')
        if isinstance(hint, dict):
            return (hint.get('English') or 
                   hint.get('english') or 
                   hint.get('default') or 
                   list(hint.values())[0] if hint else '')
        return str(hint) if hint else ''
    
    @staticmethod
    def parse_submission_data(submission_data: Dict, form_structure: Dict) -> Dict[str, Any]:
        """
        Parse submission data according to form structure
        
        Args:
            submission_data: Raw submission data
            form_structure: Parsed form structure
            
        Returns:
            Cleaned and validated submission data
        """
        parsed_data = {}
        questions_map = {q['name']: q for q in form_structure.get('questions', [])}
        
        for field_name, field_value in submission_data.items():
            # Skip system fields
            if field_name.startswith('_') or field_name.startswith('meta/'):
                continue
            
            question = questions_map.get(field_name)
            if not question:
                # Include unknown fields as-is
                parsed_data[field_name] = field_value
                continue
            
            # Parse based on question type
            question_type = question.get('type', 'text')
            parsed_data[field_name] = KoboFormParser._parse_field_value(
                field_value, question_type, question
            )
        
        return parsed_data
    
    @staticmethod
    def _parse_field_value(value: Any, question_type: str, question: Dict) -> Any:
        """Parse individual field value based on question type"""
        if value is None or value == '':
            return None
        
        try:
            if question_type == 'number':
                return int(value) if isinstance(value, (str, float)) else value
            elif question_type == 'decimal':
                return float(value) if isinstance(value, (str, int)) else value
            elif question_type == 'multiple_choice':
                # Handle space-separated multiple choice values
                if isinstance(value, str):
                    return [v.strip() for v in value.split() if v.strip()]
                return value if isinstance(value, list) else [value]
            elif question_type == 'location':
                # Parse GPS coordinates
                if isinstance(value, str):
                    coords = value.split()
                    if len(coords) >= 2:
                        return {
                            'latitude': float(coords[0]),
                            'longitude': float(coords[1]),
                            'altitude': float(coords[2]) if len(coords) > 2 else None,
                            'accuracy': float(coords[3]) if len(coords) > 3 else None
                        }
                return value
            elif question_type in ['date', 'datetime']:
                # Keep date/datetime as string for now
                return str(value)
            else:
                return str(value)
        except (ValueError, TypeError, IndexError):
            # If parsing fails, return original value
            return value
    
    @staticmethod
    def validate_submission_data(submission_data: Dict, form_structure: Dict) -> Dict[str, List[str]]:
        """
        Validate submission data against form structure
        
        Args:
            submission_data: Submission data to validate
            form_structure: Form structure for validation
            
        Returns:
            Dictionary of field names with validation errors
        """
        errors = {}
        questions_map = {q['name']: q for q in form_structure.get('questions', [])}
        
        for question in form_structure.get('questions', []):
            field_name = question['name']
            field_value = submission_data.get(field_name)
            field_errors = []
            
            # Check required fields
            if question.get('required', False) and (field_value is None or field_value == ''):
                field_errors.append(f"{question.get('label', field_name)} is required")
            
            # Type-specific validation
            if field_value is not None and field_value != '':
                question_type = question.get('type', 'text')
                
                if question_type == 'number':
                    try:
                        int(field_value)
                    except (ValueError, TypeError):
                        field_errors.append(f"{question.get('label', field_name)} must be a number")
                
                elif question_type == 'decimal':
                    try:
                        float(field_value)
                    except (ValueError, TypeError):
                        field_errors.append(f"{question.get('label', field_name)} must be a decimal number")
                
                elif question_type in ['single_choice', 'multiple_choice']:
                    choices = question.get('choices', [])
                    valid_choices = [choice['name'] for choice in choices]
                    
                    if question_type == 'single_choice':
                        if field_value not in valid_choices:
                            field_errors.append(f"Invalid choice for {question.get('label', field_name)}")
                    else:  # multiple_choice
                        selected_values = field_value if isinstance(field_value, list) else [field_value]
                        for selected in selected_values:
                            if selected not in valid_choices:
                                field_errors.append(f"Invalid choice '{selected}' for {question.get('label', field_name)}")
            
            if field_errors:
                errors[field_name] = field_errors
        
        return errors
    
    @staticmethod
    def get_form_summary(form_structure: Dict) -> Dict[str, Any]:
        """
        Get summary information about a form
        
        Args:
            form_structure: Parsed form structure
            
        Returns:
            Form summary with statistics
        """
        questions = form_structure.get('questions', [])
        
        question_types = {}
        required_count = 0
        choice_questions = 0
        
        for question in questions:
            q_type = question.get('type', 'text')
            question_types[q_type] = question_types.get(q_type, 0) + 1
            
            if question.get('required', False):
                required_count += 1
            
            if q_type in ['single_choice', 'multiple_choice']:
                choice_questions += 1
        
        return {
            'form_id': form_structure.get('form_id', ''),
            'form_name': form_structure.get('form_name', ''),
            'total_questions': len(questions),
            'required_questions': required_count,
            'optional_questions': len(questions) - required_count,
            'choice_questions': choice_questions,
            'question_types': question_types,
            'has_location': 'location' in question_types,
            'has_media': any(t in question_types for t in ['photo', 'audio', 'video']),
            'deployment_status': form_structure.get('deployment_status', False),
            'created_at': form_structure.get('created_at'),
            'modified_at': form_structure.get('modified_at')
        }


# Example usage and testing functions
def test_form_parsing():
    """Test the form parser with sample Kobo data"""
    sample_kobo_form = {
        "uid": "wildlife_survey_001",
        "name": "Wildlife Conflict Survey",
        "date_created": "2024-01-01T00:00:00Z",
        "date_modified": "2024-01-15T12:00:00Z",
        "deployment__active": True,
        "owner__username": "ranger@wildlife.org",
        "content": {
            "settings": {
                "form_title": "Human-Wildlife Conflict Report"
            },
            "survey": [
                {
                    "name": "incident_date",
                    "type": "date",
                    "label": "When did the incident occur?",
                    "required": True
                },
                {
                    "name": "location",
                    "type": "geopoint",
                    "label": "Location of incident",
                    "required": True
                },
                {
                    "name": "species",
                    "type": "select_one",
                    "label": "Which species was involved?",
                    "select_from_list_name": "species_list",
                    "required": True
                },
                {
                    "name": "incident_type",
                    "type": "select_multiple",
                    "label": "Type of conflict",
                    "select_from_list_name": "incident_types"
                },
                {
                    "name": "description",
                    "type": "text",
                    "label": "Describe the incident",
                    "hint": "Please provide as much detail as possible"
                },
                {
                    "name": "photo",
                    "type": "image",
                    "label": "Photo evidence (optional)"
                }
            ],
            "choices": [
                {
                    "list_name": "species_list",
                    "name": "elephant",
                    "label": "Elephant"
                },
                {
                    "list_name": "species_list",
                    "name": "lion",
                    "label": "Lion"
                },
                {
                    "list_name": "species_list",
                    "name": "hippo",
                    "label": "Hippopotamus"
                },
                {
                    "list_name": "incident_types",
                    "name": "crop_damage",
                    "label": "Crop damage"
                },
                {
                    "list_name": "incident_types",
                    "name": "livestock_attack",
                    "label": "Livestock attack"
                },
                {
                    "list_name": "incident_types",
                    "name": "human_injury",
                    "label": "Human injury"
                }
            ]
        }
    }
    
    parser = KoboFormParser()
    parsed_form = parser.parse_form_content(sample_kobo_form)
    
    print("Parsed Form Structure:")
    print(json.dumps(parsed_form, indent=2))
    
    # Test form summary
    summary = parser.get_form_summary(parsed_form)
    print("\nForm Summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    test_form_parsing()