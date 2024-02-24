import pandas as pd
import nasem_dairy as nd
# import sqlite3


# Display results, temporary
def display_diet_values(df, is_snapshot = False):
    '''
    Takes a dataframe from model output and formats it for better viewing.
    The `is_snapshot` argument allows a shorter version to be returned for the "snapshot" output on Diet page.
    '''
    
    if is_snapshot:
        components = ['Fd_CP', 'Fd_RDP_base', 'Fd_RDP_base_%_CP', 'Fd_RUP_base_%_CP', 'Fd_NDF', 'Fd_ADF', 'Fd_St', 'Fd_CFat']
    else:
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

    if is_snapshot:
        components_long = [
            'Crude Protein (CP)',
            'Rumen Degradeable Protein (RDP % Diet)',
            'Rumen Degradeable Protein (RDP % CP)',
            'Rumen Undegradeable Protein (RUP % CP)',
            'Neutral detergent fibre (NDF)',
            'Acid detergent fibre (ADF)',
            'Starch',
            'Fat',
        ]
        
        table = table.assign(
            Component = components_long, # This replaces the original names in component col
                ).drop(columns='kg DM/d')

    else:
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
            "10 - 12 %", # NASEM book suggestion
            "~7 %",
            "28 - 40 %",
            "65 - 75 %",
            ">19 %",
            "< 26 %",
            "< 7 %",
            "< 10 %"
        ]

        table = table.assign(
            Component = components_long, # This replaces the original names in component col
             **{'Suggestions (lactating cow)' : suggestions_long}
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


def calculate_DMI_prediction(
        animal_input: dict,
        equation_selection: dict,
        diet_NDF: float,
        coeff_dict: dict
        ):
    '''
    This is used to calculate DMI using functions from nasem_dairy based on which prediction equation the user selects.
    This is required in the app because the model is set to always run with the user-inputed target DMI
    '''
    
    DMI = 0
    animal_input = animal_input.copy()

    # Calculate additional physiology values
    animal_input['An_PrePartDay'] = animal_input['An_GestDay'] - animal_input['An_GestLength']
    animal_input['An_PrePartWk'] = animal_input['An_PrePartDay'] / 7


    equation_selection_in = equation_selection.copy()
    equation_selection = {}

    for key, value in equation_selection_in.items():
        try:
            num_value = int(value)
            equation_selection[key] = num_value
        except ValueError:
            print(f"Unable to convert '{value}' to an integer for key '{key}'")


    # Predict DMI for lactating cow - also use this equation if 0 is selected for model (i.e. user input)
    if equation_selection['DMIn_eqn'] in [0,8]: 
        # print("using DMIn_eqn: 8")
        DMI = nd.calculate_Dt_DMIn_Lact1(
            animal_input['An_Parity_rl'], 
            animal_input['Trg_MilkProd'], 
            animal_input['An_BW'], 
            animal_input['An_BCS'],
            animal_input['An_LactDay'], 
            animal_input['Trg_MilkFatp'], 
            animal_input['Trg_MilkTPp'], 
            animal_input['Trg_MilkLacp'])

    # Predict DMI for heifers    
    elif equation_selection['DMIn_eqn'] in [2,3,4,5,6,7,12,13,14,15,16,17]:
        DMI = nd.heifer_growth(
            equation_selection['DMIn_eqn'], 
            # diet_info.loc['Diet', 'Fd_NDF'],
            diet_NDF, 
            animal_input['An_BW'], 
            animal_input['An_BW_mature'], 
            animal_input['An_PrePartWk'], 
            coeff_dict)

    
    elif equation_selection['DMIn_eqn'] in [10,11]:
        DMI = nd.dry_cow_equations(
            equation_selection['DMIn_eqn'], 
            animal_input['An_BW'], 
            animal_input['An_PrePartWk'], 
            animal_input['An_GestDay'], 
            animal_input['An_GestLength'], 
            diet_NDF, 
            coeff_dict)
        
    else:
        # It needs to catch all possible solutions, otherwise it's possible that it stays unchanged without warning
        print("DMIn_eqn uncaught - DMI not changed. equation_selection[DMIn_eqn]: "+ str(equation_selection['DMIn_eqn']) )

    return round(DMI,2)

def format_mineral_dictionaries(mineral_dict):

    df = pd.DataFrame(mineral_dict.items(), columns=['Mineral_Name', 'Value']).assign(
        Mineral = lambda df: df['Mineral_Name'].str.split('_').str[1],
        Type = lambda df: df['Mineral_Name'].str.split('_').str[2]
    )#.set_index('Mineral')

    #df.index.name= None

    return df

def format_minerals_supply_and_req(
        NASEM_mineral_req_dict: pd.DataFrame,
        NASEM_mineral_bal_dict: pd.DataFrame,
        NASEM_mineral_intakes: pd.DataFrame
        ):

    mineral_req_and_balance_df = (
        pd.concat(
            [format_mineral_dictionaries(NASEM_mineral_req_dict),
            format_mineral_dictionaries(NASEM_mineral_bal_dict)]
            )
        .pivot(index='Mineral', columns='Type', values='Value')
        .reset_index()
        )


    mineral_intakes_formatted = (
        NASEM_mineral_intakes.assign(
            Diet_percent = lambda df: df['Dt_micro'].fillna(df['Dt_macro'])
            )
            .drop(columns=['Dt_macro', 'Dt_micro',])
            .reset_index(names='Mineral')
            .round(2)
            )

    mineral_req_and_balance_and_intakes = (
        mineral_intakes_formatted
        .merge(mineral_req_and_balance_df)
        .rename(
            columns = {'Dt_mineralIn':'Diet Supply (TDS), g/d',
                'Diet_percent':'Diet Density',
                'req':'Absorbed Requirement (TAR), g/d',
                'Abs_mineralIn':'Absorbed Supply (TAS), g/d',
                'bal':'Balance (TAS - TAR), g/d'
                }
                )
        .assign(
            Diet_Density_Units = lambda df: df['Mineral'].apply(lambda x: '%' if x in ['Ca', 'P', 'Mg', 'Cl', 'K', 'Na', 'S'] else 'mg/kg'),
            # Balance = lambda df: df['Absorbed Supply (TAS)'] - df['Absorbed Requirement (TAR)']
        )
        .reindex(columns = ['Mineral','Diet Density', 'Diet_Density_Units', 'Absorbed Requirement (TAR), g/d', 'Absorbed Supply (TAS), g/d','Diet Supply (TDS), g/d',  'Balance (TAS - TAR), g/d' ])
    )

    return mineral_req_and_balance_and_intakes




