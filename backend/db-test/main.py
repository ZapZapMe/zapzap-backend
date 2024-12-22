from flask import Flask, jsonify
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from google.cloud.sql.connector import Connector, IPTypes


logger = logging.getLogger(__name__)


app = Flask(__name__)


def connect_unix_socket():
    """Initializes a Unix socket connection pool for a Cloud SQL instance of Postgres."""
    db_user = os.environ["DB_USER"]  # e.g. 'my-database-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-database-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'
    INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME")

    if not all([db_user, db_pass, db_name, INSTANCE_CONNECTION_NAME]):
        raise EnvironmentError("Missing req db env variables")

    unix_socket_path = f"/cloudsql/{INSTANCE_CONNECTION_NAME}"

    pool = create_engine(
        # Equivalent URL:
        # postgresql+pg8000://<db_user>:<db_pass>@/<db_name>
        #                         ?unix_sock=<INSTANCE_UNIX_SOCKET>/.s.PGSQL.5432
        # Note: Some drivers require the `unix_sock` query parameter to use a different key.
        # For example, 'psycopg2' uses the path set to `host` in order to connect successfully.
        f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}",
        connect_args={"unix_sock": f"{unix_socket_path}/.s.PGSQL.5432"},
    )
    return pool


engine = connect_unix_socket()

# postgresql+pg8000://<db_user>:<db_pass>@/<db_name>?unix_sock=<INSTANCE_UNIX_SOCKET>/.s.PGSQL.5432


@app.route("/")
def index():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW();")).fetchone()
            return jsonify({"Status": "success", "database_time": result[0]}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"Database query failed: {e}", exc_info=True)
        return jsonify({"Status": "error", "message": "Query failed"}), 500
    # connection = connect_unix_socket()
    # if connection:
    #     try:
    #         with connection.cursor(cursor_factory=RealDictCursor) as cursor:
    #             cursor.execute("SELECT NOW();")
    #             result = cursor.fetchone()
    #             connection.close()
    #             return (
    #                 jsonify(
    #                     {
    #                         "status": "success",
    #                         "message": "Successfully connected to the database.",
    #                         "database_time": result["now"],
    #                     }
    #                 ),
    #                 200,
    #             )
    #     except Exception as e:
    #         app.logger.error(f"Query failed: {e}")
    #         return (
    #             jsonify({"status": "error", "message": f"Query failed: {str(e)}"}),
    #             500,
    #         )
    # else:
    #     return (
    #         jsonify(
    #             {"status": "error", "message": "Failed to connect to the database."}
    #         ),
    #         500,
    #     )


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # For local testing only. In production, use Gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


# # Environment Variables
# DB_USER = os.environ.get('DB_USER')
# DB_PASSWORD = os.environ.get('DB_PASS')
# DB_NAME = os.environ.get('DB_NAME')
# INSTANCE_CONNECTION_NAME = os.environ.get('INSTANCE_CONNECTION_NAME')

# # Unix socket path
# CLOUD_SQL_UNIX_SOCKET = f"/cloudsql/{INSTANCE_CONNECTION_NAME}"

# def get_db_connection():
#     try:
#         connection = psycopg2.connect(
#             user=DB_USER,
#             password=DB_PASSWORD,
#             dbname=DB_NAME,
#             host=CLOUD_SQL_UNIX_SOCKET,
#             port=5432  # Default PostgreSQL port
#         )
#         return connection
#     except Exception as e:
#         app.logger.error(f"Database connection failed: {e}")
#         return None
# #/cloudsql/zapzap-infra:europe-west1:postgres-instance/.s.PGSQL.5432
# @app.route('/')
# def index():
#     connection = get_db_connection()
#     if connection:
#         try:
#             with connection.cursor(cursor_factory=RealDictCursor) as cursor:
#                 cursor.execute("SELECT NOW();")
#                 result = cursor.fetchone()
#                 connection.close()
#                 return jsonify({
#                     "status": "success",
#                     "message": "Successfully connected to the database.",
#                     "database_time": result['now']
#                 }), 200
#         except Exception as e:
#             app.logger.error(f"Query failed: {e}")
#             return jsonify({
#                 "status": "error",
#                 "message": f"Query failed: {str(e)}"
#             }), 500
#     else:
#         return jsonify({
#             "status": "error",
#             "message": "Failed to connect to the database."
#         }), 500

# @app.route('/health')
# def health():
#     return jsonify({"status": "ok"}), 200

# if __name__ == '__main__':
#     # For local testing only. In production, use Gunicorn.
#     app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
