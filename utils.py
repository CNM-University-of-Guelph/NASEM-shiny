import pandas as pd
import sqlite3


# Display results, temporary
def display_diet_values(df):
    '''
    Takes a dataframe from model output and formats it for better viewing. Temporary solution.
    '''
    components = ['Fd_CP', 'Fd_RUP_base', 'Fd_NDF', 'Fd_ADF', 'Fd_St', 'Fd_CFat', 'Fd_Ash']
    rows = []
    
    # select diet row and store as dictionary
    diet_dict = df.loc['Diet',:].to_dict()

    # Iterate through values and select % and kg information
    for component in components:
        percent_diet = round(diet_dict.get(component + '_%_diet'), 3) * 100
        kg_diet = round(diet_dict.get(component + '_kg/d'), 2)    
        rows.append([component, percent_diet, kg_diet])

    headers = ['Component', '% DM', 'kg/d']

    table = pd.DataFrame(rows, columns = headers)

    return table



# def get_feed_library_df(path_to_db):
#     """A function to return the NASEM_feed_library as a dataframe. 

#     Args:
#         path_to_db (str): A file path as a string 

#     Returns:
#         A copy of the NASEM_feed_library table that is stored in a sqlite3 db as a pandas df.
#     """
#     conn = sqlite3.connect(path_to_db)
   
#     # SQL query to return the whole table
#     query = "SELECT * FROM NASEM_feed_library"

#     # get pandas to read table with query
#     feed_library = pd.read_sql_query(query, conn)
    
#     conn.close()
#     return feed_library


def get_unique_feed_list(df: pd.DataFrame) -> list:
    '''
    Takes the feed library and returns a list of unique feed names
    Excepts the column to be called 'Fd_Name'
    '''
    return df.loc[:,'Fd_Name'].drop_duplicates().to_list()




def get_teaching_feeds() -> list:
    '''
    Returns a hard-coded list of feed names that are called 'teaching_feeds'
    '''
    return [
        "Barley silage, mid-maturity",
        "Calcium carbonate",
        "Calcium phosphate (di)",
        "Canola meal",
        "Corn grain HM, fine grind",
        "Corn silage, typical",
        "Fat, canola oil",
        "Manganese oxide",
        "Sodium bicarbonate",
        "Soybean hulls",
        "Triticale silage, mid-maturity",
        "Urea",
        "Wheat straw",
        "Triticale hay"
        ]

def rename_df_cols_Fd_to_feed(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Rename columns of the feed df to replace Fd_ with 'Feed_' 
    Takes a df and returns a df.
    '''
    return df.rename(columns= {col: f'Feed {col[3:]}' if col.startswith('Fd_') else col for col in df.columns} )

def DM_intake_equation_strings() -> dict:
    return {
    0: 'user target DM intake',
    1: 'Milk fed calf',
    2: 'All heifers, animal factors only, NRC equation, individual animal',
    3: 'All heifers, animal and feed factors, NRC equation, individual animal',
    4: 'Holstein heifer, animal factors only, individual prepartum',
    5: 'Holstein heifer, animal and feed factors, individual prepartum',
    6: 'Holstein x Jersey heifer, animal factors only, individual prepartum',
    7: 'Holstein x Jersey heifer, animal and feed factors, individual prepartum',
    8: 'lactating, cow factors only',
    9: 'lactating, cow and feed factors',
    10: 'dry, NRC 2020',
    11: 'dry, Hayirli, 2003',
    12: 'All heifers, animal factors only, NRC equation, pen based intake',
    13: 'All heifers, animal and feed factors, NRC equation, pen based intake',
    14: 'Holstein heifer, animal factors only, pen prepartum',
    15: 'Holstein heifer, animal and feed factors, pen prepartum',
    16: 'Holstein x Jersey heifer, animal factors only, pen prepartum',
    17: 'Holstein x Jersey heifer, animal and feed factors, pen prepartum'
    }
