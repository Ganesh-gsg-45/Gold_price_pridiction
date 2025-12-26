"""
Helper utilities for the Gold Price Predictor application
"""

from functools import wraps
from typing import Callable, Any
from flask import jsonify

def handle_errors(f: Callable) -> Callable:
    """
    Decorator to handle API errors gracefully.

    Args:
        f: The function to wrap with error handling

    Returns:
        The wrapped function that catches exceptions and returns JSON error responses
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'details': str(e)
            }), 500
    return decorated
