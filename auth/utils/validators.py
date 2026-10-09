from typing import Any, Dict
from pydantic import BaseModel, ValidationError


def validate_request_body(data: Dict[str, Any], schema: BaseModel) -> Tuple[bool, Any, str]:
    """Validate request body against a Pydantic schema.
    
    Args:
        data: Request data dictionary.
        schema: Pydantic schema class.
        
    Returns:
        Tuple[bool, Any, str]: (is_valid, validated_data, error_message)
    """
    try:
        validated = schema(**data)
        return True, validated, ""
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        return False, None, "; ".join(error_messages)
