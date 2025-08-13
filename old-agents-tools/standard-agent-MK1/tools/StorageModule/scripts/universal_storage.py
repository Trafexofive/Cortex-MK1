import json
import sqlite3
import sys
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable for the database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../.data/artifacts.db')

# Ensure the directory for the database exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class UniversalStorage:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_db_exists()
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _ensure_db_exists(self):
        """Ensures the SQLite database file exists."""
        if not os.path.exists(self.db_path):
            logging.info(f"Database file not found at {self.db_path}. Creating a new one.")
            try:
                conn = self._get_connection()
                conn.close()
                logging.info("Database file created successfully.")
            except sqlite3.Error as e:
                logging.error(f"Error creating database file: {e}")
                raise

    def _get_connection(self):
        """Establishes and returns a database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Access columns by name
            return conn
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            raise

    def _table_exists(self, cursor, table_name):
        """Checks if a table exists in the database."""
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone() is not None
        logging.debug(f"Table '{table_name}' exists: {exists}")
        return exists

    def _get_table_schema(self, cursor, table_name):
        """Retrieves the schema of a given table."""
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = {row['name']: row['type'] for row in cursor.fetchall()}
        logging.debug(f"Schema for table '{table_name}': {schema}")
        return schema

    def _infer_schema(self, data):
        """Infers SQLite data types from Python types."""
        schema = {}
        for key, value in data.items():
            if isinstance(value, int):
                schema[key] = 'INTEGER'
            elif isinstance(value, float):
                schema[key] = 'REAL'
            elif isinstance(value, str):
                schema[key] = 'TEXT'
            elif isinstance(value, bool):
                schema[key] = 'INTEGER'  # Store booleans as 0 or 1
            elif isinstance(value, (list, dict)):
                schema[key] = 'TEXT'  # Store JSON as TEXT
            elif value is None:
                schema[key] = 'TEXT' # Default to TEXT for None, can be refined
            else:
                schema[key] = 'TEXT' # Fallback
        logging.debug(f"Inferred schema: {schema}")
        return schema

    def _create_table_if_not_exists(self, cursor, table_name, data):
        """Creates a table with inferred schema if it doesn't exist."""
        logging.debug(f"Attempting to create table '{table_name}' if not exists.")
        if not self._table_exists(cursor, table_name):
            schema = self._infer_schema(data)
            columns = ", ".join([f"{col_name} {col_type}" for col_name, col_type in schema.items()])
            # Ensure 'id' column is included if not already in data and is primary key
            if 'id' not in schema:
                create_table_sql = f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns})"
            else:
                create_table_sql = f"CREATE TABLE {table_name} ({columns})"

            logging.info(f"Creating table {table_name} with schema: {create_table_sql}")
            try:
                cursor.execute(create_table_sql)
                logging.info(f"Table '{table_name}' created successfully.")
            except sqlite3.Error as e:
                logging.error(f"Error creating table '{table_name}': {e}")
                raise
        else:
            # Handle schema evolution: add missing columns
            existing_schema = self._get_table_schema(cursor, table_name)
            inferred_schema = self._infer_schema(data)
            for col_name, col_type in inferred_schema.items():
                if col_name not in existing_schema:
                    alter_table_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                    logging.info(f"Adding column '{col_name}' to table '{table_name}'. SQL: {alter_table_sql}")
                    try:
                        cursor.execute(alter_table_sql)
                        logging.info(f"Column '{col_name}' added to table '{table_name}'.")
                    except sqlite3.Error as e:
                        logging.error(f"Error adding column '{col_name}' to table '{table_name}': {e}")
                        raise

    def create(self, table_name, data):
        """Inserts a new record into the specified table."""
        logging.debug(f"Create operation called for table '{table_name}' with data: {data}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            self._create_table_if_not_exists(cursor, table_name, data)

            # Prepare data for insertion, handling JSON serialization
            columns = []
            placeholders = []
            values = []
            for key, value in data.items():
                columns.append(key)
                placeholders.append('?')
                if isinstance(value, (list, dict)):
                    values.append(json.dumps(value))
                elif isinstance(value, bool):
                    values.append(1 if value else 0)
                else:
                    values.append(value)

            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            logging.debug(f"Insert SQL: {insert_sql}, Values: {values}")
            cursor.execute(insert_sql, values)
            conn.commit()
            new_id = cursor.lastrowid
            logging.info(f"Record created in '{table_name}' with ID: {new_id}")
            return new_id

    def read(self, table_name, record_id=None, query_filter=None, order_by=None, limit=None):
        """Reads records from the specified table. Supports ID, filters, ordering, and limits."""
        logging.debug(f"Read operation called for table '{table_name}', record_id: {record_id}, filter: {query_filter}")
        cache_key = f"{table_name}_{record_id}_{json.dumps(query_filter)}_{order_by}_{limit}"
        if cache_key in self.cache:
            self.cache_hits += 1
            logging.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        self.cache_misses += 1
        logging.debug(f"Cache miss for {cache_key}")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = f"SELECT * FROM {table_name}"
            params = []

            if record_id is not None:
                sql += " WHERE id = ?"
                params.append(record_id)
            elif query_filter:
                where_clauses = []
                for key, value in query_filter.items():
                    if isinstance(value, str) and ('%' in value or '_' in value): # Basic LIKE support
                        where_clauses.append(f"{key} LIKE ?")
                        params.append(value)
                    else:
                        where_clauses.append(f"{key} = ?")
                        # Handle boolean conversion for query
                        if isinstance(value, bool):
                            params.append(1 if value else 0)
                        else:
                            params.append(value)
                sql += " WHERE " + " AND ".join(where_clauses)

            if order_by:
                # Basic validation for order_by to prevent SQL injection
                # This is a simple check; for production, use a whitelist of column names
                if isinstance(order_by, str) and ' ' in order_by:
                    col, order = order_by.split(' ', 1)
                    if order.upper() in ['ASC', 'DESC']:
                        sql += f" ORDER BY {col} {order}"
                else:
                    sql += f" ORDER BY {order}"

            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

            logging.debug(f"Read SQL: {sql}, Params: {params}")
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                record = dict(row)
                # Attempt to deserialize JSON strings back to Python objects
                for key, value in record.items():
                    if isinstance(value, str):
                        try:
                            deserialized = json.loads(value)
                            if isinstance(deserialized, (dict, list)):
                                record[key] = deserialized
                        except json.JSONDecodeError:
                            pass # Not a JSON string, keep as is
                results.append(record)

            if record_id is not None and results:
                result = results[0]
            else:
                result = results

            self.cache[cache_key] = result
            return result

    def update(self, table_name, record_id, data):
        """Updates an existing record in the specified table."""
        logging.debug(f"Update operation called for table '{table_name}', record_id: {record_id}, data: {data}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Ensure table exists and schema can accommodate new columns
            self._create_table_if_not_exists(cursor, table_name, data)

            set_clauses = []
            values = []
            for key, value in data.items():
                set_clauses.append(f"{key} = ?")
                if isinstance(value, (list, dict)):
                    values.append(json.dumps(value))
                elif isinstance(value, bool):
                    values.append(1 if value else 0)
                else:
                    values.append(value)
            values.append(record_id)

            update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
            logging.debug(f"Update SQL: {update_sql}, Values: {values}")
            cursor.execute(update_sql, values)
            conn.commit()
            rows_affected = cursor.rowcount
            logging.info(f"Record ID {record_id} updated in '{table_name}'. Rows affected: {rows_affected}")
            # Invalidate relevant cache entries
            self._invalidate_cache(table_name, record_id)
            return rows_affected > 0

    def delete(self, table_name, record_id):
        """Deletes a record from the specified table."""
        logging.debug(f"Delete operation called for table '{table_name}', record_id: {record_id}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            delete_sql = f"DELETE FROM {table_name} WHERE id = ?"
            logging.debug(f"Delete SQL: {delete_sql}, Record ID: {record_id}")
            cursor.execute(delete_sql, (record_id,))
            conn.commit()
            rows_affected = cursor.rowcount
            logging.info(f"Record ID {record_id} deleted from '{table_name}'. Rows affected: {rows_affected}")
            # Invalidate relevant cache entries
            self._invalidate_cache(table_name, record_id)
            return rows_affected > 0

    def list_tables(self):
        """Lists all tables in the database."""
        logging.debug("List tables operation called.")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]
            logging.info(f"Tables in database: {tables}")
            return tables

    def get_stats(self):
        """Returns cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_cache_requests": total_requests,
            "cache_hit_rate": f"{hit_rate:.2f}%"
        }
        logging.info(f"Cache Stats: {stats}")
        return stats

    def clear_cache(self):
        """Clears the internal cache."""
        logging.debug("Clear cache operation called.")
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        logging.info("Cache cleared.")

    def _invalidate_cache(self, table_name, record_id=None):
        """Invalidates cache entries related to a table or specific record."""
        logging.debug(f"Invalidating cache for table '{table_name}', record_id: {record_id}")
        keys_to_invalidate = [k for k in self.cache if k.startswith(f"{table_name}_")]
        if record_id is not None:
            keys_to_invalidate.extend([k for k in self.cache if f"_{record_id}" in k])
        for key in set(keys_to_invalidate):
            del self.cache[key]
        logging.debug(f"Invalidated cache entries for table '{table_name}' and record '{record_id}'.")

def main():
    # The main function to handle command-line arguments and dispatch operations
    logging.debug(f"sys.argv: {sys.argv}")
    storage = UniversalStorage()
    operation = sys.argv[1] if len(sys.argv) > 1 else None
    logging.debug(f"Parsed operation: {operation}")

    result = None
    if operation == 'create':
        if len(sys.argv) < 4:
            result = {"error": "Insufficient arguments for create operation. Expected: table_name, data_json"}
        else:
            table_name = sys.argv[2]
            try:
                data = json.loads(sys.argv[3])
                logging.debug(f"Create - table_name: {table_name}, data: {data}")
                result = storage.create(table_name, data)
            except json.JSONDecodeError as e:
                result = {"error": f"Invalid JSON data for create operation: {e}"}
    elif operation == 'read':
        if len(sys.argv) < 3:
            result = {"error": "Insufficient arguments for read operation. Expected: table_name [record_id] [query_filter_json] [order_by] [limit]"}
        else:
            table_name = sys.argv[2]
            record_id = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else None
            query_filter = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
            order_by = sys.argv[5] if len(sys.argv) > 5 else None
            limit = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
            logging.debug(f"Read - table_name: {table_name}, record_id: {record_id}, filter: {query_filter}, order_by: {order_by}, limit: {limit}")
            result = storage.read(table_name, record_id, query_filter, order_by, limit)
    elif operation == 'update':
        if len(sys.argv) < 5:
            result = {"error": "Insufficient arguments for update operation. Expected: table_name, record_id, data_json"}
        else:
            table_name = sys.argv[2]
            record_id = int(sys.argv[3])
            try:
                data = json.loads(sys.argv[4])
                logging.debug(f"Update - table_name: {table_name}, record_id: {record_id}, data: {data}")
                result = storage.update(table_name, record_id, data)
            except json.JSONDecodeError as e:
                result = {"error": f"Invalid JSON data for update operation: {e}"}
    elif operation == 'delete':
        if len(sys.argv) < 4:
            result = {"error": "Insufficient arguments for delete operation. Expected: table_name, record_id"}
        else:
            table_name = sys.argv[2]
            record_id = int(sys.argv[3])
            logging.debug(f"Delete - table_name: {table_name}, record_id: {record_id}")
            result = storage.delete(table_name, record_id)
    elif operation == 'list_tables':
        result = storage.list_tables()
    elif operation == 'get_stats':
        result = storage.get_stats()
    elif operation == 'clear_cache':
        storage.clear_cache()
        result = {"status": "Cache cleared"}
    else:
        result = {"error": "Invalid operation or insufficient arguments."}

    try:
        print(json.dumps(result))
    except TypeError as e:
        # This handles cases where result might not be directly JSON serializable
        print(json.dumps({"error": f"Failed to serialize result to JSON: {e}", "raw_result": str(result)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"An unexpected error occurred: {e}"}))
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"Failed to execute operation: {e}"}))
        sys.exit(1)
