"""
Helper utilities
"""

from functools import wraps
from flask import jsonify

def handle_errors(f):
    """Decorator to handle API errors"""
    @wraps(f)
    def decorated(*args, **kwargs):
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