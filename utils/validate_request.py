from flask import request, jsonify

def validate_request(schema_class):
    def decorator(func):
        def wrapper(*args, **kwargs):
            schema = schema_class()
            json_data = request.get_json()
            if not json_data:
                return jsonify({'error': 'Missing JSON body'}), 400
            errors = schema.validate(json_data)
            if errors:
                return jsonify({'errors': errors}), 400
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator