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
import psutil
from config.config_reader import ConfigReader
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# import redis

load_dotenv()
logger = setup_logger(__name__)

app = Flask(__name__)

CORS(app)  
config_reader = ConfigReader()

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

# Thread pool configuration
MAX_WORKERS = config_reader.get_or_default_int("MAX_WORKERS", 10)
request_queue = queue.Queue()
thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

MAX_DELETE_LIMIT = config_reader.get_or_default_int("MAX_DELETE_LIMIT", 10)
TIME_DIFFERENCE = config_reader.get_or_default_int("TIME_DIFFERENCE", 10)
SCHEDULER_INTERVAL = config_reader.get_or_default_int("SCHEDULER_INTERVAL", 10)

def process_chat_request(data, session_id):
    """Process a single chat request in a separate thread"""
    try:
        user_message = data.get('message', '').strip()
        model_choice = data.get('model', 'gemini-pro')
        
        if session_id is None or session_id == "null":
            session_id = os.urandom(16).hex()
            session_title = "Untitled session"
            sessions_collection.insert_one({
                "session_id": session_id,
                "title": session_title,
                "created_at": datetime.utcnow()
            })
            logger.info(f"Created new session with ID: {session_id}")
        else:
            session = sessions_collection.find_one({"session_id": session_id})
            if not session:
                logger.error(f"Invalid session ID: {session_id}")
                return {"error": "Invalid session ID"}, 400
            session_title = session.get("title", "Untitled session")

        if not user_message:
            logger.info(f"Empty message received for session {session_id}")
            return {"session_id": session_id}, 200

        # Store user message
        user_msg = {
            "session_id": session_id,
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow()
        }
        chat_collection.insert_one(user_msg)
        logger.info(f"Stored user message for session {session_id}")

        try:
            # Process with Borg
            borg = Borg()
            graph_response = borg.execute(user_message, "abcd", "abab")
            logger.info(f"Generated response for session {session_id}: {graph_response}")
        except Exception as e:
            logger.error(f"Error in Borg execution: {str(e)}")
            return {"error": "Failed to generate response"}, 500

        # Store bot response
        bot_msg = {
            "session_id": session_id,
            "role": "bot",
            "content": graph_response,
            "timestamp": datetime.utcnow()
        }
        chat_collection.insert_one(bot_msg)
        logger.info(f"Stored bot response for session {session_id}")

        # Update session title if needed
        max_length = 20
        truncated_message = user_message[:max_length] + "..." if len(user_message) > max_length else user_message
        if session_title == "Untitled session":
            sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"title": truncated_message}}
            )
            logger.info(f"Updated session title for {session_id}")

        return {"content": graph_response, "session_id": session_id}, 200

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return {"error": "An error occurred while processing your request"}, 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/sessions', methods=['GET'])
def get_sessions():
    try:
        # Retrieve all sessions with their titles from MongoDB
        sessions = list(sessions_collection.find({}, {"_id": 0, "session_id": 1, "title": 1}))
        return jsonify(sessions)
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        return jsonify({"error": "Failed to fetch sessions"}), 500
    
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
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No data provided"}), 400
            
        session_id = request.headers.get("Session-ID", None)
        logger.info(f"Received request for session {session_id}")
        
        # Submit the request to the thread pool
        future = thread_pool.submit(process_chat_request, data, session_id)
        
        # Wait for the result with a timeout
        try:
            result, status_code = future.result(timeout=70)  # 70 second timeout
            logger.info(f"Request completed with status {status_code}")
            
            # Ensure we have a valid response
            if not result:
                logger.error("Empty result received from process_chat_request")
                return jsonify({"error": "No response generated"}), 500
                
            # Log the response for debugging
            logger.info(f"Sending response: {result}")
            
            # Return the response directly since it's already in the correct format
            return jsonify(result), status_code
            
        except TimeoutError:
            logger.error("Request timed out")
            return jsonify({"error": "Request timed out"}), 504
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def delete_old_chats():
    cpu_before = psutil.cpu_percent(interval=1)
    
    # Calculate the time threshold for old chats and sessions
    time_difference = datetime.utcnow() - timedelta(minutes=TIME_DIFFERENCE)

    # Delete old chat messages
    old_message_count = chat_collection.count_documents({"timestamp": {"$lt": time_difference}})
    if old_message_count > 0:
        old_messages = chat_collection.find({"timestamp": {"$lt": time_difference}}).limit(MAX_DELETE_LIMIT)
        message_ids = [msg["_id"] for msg in old_messages]
        
        result = chat_collection.delete_many({"_id": {"$in": message_ids}})
        logger.info(f"Deleted {result.deleted_count} old chat messages.")

    # Delete old sessions
    old_session_count = sessions_collection.count_documents({"created_at": {"$lt": time_difference}})
    if old_session_count > 0:
        old_sessions = sessions_collection.find({"created_at": {"$lt": time_difference}}).limit(MAX_DELETE_LIMIT)
        session_ids = [session["session_id"] for session in old_sessions]
        
        # Delete sessions and their associated chat history
        sessions_collection.delete_many({"session_id": {"$in": session_ids}})
        chat_collection.delete_many({"session_id": {"$in": session_ids}})
        logger.info(f"Deleted {len(session_ids)} old sessions and their associated chat history.")

    cpu_after = psutil.cpu_percent(interval=1)
    logger.info(f"CPU Usage Before Deletion: {cpu_before}%")
    logger.info(f"CPU Usage After Deletion: {cpu_after}%")

# Run Scheduler in a Background Thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  


schedule.every(SCHEDULER_INTERVAL).minutes.do(delete_old_chats)

# Start scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Cleanup function to be called when the application shuts down
def cleanup():
    thread_pool.shutdown(wait=True)
    mongo_client.close()

# Register cleanup function
import atexit
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

