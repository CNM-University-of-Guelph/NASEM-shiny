from shiny import App, reactive, render, ui
import pandas as pd
from asyncio import sleep
# import shinyswatch
#import pdb #like browser()

from NASEM_functions import *
from ration_balancer import *

# get list of feeds available from the feed library in db
# used for user selection in shiny
unique_fd_list = fl_get_feeds_from_db('diet_database.db')

def NASEM_model(diet_info, animal_input, equation_selection):
########################################
# Step 1: Read User Input
########################################
   
    diet_info = diet_info.copy()

        # list_of_feeds is used to query the database and retrieve the ingredient composition, stored in feed_data
    list_of_feeds = diet_info['Feedstuff'].tolist()
    feed_data = fl_get_rows(list_of_feeds, path_to_db = 'diet_database.db')

    # Scale %_DM_intake to 100%
    user_perc = diet_info['%_DM_user'].sum()
    scaling_factor = 100 / user_perc

    # Should be called 'Fd_DMInp' instead of %_DM_intake
    diet_info['%_DM_intake'] = diet_info['%_DM_user'] * scaling_factor
    # Adjust so sum is exactly 100
    adjustment = 100 - diet_info['%_DM_intake'].sum()
    diet_info['%_DM_intake'] += adjustment / len(diet_info)

    # Predict DMI
    if equation_selection['DMI_pred'] == 0:
        animal_input['DMI'] = calculate_Dt_DMIn_Lact1(animal_input['An_Parity_rl'], animal_input['Trg_MilkProd'], animal_input['An_BW'], animal_input['An_BCS'],
                                                      animal_input['An_LactDay'], animal_input['Trg_MilkFatp'], animal_input['Trg_MilkTPp'], animal_input['Trg_MilkLacp'])
    # Should be called 'Fd_DMIn' for consistency with R code
    diet_info['kg_intake'] = diet_info['%_DM_intake'] / 100 * animal_input['DMI']

########################################
# Step 2: Feed Based Calculations
########################################
    diet_info = get_nutrient_intakes(diet_info, feed_data, animal_input, equation_selection)

########################################
# Step 3: Microbial Protein Calculations
########################################
    Du_MiN_NRC2021_g = calculate_Du_MiCP_g(diet_info.loc['Diet', 'Fd_NDFIn'], animal_input['DMI'], diet_info.loc['Diet', 'Fd_St_kg/d'], diet_info.loc['Diet', 'Fd_CP_kg/d'], diet_info.loc['Diet', 'Fd_ADF_kg/d'], 
                                    diet_info.loc['Diet', 'Fd_ForWetIn'], diet_info.loc['Diet', 'Fd_RUPIn'], diet_info.loc['Diet', 'Fd_ForNDFIn'], diet_info.loc['Diet', 'Dt_RDPIn'])

########################################
# Step 4: Amino Acid Calculations
########################################
    AA_values = AA_calculations(Du_MiN_NRC2021_g, feed_data, diet_info)

########################################
# Step 5: Other Calculations
########################################
# Intake calculations that require additional steps, need results from other calculations or values that need to be calculated for other functions

    # This function could be renamed as it is doing all the DE intake calculations
    An_DEIn, An_DENPNCPIn, An_DETPIn, An_DigNDFIn, An_DEStIn, An_DEFAIn, An_DErOMIn, An_DENDFIn, Fe_CP, Fe_CPend_g = calculate_An_DEIn(diet_info.loc['Diet', 'Fd_DigNDFIn_Base'], diet_info.loc['Diet', 'Fd_NDFIn'], 
                                                                                                                    diet_info.loc['Diet', 'Fd_DigStIn_Base'], diet_info.loc['Diet', 'Fd_St_kg/d'], 
                                                                                                                    diet_info.loc['Diet','Fd_DigrOMtIn'], diet_info.loc['Diet', 'Fd_CPIn'], diet_info.loc['Diet', 'Fd_RUPIn'],
                                                                                                                    diet_info.loc['Diet', 'Fd_idRUPIn'], diet_info.loc['Diet', 'Fd_NPNCPIn'], diet_info.loc['Diet', 'Fd_DigFAIn'], 
                                                                                                                    Du_MiN_NRC2021_g, animal_input['An_BW'], animal_input['DMI'])

    # Predicted milk protein
    Mlk_NP_g, Du_idMiCP_g = calculate_Mlk_NP_g(AA_values, diet_info.loc['Diet', 'Fd_idRUPIn'], Du_MiN_NRC2021_g, An_DEIn, An_DETPIn, An_DENPNCPIn, An_DigNDFIn, An_DEStIn, An_DEFAIn, An_DErOMIn, An_DENDFIn, animal_input['An_BW'], animal_input['DMI'])

    # Net energy/Metabolizable energy
    An_NE, An_MEIn = calculate_An_NE(diet_info.loc['Diet', 'Fd_CPIn'], diet_info.loc['Diet', 'Fd_FAIn'], Mlk_NP_g, An_DEIn, An_DigNDFIn, Fe_CP, Fe_CPend_g, animal_input['DMI'], animal_input['An_BW'], animal_input['An_BW_mature'], 
                            animal_input['Trg_FrmGain'], animal_input['An_GestDay'], animal_input['An_GestLength'], animal_input['An_LactDay'], animal_input['Trg_RsrvGain'], animal_input['Fet_BWbrth'],
                            animal_input['An_AgeDay'], animal_input['An_Parity_rl'])
 
########################################
# Step 6: Requirement Calculations
########################################

    # Metabolizable Energy Requirements
    Trg_MEuse, An_MEmUse, An_MEgain, Gest_MEuse, Trg_Mlk_MEout = calculate_ME_requirement(animal_input['An_BW'], animal_input['DMI'], animal_input['Trg_MilkProd'], animal_input['An_BW_mature'], animal_input['Trg_FrmGain'], animal_input['An_GestDay'], 
                                                                                          animal_input['An_GestLength'], animal_input['An_AgeDay'], animal_input['Fet_BWbrth'], animal_input['An_LactDay'], animal_input['An_Parity_rl'],
                                                                                          animal_input['Trg_MilkFatp'], animal_input['Trg_MilkTPp'], animal_input['Trg_MilkLacp'], animal_input['Trg_RsrvGain'])
    # Metabolizable Protein Requirements
    An_MPuse_g_Trg, An_MPm_g_Trg, Body_MPUse_g_Trg, Gest_MPUse_g_Trg, Mlk_MPUse_g_Trg = calculate_MP_requirement(diet_info.loc['Diet', 'Fd_NDFIn'], animal_input['DMI'], animal_input['An_BW'], animal_input['An_BW_mature'], animal_input['Trg_FrmGain'],
                                                                                                                 animal_input['Trg_RsrvGain'], animal_input['An_GestDay'], animal_input['An_GestLength'], animal_input['An_AgeDay'], animal_input['Fet_BWbrth'],
                                                                                                                 animal_input['An_LactDay'], animal_input['An_Parity_rl'], animal_input['Trg_MilkProd'], animal_input['Trg_MilkTPp'])    

########################################
# Step 7: Performance Calculations
########################################

    # Predicted milk fat
    Mlk_Fat_g = calculate_Mlk_Fat_g(AA_values, diet_info.loc['Diet', 'Fd_FAIn'], diet_info.loc['Diet', 'Fd_DigC160In'], diet_info.loc['Diet', 'Fd_DigC183In'], animal_input['An_LactDay'], animal_input['DMI'])

    # Predicted milk yield
    Mlk_Prod_comp = calculate_Mlk_Prod_comp(Mlk_NP_g, Mlk_Fat_g, An_DEIn, animal_input['An_LactDay'], animal_input['An_Parity_rl']) 
  
    # MP Allowable Milk
    Mlk_Prod_MPalow = calculate_Mlk_Prod_MPalow(An_MPuse_g_Trg, Mlk_MPUse_g_Trg, diet_info.loc['Diet', 'Fd_idRUPIn'], Du_idMiCP_g, animal_input['Trg_MilkTPp'])

    # NE Allowable Milk
    Mlk_Prod_NEalow = calculate_Mlk_Prod_NEalow(An_MEIn, An_MEgain, An_MEmUse, Gest_MEuse, animal_input['Trg_MilkFatp'], animal_input['Trg_MilkTPp'], animal_input['Trg_MilkLacp'])

########################################
# Step 8: *Temporary* Add values of interest to list
########################################
    # Milk Fat %
    milk_fat = (Mlk_Fat_g / 1000) / Mlk_Prod_comp *100
    # Milk Protein %
    milk_protein = (Mlk_NP_g / 1000) / Mlk_Prod_comp *100

    model_results = {
    'milk_fat': milk_fat,
    'milk_protein': milk_protein,
    'Mlk_Prod_comp': Mlk_Prod_comp,
    'Mlk_Prod_MPalow': Mlk_Prod_MPalow,
    'Mlk_Prod_NEalow': Mlk_Prod_NEalow,
    'Trg_MEuse': Trg_MEuse,
    'An_MPuse_g_Trg': An_MPuse_g_Trg
    }

    output = {
    'diet_info': diet_info,
    'animal_input': animal_input,
    'feed_data': feed_data,
    'equation_selection': equation_selection,
    'AA_values': AA_values,
    'model_results': model_results
}
    # Return so they can be viewed in environment
    return output



# Display results, temporary
def display_diet_values(df):
    components = ['Fd_CP', 'Fd_RUP_base', 'Fd_NDF', 'Fd_ADF', 'Fd_St', 'Fd_CFat', 'Fd_Ash']
    rows = []

    for component in components:
        percent_diet = round(df.loc['Diet', component + '_%_diet']) #.values[0], 2)
        kg_diet = round(df.loc['Diet', component + '_kg/d'])    #.values[0], 2)
        rows.append([component, percent_diet, kg_diet])

    headers = ['Component', '% DM', 'kg/d']

    table = pd.DataFrame(rows, columns = headers)

    return table


# Function to add ui.div with new ingredenient and percentage
def insert_new_ingredient(current_iter, feed_choices, feed_selected = None, perc_selected = 0):
    newItemDiv = ui.div(
            {"id" : "userfeed_" + current_iter}, # div ID
            ui.row(
                ui.column(4, ui.input_selectize("item_" + current_iter,
                                                #  "Choose feeds to use in ration:",
                                                label = "",
                                                choices = feed_choices,
                                                selected = feed_selected,
                                                multiple = False)),
                ui.column(2, ui.input_numeric('perc_' + current_iter, 
                            #  label="Enter percentage:", 
                            label = "",
                             min=0, max=100, value = perc_selected)),
            )
        )
    ui.insert_ui(newItemDiv, 
                 selector = "#item_input", 
                 where = "beforeEnd")

##############################################################################################
# Shiny App
##############################################################################################

app_ui = ui.page_navbar(
    # shinyswatch.theme.flatly(),
        ui.nav("Feed Inputs",
           ui.panel_title("Feed inputs"),
           ui.output_ui("item_input"),
           ui.row(
               ui.column(4, ui.input_action_button("add_button", "Add another feed")),
               ui.column(4, ui.input_action_button("add_demo_diet", "Add demo diet"))
           ),
           ui.br(),
           ui.output_table("user_selections"),
           ),
        ui.nav("Animal Inputs",
               # There are 3 NDF Digestability estimates, 0=Lg based, 1=DNDF48 for forages, 2=DNDF48 for all
               ui.input_radio_buttons("Use_DNDF_IV", "Use_DNDF_IV (NASEM default is Lg based)",
                                      {0:"Lg based", 
                                       1:"DNDF48 for forages", 
                                       2:"DNDF48 for all"}),
               # This selection should move somewhere else eventually
               # # 0 = use DMI prediction, 1 = user entered DMI
               ui.input_radio_buttons("DMI_pred", "DMI_pred", {0:"use DMI prediction", 1:"use DMI entered below"}, selected=1),
               ui.panel_title("Animal Inputs"),
                ui.input_numeric("An_Parity_rl", "An_Parity_rl: Value from 1-2 representing % of multiparous cows, 2 = 100% multiparous", 1, min=1, max=2),
                ui.input_numeric("Trg_MilkProd", "Trg_MilkProd: Target milk production (kg/d)", 25.062, min=0),
                ui.input_numeric("An_BW", "An_BW: Animal bodyweight (kg)", 624.795, min=0),
                ui.input_numeric("An_BCS", "An_BCS: Animal body condition score (0-5)", 3.5, min=0, max=5),
                ui.input_numeric("An_LactDay", "An_LactDay: day of lactation/days in milk", 100, min=0),
                ui.input_numeric("Trg_MilkFatp", "Trg_MilkFatp: Target milk fat %", 4.55, min=0),
                ui.input_numeric("Trg_MilkTPp", "Trg_MilkTPp: Target milk true protein %", 3.66, min=0),
                ui.input_numeric("Trg_MilkLacp", "Trg_MilkLacp: Target milk lactose %", 4.85, min=0),
                ui.input_numeric("DMI", "DMI: Dry matter intake (kg/d)", 24.521, min=0),
                ui.input_numeric("An_BW_mature", "An_BW_mature: Animal mature bodyweight (kg)", 700, min=0),
                ui.input_numeric("Trg_FrmGain", "Trg_Frm_Gain: Target gain in body frame weight (kg fresh weight/d)", 0.19, min=0),
                ui.input_numeric("An_GestDay", "An_GestDay: Day of gestation (d)", 46, min=0),
                ui.input_numeric("An_GestLength", "An_GestLength: gestation length (d)", 280, min=0),
                ui.input_numeric("Trg_RsrvGain", "Trg_RsrvGain: Target gain or loss of body reserves (kg fresh weight/d)", 0, min=0),
                ui.input_numeric("Fet_BWbrth", "Fet_BWbrth: Calf birth weight (kg)", 44.1, min=0),
                ui.input_numeric("An_AgeDay", "An_AgeDay: Animal age (d)", 820.8, min=0),
                ui.input_numeric("An_305RHA_MlkTP", "An_305RHA_MlkTP (280 hard coded, UI not used - need to update code)", 280, min = 0)
                ),
        ui.nav("Run Model",
               ui.panel_title("Run NASEM model"),
               ui.br(),
               ui.input_action_button("btn_run_model", "Run NASEM model"),
               ui.h4("Model Outputs"),
               ui.output_table('diet_data_model'),
               ui.output_table('model_data'),
               ui.br(),
               ui.br(),
               ui.h4("Confirm Model inputs:"),
               ui.output_table('animal_inputs_table'),
               ui.output_table('equation_selection_table'),
               ui.output_table('raw_diet_info'),
               ui.br(),
               ui.h4('extended output'),
               ui.output_table('feed_data'),
               ui.output_table('diet_info')
               
               ),   
    title= "NASEM for python",
    id='navbar_id',
    inverse = True


)

def server(input, output, session):
    # Initialize reactive values to store user selections
    user_feeds = reactive.Value(['item_1'])
    user_percentages = reactive.Value(['perc_1'])
    
    #used for demo data
    feed_selected = reactive.Value(None)
    perc_selected = reactive.Value(0)

    @reactive.Calc
    def iterate_new_ingredient():
        current_iter =  str(len(user_feeds()) + 1)

        # feed_selected = None
        # perc_selected = 0

        # copy, append and re-set items and percentages, to keep track of inputs
        xout = user_feeds().copy()
        xout.append('item_' + current_iter)
        user_feeds.set(xout)

        pout = user_percentages().copy()
        pout.append('perc_' + current_iter)
        user_percentages.set(pout)

        insert_new_ingredient(current_iter = current_iter, 
                              feed_choices = unique_fd_list, # global
                              feed_selected=feed_selected(),
                              perc_selected=perc_selected()
                              )
        return current_iter
        
    # Generate a new item input whenever the "Add another item" button is clicked
    @reactive.Effect
    @reactive.event(input.add_button)
    def _():
        iterate_new_ingredient()
        


  
    
    @reactive.Effect
    @reactive.event(input.add_demo_diet)
    def _():
        ui.update_selectize(id = 'item_1', selected = "Canola meal")
        ui.update_numeric(id = 'perc_1', value = 10)

        demo_feeds = ['Alfalfa meal', 'Corn silage, typical', 'Barley grain, dry, ground', 'Pasture, grass']
        demo_percs = [16.3, 40, 16.3, 15]

        for feed, perc in  zip(demo_feeds, demo_percs):
            # Can't pass arguments to event.Calc ? - using reactives
            feed_selected.set(feed)
            perc_selected.set(perc)
            iterate_new_ingredient()
        
        # reset to defaults
        feed_selected.set(None)
        perc_selected.set(0)

        # animal:
        # change page that is being viewed:
        ui.update_navs("navbar_id", selected="Animal Inputs")

        anim_list = ["An_Parity_rl", "Trg_MilkProd", "An_BW", "An_BCS", "An_LactDay", "Trg_MilkFatp", "Trg_MilkTPp", "Trg_MilkLacp", "DMI", "An_BW_mature", "Trg_FrmGain", "An_GestDay", "An_GestLength", "Trg_RsrvGain", "Fet_BWbrth", "An_AgeDay"]
        anim_defaults = [2, 35, 700, 3, 150, 3.8, 3.10, 4.85, 24.5, 700, 0.19, 46, 280, 0, 44.1, 1620]
        
        for an_item, an_val in zip(anim_list, anim_defaults):
            ui.update_numeric(id = an_item, value = an_val)

        # remove button
        ui.remove_ui(selector="div:has(> #add_demo_diet)")

    


    @output
    @render.ui
    def item_input():
        # Generate initial item input
        itemInput = ui.div(
            {"id" : "userfeed_1" },
            ui.row(
                ui.column(4, ui.input_selectize( "item_1" ,
                                                 "Choose feeds to use in ration:",
                                                unique_fd_list,
                                                multiple = False)),
                ui.column(2, ui.input_numeric('perc_1', 
                             label="Enter percentage:", 
                             min=0, max=100, value=0)),
            )
        )
        return itemInput

    @reactive.Calc
    def get_diet_info():
    #     # Get items from input by name
        items = [getattr(input, x) for x in user_feeds()]
        perc = [getattr(input, x) for x in user_percentages()]
        
        # This is required to convert lists of reactive values to data frame.
        tmp_diet_info = pd.DataFrame({'Feedstuff' : [str(x()) for x in items], 
                             '%_DM_user' : [float(x()) for x in perc]})
        
        tmp_diet_info['Feedstuff'] = tmp_diet_info['Feedstuff'].str.strip()

        tmp_diet_info['Index'] = tmp_diet_info['Feedstuff']
        tmp_diet_info = tmp_diet_info.set_index('Index') 

        return tmp_diet_info
    
    @reactive.Calc
    def format_diet_info():
        # create a copy is important, or it will override `tmp_diet_info` from get_diet_info()
        df_out = get_diet_info().copy()
        # add total row: 
        total_row = df_out.sum(numeric_only=True)
        total_row['Feedstuff'] = 'Total'
        df_out.loc['Total'] = total_row
        
        return df_out


    # render table by calling the calc function for it's output       
    @output
    @render.table
    def user_selections():
        return format_diet_info()

    @output
    @render.table
    def raw_diet_info():
        return get_diet_info()


    ###########################################
    # Animal inputs
    @reactive.Calc
    def animal_input():
        return {
                'An_Parity_rl': input.An_Parity_rl(),
                'Trg_MilkProd': input.Trg_MilkProd(),
                'An_BW': input.An_BW(),
                'An_BCS': input.An_BCS(),
                'An_LactDay': input.An_LactDay(),
                'Trg_MilkFatp': input.Trg_MilkFatp(),
                'Trg_MilkTPp': input.Trg_MilkTPp(),
                'Trg_MilkLacp': input.Trg_MilkLacp(),
                'DMI': input.DMI(),
                'An_BW_mature': input.An_BW_mature(),
                'Trg_FrmGain': input.Trg_FrmGain(),
                'An_GestDay': input.An_GestDay(),
                'An_GestLength': input.An_GestLength(),
                'Trg_RsrvGain': input.Trg_RsrvGain(),
                'Fet_BWbrth': input.Fet_BWbrth(),
                'An_AgeDay': input.An_AgeDay()
                }

    @output
    @render.table
    def animal_inputs_table():
        return pd.DataFrame(animal_input().items(), columns=['Variable Name', 'Value'])

    @reactive.Calc
    def equation_selection():
        return {'Use_DNDF_IV' : input.Use_DNDF_IV(), 'DMI_pred': input.DMI_pred()}
    
    @output
    @render.table
    def equation_selection_table():
        return pd.DataFrame(equation_selection().items(), columns=['Variable Name', 'Value'])
    
    #######################################################
    # Run Model

    @reactive.Calc
    @reactive.event(input.btn_run_model)
    def NASEM_out():
        return NASEM_model(get_diet_info(), animal_input(), equation_selection())
    
    @output
    @render.table
    def model_data():
        return pd.DataFrame(NASEM_out()["model_results"], index=['Value']).T.reset_index()

    @output
    @render.table
    def diet_data_model():
        return display_diet_values(NASEM_out()["diet_info"])
    
    @output
    @render.table
    def diet_info():
        return NASEM_out()['diet_info']
    
    @output
    @render.table
    def feed_data():
        return NASEM_out()['feed_data']


app = App(app_ui, server)
