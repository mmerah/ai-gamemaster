import os

from app import create_app  # Import the app factory function

# Load configuration to determine host/port if needed, otherwise use defaults
# Example: config_name = os.getenv('FLASK_CONFIG') or 'default'

# IMPORTANT: Do not create app at module level during testing
# This allows tests to mock services before app creation
if os.environ.get("TESTING") != "true":
    app = create_app()  # Create the Flask app instance using the factory

if __name__ == "__main__":
    # If not already created (e.g., during testing), create it now
    if "app" not in globals():
        app = create_app()
    # Debug mode will be enabled based on FLASK_DEBUG in .env via app.config
    app.run(host="127.0.0.1", port=5000)
