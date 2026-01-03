"""
MongoDB connection handler for Job Aggregator.
"""

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Global connection instance
_client: Optional[MongoClient] = None
_database: Optional[Database] = None


class DatabaseConnection:
    """MongoDB connection manager."""
    
    def __init__(self, uri: str, database_name: str = 'job_aggregator'):
        """
        Initialize database connection.
        
        Args:
            uri: MongoDB connection URI
            database_name: Name of the database to use
        """
        self.uri = uri
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
    
    def connect(self) -> Database:
        """
        Establish connection to MongoDB.
        
        Returns:
            Database instance
        
        Raises:
            ConnectionFailure: If connection fails
        """
        global _client, _database
        
        if _database is not None:
            return _database
        
        try:
            print(f"🔌 Connecting to MongoDB...")
            
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                retryWrites=True,
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.database_name]
            
            # Store globally for reuse
            _client = self.client
            _database = self.db
            
            print(f"   ✓ Connected to MongoDB database: {self.database_name}")
            return self.db
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"   ❌ Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Close the database connection."""
        global _client, _database
        
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            _client = None
            _database = None
            print("🔌 Disconnected from MongoDB")
    
    def get_collection(self, name: str):
        """Get a collection from the database."""
        if self.db is None:
            self.connect()
        return self.db[name]
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        if self.client is None:
            return False
        
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def get_database() -> Optional[Database]:
    """Get the current database instance."""
    return _database


def init_database(uri: str, database_name: str = 'job_aggregator') -> Database:
    """
    Initialize and return database connection.
    
    Args:
        uri: MongoDB connection URI
        database_name: Database name
    
    Returns:
        Database instance
    """
    conn = DatabaseConnection(uri, database_name)
    return conn.connect()


