from shiny import render
import pandas as pd
import nasem_dairy as nd
# import sqlite3
from pathlib import Path


# load data required
app_dir = Path(__file__).parent
var_desc = pd.read_csv(app_dir / "www/variable_descriptions.csv").query("Description != 'Duplicate'")

# Load global resources
feed_library_default = pd.read_csv(app_dir / 'www/FeedLibrary/NASEM_feed_library.csv').sort_values("Fd_Name")

# Display results, temporary
def display_diet_values(model_output = nd.ModelOutput, is_snapshot = False):
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

    # Iterate through values and select % and kg information
    for component in components: 
        if component in ['Dt_RDP_CP', 'Dt_RUP_CP', 'Dt_ForNDFIn_percNDF']:
            percent_diet = round(float(model_output.get_value(component)),2) 
            kg_diet = None
        else:
            percent_diet = round(float(model_output.get_value(component)), 2) 
            # print(type(model_output.get_value(f'{component}In')))
            kg_diet = round(float(model_output.get_value(f'{component}In')),2)    

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
    # 0: 'user target DM intake',
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
        model_output: nd.ModelOutput,
        # diet_NDF: float,
        coeff_dict: dict
        ):
    '''
    This is used to calculate DMI using functions from nasem_dairy based on which prediction equation the user selects.
    This is required in the app because the model is set to always run with the user-inputed target DMI.
    The model requires diet_NDF which is pre-calculated in the app. However, the DMI on Diet page should have a warning if NDF is missing.
    '''
    
    DMI = 0
    animal_input = animal_input.copy()

    # Predict DMI for lactating cow - also use this equation if 0 is selected for model (i.e. user input)
    if DMIn_eqn in [0,8,11] or model_output is None: 
        #  If dry cow eqn:
        if DMIn_eqn == 11:
            DMI = nd.calculate_Dt_DMIn_DryCow2(
                animal_input['An_BW'], 
                animal_input['An_GestDay'], 
                animal_input['An_GestLength'] 
                ) 
        # This allows for if user has 9 selected, but model_output is none. Returns what it can.
        else:
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
        
    elif DMIn_eqn == 9:
        DMI = nd.calculate_Dt_DMIn_Lact2(
            model_output.get_value('Dt_ForNDF'),
            model_output.get_value('Dt_ADF'),
            model_output.get_value('Dt_NDF'),
            model_output.get_value('Dt_ForDNDF48_ForNDF'),
            model_output.get_value('Trg_MilkProd')
        )
        
    elif DMIn_eqn == 10:      
        # Calculate additional physiology values
        animal_input['An_PrePartDay'] = animal_input['An_GestDay'] - animal_input['An_GestLength']
        animal_input['An_PrePartWk'] = animal_input['An_PrePartDay'] / 7

        Kb_LateGest_DMIn = nd.calculate_Kb_LateGest_DMIn(model_output.get_value('Dt_NDF'))
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
    
        
    else:
        # It needs to catch all possible solutions, otherwise it's possible that it stays unchanged without warning
        print(f"SHINY DMI func: DMIn_eqn uncaught - DMI not changed. DMIn_eqn == {str(DMIn_eqn)}")
        return 'DMI error'

    return round(DMI,2)

##########################################################################################

def pad_cols_UI_df(df: pd.DataFrame, 
                   n_length = 15, 
                   n_length_longer = 100,
                   cols_longer: int|list|str = None # -1 for last column, 0 for first column
                   ):
    """
    df : pd.DataFrame to assign new column names to for rendering UI better
    n_length : minimum width of column
    n_length_longer: length for columns that will be given 'longer' length
    index_longer: index or list of indices for columns to have the longer length
    """
    if cols_longer is None:
        cols_longer = []

    # Ensure index_longer is a list
    if isinstance(cols_longer, (int, str)):
        cols_longer = [cols_longer]
    
    # Convert column names to their respective indices
    adjusted_indices = []
    for idx in cols_longer:
        if isinstance(idx, int) and idx < 0:
            adjusted_indices.append(len(df.columns) + idx)
        elif isinstance(idx, str):
            adjusted_indices.append(df.columns.get_loc(idx))
        else:
            adjusted_indices.append(idx)
    padded_columns = [
        col.ljust(n_length_longer, "\u00A0") if i in adjusted_indices else col.ljust(n_length, "\u00A0")
        for i, col in enumerate(df.columns)
    ]
    
    df.columns = padded_columns
    return df

def prepare_df_render(df_in, *args, cols_longer = [], use_DataTable = True):
        
    if cols_longer == []:
        list_longer = ['Description']
    else:
        list_longer = cols_longer # this will pass None through if needed

    try: 
        df = pad_cols_UI_df(df_in, *args, cols_longer=list_longer)
        
    except (KeyError) as e:
        raise KeyError(f"A column provided to cols_longer argument was not found in df: {e} ") from e

    if use_DataTable == True:
        return render.DataTable(df, height='auto')
    else:
        return render.DataGrid(df, height='auto')


def get_clean_vars(var: str, model_output = nd.ModelOutput):
    '''
    Clean vars gets values from model_output and then converts any single arrays to floats and rounding to 4 significant figures.
    By getting values directly here, meaningful errors can be returned.

    '''
    model_var = model_output.get_value(var)
    
    if model_var is None:
        print(f"Value not in ModelOutput: {var}")
        return None  
    
    try:
    # Try to convert the value to float
        floatvar = float(model_var)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Variable cannot be converted to a float. Likely it is a multi-value np.array. Error from: {var}: {model_var} ") from e

    sig_figs = 4

    return float(f"{floatvar:.{sig_figs}g}")


def get_vars_as_df(vars_return: list, 
                   model_output: nd.ModelOutput,
                   var_desc: pd.DataFrame = var_desc) -> pd.DataFrame:
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
    dict_return = {var: get_clean_vars(var, model_output) for var in vars_return}

    # Convert the dictionary to a DataFrame
    df = (
        pd.DataFrame(
            list(dict_return.items()), 
            columns=['Model Variable', 'Value']
            )
        .merge(var_desc, how = 'left')
        )
            
    return df



