from flask import Flask,  render_template, request, jsonify
from flask_cors import CORS
# import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from borg import Borg
from utils.logger import setup_logger
# from flask_session import Session
import schedule
import time
import threading
from pymongo import MongoClient
from datetime import datetime, timedelta

# import redis

load_dotenv()
logger = setup_logger(__name__)

app = Flask(__name__)
CORS(app)  

logging.basicConfig(level=logging.INFO)

#GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#if not GEMINI_API_KEY:
 #   raise ValueError("GEMINI_API_KEY not found in environment variables")

#genai.configure(api_key=GEMINI_API_KEY)
#model = genai.GenerativeModel('gemini-pro')

# app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecretkey")  # Secret key for session management
# app.config['SESSION_TYPE'] = 'redis'  # Use Redis for session storage
# app.config['SESSION_PERMANENT'] = True
# app.config['SESSION_USE_SIGNER'] = True  # Secure cookies
# app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')  # Redis connection URL
# Session(app)

# Configure MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://amritpandey610:3rSmW2J5DRlxYyHv@cluster0.6dv6j.mongodb.net/")  # MongoDB connection URI
mongo_client = MongoClient(mongo_uri)
db = mongo_client["chat_db"]  # Database name
chat_collection = db["chat_history"] 
sessions_collection = db["sessions"]

# @app.before_request
# def assign_session():
#     if 'session_id' not in session:
#         session['session_id'] = str(uuid.uuid4())  # Generate a unique session ID
#         session.modified = True


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/history', methods=['GET'])
def get_chat_history():
    try:
        session_id = request.headers.get("Session-ID")
        if not session_id:
            return jsonify([])  # Return empty list if no session ID

        # Retrieve chat history from MongoDB
        chat_history = list(chat_collection.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1))
        # print(f"Chat history for session {session_id}: {chat_history}")
        return jsonify(chat_history)
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

@app.route('/generate', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        session_id = request.headers.get("Session-ID", None)
        a=session_id
        user_message = data.get('message', '').strip()
        model_choice = data.get('model', 'gemini-pro')
        
        if not user_message:
            return jsonify({"error": "Empty message received"}), 400
        
        if session_id==None or session_id=="null":
            session_id = os.urandom(16).hex()
            

        user_msg = {
            "session_id": session_id,
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow()
        }
        chat_collection.insert_one(user_msg)

        borg = Borg()
        graph_response = borg.execute(user_message,"abcd","abab")
 
        logger.info("Final response: %s", graph_response)
        print("Session",type(a))
        bot_msg = {
            "session_id": session_id,
            "role": "bot",
            "content": graph_response,
            "timestamp": datetime.utcnow()
        }
        chat_collection.insert_one(bot_msg)

        return jsonify({"content":graph_response, "session_id": session_id})
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({
            "error": "An error occurred while processing your request"
        }), 500

def delete_old_chats():
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = chat_collection.delete_many({"timestamp": {"$lt": one_hour_ago}})
    print(f"Deleted {result.deleted_count} old messages.")

# Run Scheduler in a Background Thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  

schedule.every(3).minutes.do(delete_old_chats)

# Start scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

