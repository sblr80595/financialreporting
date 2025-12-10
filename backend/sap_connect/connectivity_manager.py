"""
Connectivity Manager Module
Handles both SQL Server and API connections to SAP B1
Supports multiple entities with different connection types
"""

import json
import os
import pyodbc
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import urllib3

# Suppress SSL warnings for API connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ConnectivityManager:
    """
    Unified manager for handling SQL and API connections to SAP B1
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the connectivity manager
        
        Args:
            config_path: Path to the entities configuration file
        """
        if config_path is None:
            # Default to backend/config/sap_connect/entities.json
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "sap_connect", "entities.json")
        
        self.config_path = config_path
        self.config = self._load_config()
        self.session = None  # For API connections
        self.connection = None  # For SQL connections
        
    def _load_config(self) -> Dict:
        """Load entities configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_all_entities(self) -> List[Dict]:
        """Get list of all available entities"""
        api_entities = self.config['entities']['api_entities']
        sql_entities = self.config['entities']['sql_entities']
        return api_entities + sql_entities
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Dict]:
        """Get entity configuration by ID"""
        for entity in self.get_all_entities():
            if entity['id'] == entity_id:
                return entity
        return None
    
    def get_entities_by_type(self, connection_type: str) -> List[Dict]:
        """
        Get entities filtered by connection type
        
        Args:
            connection_type: 'api' or 'sql'
        """
        if connection_type == 'api':
            return self.config['entities']['api_entities']
        elif connection_type == 'sql':
            return self.config['entities']['sql_entities']
        return []
    
    # ========== SQL Server Connection Methods ==========
    
    def get_available_odbc_drivers(self) -> List[str]:
        """Get list of available ODBC drivers"""
        return pyodbc.drivers()
    
    def _get_best_sql_driver(self) -> Optional[str]:
        """Find the best available SQL Server ODBC driver"""
        drivers = self.get_available_odbc_drivers()
        
        preferred_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]
        
        for pref_driver in preferred_drivers:
            if pref_driver in drivers:
                return pref_driver
        return None
    
    def test_sql_connection(self, entity: Dict) -> Tuple[bool, str, Optional[float]]:
        """
        Test SQL Server connection to an entity
        
        Args:
            entity: Entity configuration dictionary
            
        Returns:
            Tuple of (success, message, response_time)
        """
        try:
            start_time = datetime.now()
            
            driver = self._get_best_sql_driver()
            if not driver:
                return False, "No SQL Server ODBC driver found", None
            
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={entity['sql_server']};"
                f"DATABASE={entity['database']};"
                f"UID={entity['username']};"
                f"PWD={entity['password']};"
                f"TrustServerCertificate=yes;"
            )
            
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT DB_NAME() AS CurrentDatabase")
            row = cursor.fetchone()
            
            # Get table count
            cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            table_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return True, f"Connected successfully - {table_count} tables accessible", response_time
            
        except pyodbc.Error as e:
            error_msg = str(e)
            if "Login failed" in error_msg:
                return False, "Authentication failed - Invalid credentials", None
            elif "Cannot open database" in error_msg:
                return False, "Database not found", None
            elif "timeout" in error_msg.lower():
                return False, "Connection timeout - Server unreachable", None
            else:
                short_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                return False, f"Error: {short_error}", None
                
        except Exception as e:
            return False, f"Unexpected error: {str(e)[:100]}", None
    
    def connect_sql(self, entity: Dict):
        """
        Establish SQL Server connection
        
        Args:
            entity: Entity configuration dictionary
            
        Returns:
            pyodbc.Connection object
        """
        driver = self._get_best_sql_driver()
        if not driver:
            raise Exception("No SQL Server ODBC driver found. Please install ODBC Driver for SQL Server.")
        
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={entity['sql_server']};"
            f"DATABASE={entity['database']};"
            f"UID={entity['username']};"
            f"PWD={entity['password']};"
            f"TrustServerCertificate=yes;"
        )
        
        self.connection = pyodbc.connect(conn_str, timeout=30)
        return self.connection
    
    def execute_sql_query(self, entity: Dict, query: str) -> List[Dict]:
        """
        Execute SQL query and return results as list of dictionaries
        
        Args:
            entity: Entity configuration dictionary
            query: SQL query to execute
            
        Returns:
            List of dictionaries representing query results
        """
        conn = self.connect_sql(entity)
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Fetch all rows and convert to list of dicts
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        
        return results
    
    # ========== API Connection Methods ==========
    
    def test_api_connection(self, entity: Dict) -> Tuple[bool, str, Optional[float]]:
        """
        Test API connection to SAP Service Layer
        
        Args:
            entity: Entity configuration dictionary
            
        Returns:
            Tuple of (success, message, response_time)
        """
        try:
            start_time = datetime.now()
            
            login_url = f"{entity['service_layer_url']}/Login"
            payload = {
                "CompanyDB": entity['database'],
                "UserName": entity['username'],
                "Password": entity['password']
            }
            
            response = requests.post(
                login_url,
                json=payload,
                verify=entity.get('verify_ssl', False),
                timeout=30
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get('SessionId', 'N/A')
                
                # Logout
                logout_url = f"{entity['service_layer_url']}/Logout"
                cookies = response.cookies
                requests.post(logout_url, cookies=cookies, verify=entity.get('verify_ssl', False), timeout=10)
                
                return True, f"Connected successfully - Session ID: {session_id[:20]}...", response_time
            else:
                return False, f"Login failed - Status {response.status_code}: {response.text[:100]}", response_time
                
        except requests.exceptions.Timeout:
            return False, "Connection timeout - Server unreachable", None
        except requests.exceptions.ConnectionError:
            return False, "Connection error - Check network/VPN", None
        except Exception as e:
            return False, f"Error: {str(e)[:100]}", None
    
    def connect_api(self, entity: Dict) -> requests.Session:
        """
        Establish API connection to SAP Service Layer
        
        Args:
            entity: Entity configuration dictionary
            
        Returns:
            requests.Session object with authentication
        """
        login_url = f"{entity['service_layer_url']}/Login"
        payload = {
            "CompanyDB": entity['database'],
            "UserName": entity['username'],
            "Password": entity['password']
        }
        
        try:
            self.session = requests.Session()
            
            response = self.session.post(
                login_url,
                json=payload,
                verify=entity.get('verify_ssl', False),
                timeout=30
            )
            
            if response.status_code != 200:
                # Clear the session on failed login
                self.session = None
                raise Exception(f"API Login failed: {response.status_code} - {response.text}")
            
            return self.session
            
        except Exception as e:
            # Ensure session is cleared on any error
            self.session = None
            raise Exception(f"Failed to connect to API: {str(e)}")
    
    def disconnect_api(self, entity: Dict):
        """Logout from SAP Service Layer"""
        if self.session:
            try:
                logout_url = f"{entity['service_layer_url']}/Logout"
                self.session.post(logout_url, verify=entity.get('verify_ssl', False), timeout=10)
            except:
                pass
            finally:
                self.session = None
    
    def fetch_api_data(self, entity: Dict, endpoint: str, filter_query: str = None, 
                       select_fields: str = None, top: int = 1000) -> List[Dict]:
        """
        Fetch data from SAP Service Layer API
        
        Args:
            entity: Entity configuration dictionary
            endpoint: API endpoint (e.g., 'ChartOfAccounts', 'JournalEntries')
            filter_query: OData filter query
            select_fields: Comma-separated list of fields to select
            top: Number of records to fetch per request
            
        Returns:
            List of dictionaries representing the data
        """
        # Ensure we have an active session
        if not self.session:
            try:
                self.connect_api(entity)
            except Exception as e:
                raise Exception(f"Failed to establish API connection: {str(e)}")
        
        # Double-check session is valid
        if not self.session:
            raise Exception("Session is None after connection attempt. API connection may have failed.")
        
        url = f"{entity['service_layer_url']}/{endpoint}"
        
        params = {"$top": top}
        if filter_query:
            params["$filter"] = filter_query
        if select_fields:
            params["$select"] = select_fields
        
        all_data = []
        skip = 0
        
        while True:
            params["$skip"] = skip
            
            response = self.session.get(
                url,
                params=params,
                verify=entity.get('verify_ssl', False),
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            records = data.get('value', [])
            
            if not records:
                break
            
            all_data.extend(records)
            skip += top
            
            # Break if we got fewer records than requested (last page)
            if len(records) < top:
                break
        
        return all_data
    
    # ========== Universal Connection Test ==========
    
    def test_connection(self, entity_id: str) -> Tuple[bool, str, Optional[float], str]:
        """
        Test connection to any entity (SQL or API)
        
        Args:
            entity_id: Entity ID to test
            
        Returns:
            Tuple of (success, message, response_time, connection_type)
        """
        entity = self.get_entity_by_id(entity_id)
        
        if not entity:
            return False, f"Entity '{entity_id}' not found", None, "unknown"
        
        if entity['connection_type'] == 'sql':
            success, message, response_time = self.test_sql_connection(entity)
            return success, message, response_time, "sql"
        elif entity['connection_type'] == 'api':
            success, message, response_time = self.test_api_connection(entity)
            return success, message, response_time, "api"
        else:
            return False, "Unknown connection type", None, "unknown"
    
    def test_all_connections(self) -> List[Dict]:
        """
        Test connections to all entities
        
        Returns:
            List of test results for each entity
        """
        results = []
        
        for entity in self.get_all_entities():
            success, message, response_time, conn_type = self.test_connection(entity['id'])
            
            results.append({
                'entity_id': entity['id'],
                'entity_name': entity['name'],
                'connection_type': conn_type,
                'database': entity.get('database', 'N/A'),
                'success': success,
                'message': message,
                'response_time': response_time,
                'status': '✓ Connected' if success else '✗ Failed'
            })
        
        return results
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup connections"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        
        if self.session:
            try:
                # Try to logout from current session
                self.session.close()
            except:
                pass
