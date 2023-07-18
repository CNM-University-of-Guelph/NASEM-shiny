import sqlite3

def fl_get_feeds_from_db(path_to_db):
    conn = sqlite3.connect(path_to_db)
    cursor = conn.cursor()
   
    # SQL query to select unique entries from the Fd_Name column
    query = "SELECT DISTINCT Fd_Name FROM NASEM_feed_library"

    # Execute the query
    cursor.execute(query)

    # Fetch all the unique Fd_Name values as a list
    unique_fd_names = [row[0] for row in cursor.fetchall()]

    # Close the cursor and the connection
    cursor.close()
    conn.close()
    return unique_fd_names