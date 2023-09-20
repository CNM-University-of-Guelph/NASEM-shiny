import pandas as pd
import sqlite3


# Display results, temporary
def display_diet_values(df):
    '''
    Takes a dataframe from model output and formats it for better viewing. Temporary solution.
    '''
    components = ['Fd_CP', 'Fd_RUP_base', 'Fd_NDF', 'Fd_ADF', 'Fd_St', 'Fd_CFat', 'Fd_Ash']
    rows = []

    for component in components:
        percent_diet = round(df.loc['Diet', component + '_%_diet']) #.values[0], 2)
        kg_diet = round(df.loc['Diet', component + '_kg/d'])    #.values[0], 2)
        rows.append([component, percent_diet, kg_diet])

    headers = ['Component', '% DM', 'kg/d']

    table = pd.DataFrame(rows, columns = headers)

    return table



def get_feed_library_df(path_to_db):
    """A function to return the NASEM_feed_library as a dataframe. 

    Args:
        path_to_db (str): A file path as a string 

    Returns:
        A copy of the NASEM_feed_library table that is stored in a sqlite3 db as a pandas df.
    """
    conn = sqlite3.connect(path_to_db)
   
    # SQL query to return the whole table
    query = "SELECT * FROM NASEM_feed_library"

    # get pandas to read table with query
    feed_library = pd.read_sql_query(query, conn)
    
    conn.close()
    return feed_library