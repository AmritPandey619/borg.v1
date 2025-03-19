import argparse
from pymilvus import MilvusClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get Milvus connection details from .env
MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", 19530))
MILVUS_USER = os.getenv("MILVUS_USER", "default_user")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "default_password")

# Initialize Milvus client
client = MilvusClient(uri=MILVUS_URI, port=MILVUS_PORT, user=MILVUS_USER, password=MILVUS_PASSWORD)

def list_databases():
    """List all databases in Milvus."""
    print("Databases:", client.list_databases())

def list_collections(database_name):
    """List all collections in a specific database."""
    client.using_database(database_name)
    print(f"Collections in database '{database_name}':", client.list_collections())

def drop_collection(database_name, collection_name):
    """Drop a collection from a specific database."""
    client.using_database(database_name)
    client.drop_collection(collection_name)
    print(f"Collection '{collection_name}' dropped from database '{database_name}'.")

def drop_database(database_name):
    """Drop a database."""
    client.drop_database(database_name)
    print(f"Database '{database_name}' dropped.")

def create_user(user_name, password):
    """Create a user with a specified password."""
    client.create_user(user_name=user_name, password=password)
    print(f"User '{user_name}' created.")

def main():
    parser = argparse.ArgumentParser(description="Milvus Management Script")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List databases
    subparsers.add_parser("list_databases", help="List all databases")

    # List collections
    list_collections_parser = subparsers.add_parser("list_collections", help="List all collections in a database")
    list_collections_parser.add_argument("database_name", help="Name of the database")

    # Drop collection
    drop_collection_parser = subparsers.add_parser("drop_collection", help="Drop a collection from a database")
    drop_collection_parser.add_argument("database_name", help="Name of the database")
    drop_collection_parser.add_argument("collection_name", help="Name of the collection")

    # Drop database
    drop_database_parser = subparsers.add_parser("drop_database", help="Drop a database")
    drop_database_parser.add_argument("database_name", help="Name of the database")

    # Create user
    create_user_parser = subparsers.add_parser("create_user", help="Create a user with a password")
    create_user_parser.add_argument("user_name", help="Name of the user to create")
    create_user_parser.add_argument("password", help="Password for the user")

    args = parser.parse_args()

    try:
        if args.command == "list_databases":
            list_databases()
        elif args.command == "list_collections":
            list_collections(args.database_name)
        elif args.command == "drop_collection":
            drop_collection(args.database_name, args.collection_name)
        elif args.command == "drop_database":
            drop_database(args.database_name)
        elif args.command == "create_user":
            create_user(args.user_name, args.password)
        else:
            parser.print_help()
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
