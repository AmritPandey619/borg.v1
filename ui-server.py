from flask import Flask,  render_template, request, jsonify
from flask_socketio import SocketIO
#from llm_handler import generate_robot_test
from utils.logger import setup_logger
from borg import Borg


logger = setup_logger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    logger.info("Query from user")
    data = request.json
    logger.info("Query from user: %s", data)
    description = data.get("message", "")
    borg = Borg()
   # logger.info("Actual Query from user: %s", description)
    #cmd = "python /home/borg.v1/borg.py -q " +str(description)
    #logger.info("Command: %s", cmd)
    #os.system(cmd)  
    graph_response = borg.execute(description,"abcd","abab")
    logger.info("Final response: %s", graph_response)
    if not description:
        return jsonify({"error": "Description is required"}), 400
    

    logger.info(f"Sending response back to chat UI: {graph_response}")
   # socketio.emit('server_response', {'message': graph_response}) 
   # robot_test = generate_robot_test(description)
    return jsonify({"robot_test": graph_response})
   # return jsonify({"graph_response"})
    #return graph_response

@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, debug=True)
