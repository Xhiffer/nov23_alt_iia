from flask import Flask
from routes.main import main  # correct import
from routes.alerts import alerts 
app = Flask(__name__)

# Register blueprint
app.register_blueprint(main)
app.register_blueprint(alerts)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5010)

