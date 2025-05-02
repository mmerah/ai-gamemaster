import os
from app import create_app # Import the app factory function

# Load configuration to determine host/port if needed, otherwise use defaults
# Example: config_name = os.getenv('FLASK_CONFIG') or 'default'

app = create_app() # Create the Flask app instance using the factory

if __name__ == '__main__':
    # Debug mode will be enabled based on FLASK_DEBUG in .env via app.config
    app.run(host='127.0.0.1', port=5000)