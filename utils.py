import pandas as pd
import nasem_dairy as nd
# import sqlite3


# Display results, temporary
def display_diet_values(diet_dict: dict, is_snapshot = False):
    '''
    Takes a dataframe from model output and formats it for better viewing.
    The `is_snapshot` argument allows a shorter version to be returned for the "snapshot" output on Diet page.
    '''
    if is_snapshot:
        # 'In' = kg/d (instead of %); RUP/RDP _CP = % of CP; 
        components = [
            'Dt_CP', 'Dt_RDP', 'Dt_RDP_CP', 'Dt_RUP_CP', 'Dt_NDF', 
            'Dt_ADF', 'Dt_St', 'Dt_CFat'
            ]
    else:
        components = [
            'Dt_CP', 'Dt_RDP_CP', 'Dt_RUP_CP','Dt_RDP', 'Dt_RUP', 'Dt_NDF', 
            'Dt_ForNDFIn_percNDF','Dt_ADF', 'Dt_St', 'Dt_CFat', 'Dt_Ash'
            ]


    rows = []

    # Add dietary forage NDF intake as a % of diet NDF intake
    diet_dict['Dt_ForNDFIn_percNDF'] = diet_dict.get('Dt_ForNDFIn') / diet_dict.get('Dt_NDFIn')

    # Iterate through values and select % and kg information
    for component in components: 
        if component in ['Dt_RDP_CP', 'Dt_RUP_CP', 'Dt_ForNDFIn_percNDF']:
            percent_diet = round(float(diet_dict.get(component)),2) 
            kg_diet = None
        else:
            percent_diet = round(float(diet_dict.get(component)), 2) 
            # print(type(diet_dict.get(f'{component}In')))
            kg_diet = round(float(diet_dict.get(f'{component}In')),2)    

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

# def display_diet_values(df, is_snapshot = False):
#     '''
#     Takes a dataframe from model output and formats it for better viewing.
#     The `is_snapshot` argument allows a shorter version to be returned for the "snapshot" output on Diet page.
#     '''
    
#     if is_snapshot:
#         components = ['Fd_CP', 'Fd_RDP_base', 'Fd_RDP_base_%_CP', 'Fd_RUP_base_%_CP', 'Fd_NDF', 'Fd_ADF', 'Fd_St', 'Fd_CFat']
#     else:
#         components = ['Fd_CP', 'Fd_RDP_base_%_CP', 'Fd_RUP_base_%_CP','Fd_RDP_base', 'Fd_RUP_base', 'Fd_NDF', 'Fd_ForNDFIn_percNDF','Fd_ADF', 'Fd_St', 'Fd_CFat', 'Fd_Ash']
    
#     rows = []
    
#     # select diet row and store as dictionary
#     diet_dict =  df.assign(
#         Fd_ForNDFIn_percNDF = lambda df: df['Fd_ForNDFIn'] / df['Fd_NDFIn']
#         ).loc['Diet',:].to_dict()
#     # diet_dict = df.loc['Diet',:].to_dict()

#     # Iterate through values and select % and kg information
#     for component in components:
#         if component in ['Fd_RDP_base_%_CP', 'Fd_RUP_base_%_CP', 'Fd_ForNDFIn_percNDF']:
#             percent_diet = round(diet_dict.get(component),2) * 100
#             kg_diet = None
#         else:
#             percent_diet = round(diet_dict.get(component + '_%_diet'), 3) * 100
#             kg_diet = round(diet_dict.get(component + '_kg/d'), 2)    
        
#         rows.append([component, percent_diet, kg_diet])

#     headers = ['Component', '% DM', 'kg DM/d']


#     table = pd.DataFrame(rows, columns = headers)

#     if is_snapshot:
#         components_long = [
#             'Crude Protein (CP)',
#             'Rumen Degradeable Protein (RDP % Diet)',
#             'Rumen Degradeable Protein (RDP % CP)',
#             'Rumen Undegradeable Protein (RUP % CP)',
#             'Neutral detergent fibre (NDF)',
#             'Acid detergent fibre (ADF)',
#             'Starch',
#             'Fat',
#         ]
        
#         table = table.assign(
#             Component = components_long, # This replaces the original names in component col
#                 ).drop(columns='kg DM/d')

#     else:
#         # map new names
#         components_long = [
#             'Crude Protein (CP)',
#             'Rumen Degradeable Protein (RDP % CP)',
#             'Rumen Undegradeable Protein (RUP % CP)',
#             'Rumen Degradeable Protein (RDP % Diet)',
#             'Rumen Undegradeable Protein (RUP % Diet)',
#             'Neutral detergent fibre (NDF)',
#             'Forage NDF (% NDF)',
#             'Acid detergent fibre (ADF)',
#             'Starch',
#             'Fat',
#             'Ash'
#         ]

#         suggestions_long = [
#             "15 - 17 %",
#             "< 70 %",
#             "33 - 40 %",
#             "10 - 12 %", # NASEM book suggestion
#             "~7 %",
#             "28 - 40 %",
#             "65 - 75 %",
#             ">19 %",
#             "< 26 %",
#             "< 7 %",
#             "< 10 %"
#         ]

#         table = table.assign(
#             Component = components_long, # This replaces the original names in component col
#              **{'Suggestions (lactating cow)' : suggestions_long}
#             )
#     return table


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
    # 1: 'Milk fed calf',
    # 2: 'All heifers, animal factors only, NRC equation, individual animal',
    # 3: 'All heifers, animal and feed factors, NRC equation, individual animal',
    # 4: 'Holstein heifer, animal factors only, individual prepartum',
    # 5: 'Holstein heifer, animal and feed factors, individual prepartum',
    # 6: 'Holstein x Jersey heifer, animal factors only, individual prepartum',
    # 7: 'Holstein x Jersey heifer, animal and feed factors, individual prepartum',
    8: 'lactating, cow factors only',
    9: 'lactating, cow and feed factors',
    10: 'dry, NRC 2020',
    11: 'dry, Hayirli, 2003',
    # 12: 'All heifers, animal factors only, NRC equation, pen based intake',
    # 13: 'All heifers, animal and feed factors, NRC equation, pen based intake',
    # 14: 'Holstein heifer, animal factors only, pen prepartum',
    # 15: 'Holstein heifer, animal and feed factors, pen prepartum',
    # 16: 'Holstein x Jersey heifer, animal factors only, pen prepartum',
    # 17: 'Holstein x Jersey heifer, animal and feed factors, pen prepartum'
    }


def validate_equation_selections(equation_selection: dict) -> dict:
    '''
    Inputs from Shiny may need to be coerced from strings to numbers to use.
    '''
    equation_selection_in = equation_selection.copy()
    equation_selection = {}

    for key, value in equation_selection_in.items():
        try:
            num_value = int(value)
            equation_selection[key] = num_value
        except ValueError:
            print(f"Unable to convert '{value}' to an integer for key '{key}'")
    return equation_selection


def calculate_DMI_prediction(
        animal_input: dict,
        DMIn_eqn: int,
        diet_NDF: float,
        coeff_dict: dict
        ):
    '''
    This is used to calculate DMI using functions from nasem_dairy based on which prediction equation the user selects.
    This is required in the app because the model is set to always run with the user-inputed target DMI.
    The model requires diet_NDF which is pre-calculated in the app. However, the DMI on Diet page should have a warning if NDF is missing.
    '''
    
    DMI = 0
    animal_input = animal_input.copy()

    # Calculate additional physiology values
    animal_input['An_PrePartDay'] = animal_input['An_GestDay'] - animal_input['An_GestLength']
    animal_input['An_PrePartWk'] = animal_input['An_PrePartDay'] / 7


    # Predict DMI for lactating cow - also use this equation if 0 is selected for model (i.e. user input)
    if DMIn_eqn in [0,8]: 
        Trg_NEmilk_Milk = nd.calculate_Trg_NEmilk_Milk(
            animal_input['Trg_MilkTPp'], 
            animal_input['Trg_MilkFatp'], 
            animal_input['Trg_MilkLacp']
            )
        # print("using DMIn_eqn: 8")
        DMI = nd.calculate_Dt_DMIn_Lact1(
            animal_input['Trg_MilkProd'], 
            animal_input['An_BW'], 
            animal_input['An_BCS'],
            animal_input['An_LactDay'], 
            animal_input['An_Parity_rl'], 
            Trg_NEmilk_Milk)
        
    # elif DMIn_eqn == 9:
        
    elif DMIn_eqn == 10:      
        Kb_LateGest_DMIn = nd.calculate_Kb_LateGest_DMIn(diet_NDF)
        An_PrePartWklim = nd.calculate_An_PrePartWklim(
            animal_input['An_PrePartWk']
        )
        An_PrePartWkDurat = An_PrePartWklim * 2

        Dt_DMIn_BW_LateGest_i = nd.calculate_Dt_DMIn_BW_LateGest_i(
            An_PrePartWklim, 
            Kb_LateGest_DMIn, 
            coeff_dict
            )
        Dt_DMIn_BW_LateGest_p = nd.calculate_Dt_DMIn_BW_LateGest_p(
            An_PrePartWkDurat,
            Kb_LateGest_DMIn, 
            coeff_dict
            )
        
        if animal_input['An_PrePartWk'] > An_PrePartWkDurat:
            DMI = min(
                nd.calculate_Dt_DMIn_DryCow1_FarOff(
                    animal_input['An_BW'], 
                    Dt_DMIn_BW_LateGest_i),
                nd.calculate_Dt_DMIn_DryCow1_Close(
                    animal_input['An_BW'], 
                    Dt_DMIn_BW_LateGest_p))
        else:
            DMI = nd.calculate_Dt_DMIn_DryCow1_FarOff(
                animal_input['An_BW'], 
                Dt_DMIn_BW_LateGest_i
                )
            
    elif DMIn_eqn == 11:
        DMI = nd.calculate_Dt_DMIn_DryCow2(
            animal_input['An_BW'], 
            animal_input['An_GestDay'], 
            animal_input['An_GestLength'] 
            ) 
    
        
    else:
        # It needs to catch all possible solutions, otherwise it's possible that it stays unchanged without warning
        print(f"DMIn_eqn uncaught - DMI not changed. DMIn_eqn == {str(DMIn_eqn)}")
        return 'DMI error'

    return round(DMI,2)

# def format_mineral_dictionaries(mineral_dict):

#     df = pd.DataFrame(mineral_dict.items(), columns=['Mineral_Name', 'Value']).assign(
#         Mineral = lambda df: df['Mineral_Name'].str.split('_').str[1],
#         Type = lambda df: df['Mineral_Name'].str.split('_').str[2]
#     )#.set_index('Mineral')

#     #df.index.name= None

#     return df

# def format_minerals_supply_and_req(
#         NASEM_mineral_req_dict: pd.DataFrame,
#         NASEM_mineral_bal_dict: pd.DataFrame,
#         NASEM_mineral_intakes: pd.DataFrame
#         ):

#     mineral_req_and_balance_df = (
#         pd.concat(
#             [format_mineral_dictionaries(NASEM_mineral_req_dict),
#             format_mineral_dictionaries(NASEM_mineral_bal_dict)]
#             )
#         .pivot(index='Mineral', columns='Type', values='Value')
#         .reset_index()
#         )


#     mineral_intakes_formatted = (
#         NASEM_mineral_intakes.assign(
#             Diet_percent = lambda df: df['Dt_micro'].fillna(df['Dt_macro'])
#             )
#             .drop(columns=['Dt_macro', 'Dt_micro',])
#             .reset_index(names='Mineral')
#             .round(2)
#             )

#     mineral_req_and_balance_and_intakes = (
#         mineral_intakes_formatted
#         .merge(mineral_req_and_balance_df)
#         .rename(
#             columns = {'Dt_mineralIn':'Diet Supply (TDS), g/d',
#                 'Diet_percent':'Diet Density',
#                 'req':'Absorbed Requirement (TAR), g/d',
#                 'Abs_mineralIn':'Absorbed Supply (TAS), g/d',
#                 'bal':'Balance (TAS - TAR), g/d'
#                 }
#                 )
#         .assign(
#             Diet_Density_Units = lambda df: df['Mineral'].apply(lambda x: '%' if x in ['Ca', 'P', 'Mg', 'Cl', 'K', 'Na', 'S'] else 'mg/kg'),
#             # Balance = lambda df: df['Absorbed Supply (TAS)'] - df['Absorbed Requirement (TAR)']
#         )
#         .reindex(columns = ['Mineral','Diet Density', 'Diet_Density_Units', 'Absorbed Requirement (TAR), g/d', 'Absorbed Supply (TAS), g/d','Diet Supply (TDS), g/d',  'Balance (TAS - TAR), g/d' ])
#     )

#     return mineral_req_and_balance_and_intakes

##########################################################################################


def get_vars_as_df(vars_return: list, model_output: nd.ModelOutput) -> pd.DataFrame:
    """
    Create a pandas DataFrame from a list of variable names.

    Parameters:
    vars_return (list of str): A list of variable names for which values are to be retrieved.
    model_output (ModelOutput): A ModelOutput from nasem_dairy package

    Returns:
    pd.DataFrame: A DataFrame with two columns 'Variable' and 'Value', containing the variable names
                  and their corresponding values.
    """
    # Create a dictionary with variable names as keys and their corresponding values as float
    dict_return = {var: model_output.get_value(var) for var in vars_return}
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(list(dict_return.items()), columns=['Variable', 'Value'])
    
    return df

# Example usage:
# Assuming 'vars_return' is predefined and 'output.get_value' is an existing function that you can call.
# vars_return = ['Trg_MEuse', 'An_MEmUse', 'An_MEgain', 'Gest_MEuse', ...]
# dataframe = create_dataframe_from_vars(vars_return)
# print(dataframe)


