import logging
from typing import Optional, TypedDict

import psycopg2
from psycopg2 import sql

import discord
from discord.ext import commands


class PSQLParams(TypedDict):
    dbname: str
    user: str
    password: str
    host: str
    port: int


class ChatHelper:
    """A class to save and query chat history.

    Attributes:
        conn_params (PSQLParams): Database connection parameters.
        conn (Optional[psycopg2.extensions.connection]): The connection
            object for the database.
        cursor (Optional[psycopg2.extensions.cursor]): The cursor object for
            executing database commands.
    """

    TABLE_NAME = "chat_history"
    TABLE_STRUCT = """
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        username BIGINT NOT NULL,
        channel VARCHAR(50) NOT NULL,
        message TEXT NOT NULL
    """

    def __init__(self, db_params: PSQLParams) -> None:
        """Initializes the PostgresTableCreator with database parameters.

        Args:
            db_params (PSQLParams): Database connection parameters.
        """
        self.conn_params: PSQLParams = db_params
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        self._logger = logging.getLogger(__name__)

    def __enter__(self) -> 'ChatHelper':
        """Establishes the database connection and returns the instance.

        This allows the class to be used as a context manager, automatically
        handling the connection setup.

        Returns:
            PostgresTableCreator: The instance of the class.

        Raises:
            psycopg2.Error: If the database connection fails.
        """
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor()
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the database cursor and connection.

        This method is called when exiting the 'with' block, ensuring that
        database resources are properly released.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def _assert_connection(self) -> None:
        """Assert there is an active database connection.

        Raises:
            RuntimeError: If there is no active connection.
        """
        if not self.conn or not self.cursor:
            raise psycopg2.Error("Database connection is not available.")

    def drop_table(self) -> None:
        """Drops the chat history table if it exists.

        Raises:
            psycopg2.Error: If the table deletion fails.
        """
        self._assert_connection()

        try:
            drop_query = sql.SQL("DROP TABLE IF EXISTS {table} CASCADE").format(
                table=sql.Identifier(ChatHelper.TABLE_NAME)
            )
            self.cursor.execute(drop_query)
            self.conn.commit()
            self._logger.info(f"Table '{ChatHelper.TABLE_NAME}' dropped successfully (if it existed).")
        except psycopg2.Error as e:
            self._logger.error(f"Error dropping table '{ChatHelper.TABLE_NAME}': {e}")
            if self.conn:
                self.conn.rollback()
            raise e

    def verify_table(self) -> None:
        """Creates a table in the database if it does not already exist.

        Raises:
            psycopg2.Error: If the table creation fails.
        """
        self._assert_connection()

        # The column definitions are passed as a raw string,
        # but the table name is passed as a safe SQL identifier.
        query = sql.SQL("CREATE TABLE IF NOT EXISTS {table} ({columns})").format(
            table=sql.Identifier(ChatHelper.TABLE_NAME),
            columns=sql.SQL(ChatHelper.TABLE_STRUCT)
        )

        try:
            self.cursor.execute(query)
            self.conn.commit()
            self._logger.info(f"Table '{ChatHelper.TABLE_NAME}' created successfully or already exists.")
        except psycopg2.Error as e:
            self._logger.warning(f"Error creating table '{ChatHelper.TABLE_NAME}': {e}")
            if self.conn:
                self.conn.rollback()
            raise e

    def table_exists(self, table_name: str) -> bool:
        """Checks if a table exists in the database.

        Args:
            table_name (str): The name of the table to check.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        self._assert_connection()

        query = sql.SQL("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)")
        self.cursor.execute(query, (table_name,))
        exists = self.cursor.fetchone()[0]
        return exists

    def save_chat_message(self, message: discord.Message) -> None:
        """Saves a chat message to the database.

        Args:
            message (discord.Message): The message to save.
        """
        self._assert_connection()
        try:
            insert_query = sql.SQL(
                "INSERT INTO {table} (username, channel, message) VALUES (%s, %s, %s)"
            ).format(table=sql.Identifier(ChatHelper.TABLE_NAME))
            self.cursor.execute(
                insert_query,
                (message.author.id, message.channel.name, message.clean_content)
            )
            self.conn.commit()
            self._logger.info("Chat message saved successfully.")
        except psycopg2.Error as e:
            self._logger.error(f"Error saving chat message: {e}")
            if self.conn:
                self.conn.rollback()

    def messages_from_user(self, user: discord.User, since: int = 0) -> tuple[discord.Message]:
        """Retrieves chat messages from a specific user.

        Args:
            username (str): The username to filter messages by.
            since (int): Limit messages to ones less than this many seconds old.

        Returns:
            tuple[discord.Message]: A tuple of Discord Message objects.
        """
        # This is a simplified representation.
        # In a real bot, you'd reconstruct or use these parts as needed.
        class MockAuthor:
            def __init__(self, name):
                self.global_name = name
        class MockChannel:
            def __init__(self, name):
                self.name = name

        self._assert_connection()
        try:
            if since > 0:
                query = sql.SQL(
                    "SELECT username, channel, message, timestamp FROM {table} WHERE username = %s AND timestamp >= NOW() - INTERVAL '%s seconds' ORDER BY timestamp ASC"
                ).format(table=sql.Identifier(ChatHelper.TABLE_NAME))
                self.cursor.execute(query, (user.id, since))
            else:
                query = sql.SQL(
                    "SELECT username, channel, message, timestamp FROM {table} WHERE username = %s ORDER BY timestamp ASC"
                ).format(table=sql.Identifier(ChatHelper.TABLE_NAME))
                self.cursor.execute(query, (user.id,))

            rows = self.cursor.fetchall()
            # Convert rows to a list of discord.Message-like objects
            # (simplified for demonstration, as full discord.Message requires more context)
            messages = []
            for row in rows:
                mock_message = type('MockMessage', (object,), {
                    'created_at': row[3],
                    'author': MockAuthor(row[0]),
                    'channel': MockChannel(row[1]),
                    'clean_content': row[2]
                })()
                messages.append(mock_message)
            return tuple(messages)
        except psycopg2.Error as e:
            self._logger.error(f"Error retrieving messages for user '{user.global_name}': {e}")
            return ()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # --- Example Usage ---
    # Replace with your actual database connection parameters
    db_connection_params = PSQLParams(
        dbname="bad_employee",
        user="employee",
        password="password",
        host="db",
        port="5432"
    )

    with ChatHelper(db_connection_params) as chat_helper:
        if chat_helper.table_exists("chat_history"):
            print("Table 'chat_history' exists.")
        else:
            print("Table 'chat_history' does not exist.")

        chat_helper.drop_table()
        chat_helper.verify_table()
