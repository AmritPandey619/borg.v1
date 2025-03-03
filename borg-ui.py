from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, send
from flask_cors import CORS  # Add this import
import logging
from borg import Borg

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)  # Add this line
socketio = SocketIO(app, cors_allowed_origins="*")  # Update this line

# Mock data for "Bundle"
bundles = [
    {"name": "data", "type": "Data", "status": "DRAFT", "managed_elements": "N/A", "last_modified": "12/13/2024, 04:40 PM"}
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

borg = None

@app.route('/api/bundles', methods=['GET'])
def get_bundles():
    return jsonify(bundles)

@app.route('/')
def index():
    logger.info(f"Message received...")
    return render_template('index.html')

# WebSocket chat functionality
@socketio.on('message')
def handle_message(msg):
    logger.info(f"Message received from chat UI: {msg}")
    send(msg, broadcast=True)  # Echo user message
    # Invoke AI
    graph_response = borg.execute(msg, "data/create_bundle_default_config.yml",
                                  "data/create_bundle_json_payload.txt")
    #graph_response = borg.execute(msg, "data/create_user_default_config.yml",
    #                              "data/create_user_json_payload.txt")
    
    # Send AI response
    logger.info(f"Sending response back to chat UI: {graph_response}")
    socketio.emit('server_response', {'message': graph_response})

@socketio.on('button_click')
def handle_button_click(data):
    logger.debug("Button click event received")

@socketio.on('play_button_click')
def handle_play_button_click():
    logger.info("Play button clicked")

@socketio.on('edit_button_click')
def handle_edit_button_click():
    logger.info("Edit button clicked")

if __name__ == '__main__':
    logger.info("Starting server...")
    borg = Borg()
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')
