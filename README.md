# Milvus Management Script

This Python script provides a command-line interface to manage Milvus databases and collections. It allows you to list databases, list collections, drop collections, drop databases, and create users.

## Prerequisites

1. Python 3.7 or later.
2. Install the required Python packages:
```bash
pip install pymilvus python-dotenv
```
3. Create a .env file in the same directory as the script with the following content:
MILVUS_URI=http://10.76.144.114
MILVUS_PORT=19530
MILVUS_USER=ncc
MILVUS_PASSWORD=Passw0rd

## Usage
Run the script from the command line with the desired operation.

### Available Commands
1. List all databases
```bash
python milvus_manager.py list_databases
```

2. List collections in a database
python milvus_manager.py list_collections <database_name>
Example:
```bash
python milvus_manager.py list_collections apidocs
```

3. Drop a collection from a database
python milvus_manager.py drop_collection <database_name> <collection_name>
Example:
```bash
python milvus_manager.py drop_collection apidocs BUNDLE
```

4. Drop a database
python milvus_manager.py drop_database <database_name>
Example:
```bash
python milvus_manager.py drop_database apidocs
```

5. Create a user
python milvus_manager.py create_user <user_name> <password>
Example:
```bash
python milvus_manager.py create_user ncc Passw0rd
```

### Error Handling
If an error occurs during an operation, it will print an error message and provide details for troubleshooting.

## Security Notice
Do not hardcode sensitive information like passwords in the script.
Use the .env file to securely manage connection details.

##License


