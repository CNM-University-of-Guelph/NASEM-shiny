import pandas as pd
# import sqlite3


# Display results, temporary
def display_diet_values(df):
    '''
    Takes a dataframe from model output and formats it for better viewing.
    '''
    components = ['Fd_CP', 'Fd_RDP_base_%_CP', 'Fd_RUP_base_%_CP','Fd_RDP_base', 'Fd_RUP_base', 'Fd_NDF', 'Fd_ForNDFIn_percNDF','Fd_ADF', 'Fd_St', 'Fd_CFat', 'Fd_Ash']
    rows = []
    
    # select diet row and store as dictionary
    diet_dict =  df.assign(
        Fd_ForNDFIn_percNDF = lambda df: df['Fd_ForNDFIn'] / df['Fd_NDF_kg/d']
        ).loc['Diet',:].to_dict()
    # diet_dict = df.loc['Diet',:].to_dict()

    # Iterate through values and select % and kg information
    for component in components:
        if component in ['Fd_RDP_base_%_CP', 'Fd_RUP_base_%_CP', 'Fd_ForNDFIn_percNDF']:
            percent_diet = round(diet_dict.get(component),2) * 100
            kg_diet = None
        else:
            percent_diet = round(diet_dict.get(component + '_%_diet'), 3) * 100
            kg_diet = round(diet_dict.get(component + '_kg/d'), 2)    
        
        rows.append([component, percent_diet, kg_diet])

    headers = ['Component', '% DM', 'kg DM/d']


    table = pd.DataFrame(rows, columns = headers)


    # map new names
    components_long = [
        'Crude Protein (CP)',
        'Rumen Degradeable Protein (RDP % CP)',
        'Rumen Undegradeable Protein (RUP % CP)',
        'Rumen Degradeable Protein (RDP % Diet)',
        'Rumen Undegradeable Protein (RUP % Diet)',
        'Neutral detergent fibre (NDF)',
        'Forage NDF (% NDF)',
        'Acid detergent fibre (ADF)',
        'Starch',
        'Fat',
        'Ash'
    ]

    suggestions_long = [
        "15 - 17 %",
        "< 70 %",
        "33 - 40 %",
        "~10 %",
        "~7 %",
        "28 - 40 %",
        "65 - 75 %",
        ">19 %",
        "< 26 %",
        "< 7 %",
        "< 10 %"
    ]

    table = table.assign(
        Component = components_long,
        Suggestions = suggestions_long
        )

    return table




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
        "DDGS, high protein",
        "Fat, canola oil",
        "Legume hay, mid-maturity",
        "Magnesium oxide",
        "Sodium bicarbonate",
        "Soybean hulls",
        'Soybean meal, extruded',
        "Triticale silage, mid-maturity",
        "Urea",
        "Wheat straw",
        "Triticale hay",
        'VitTM Premix, generic'
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
