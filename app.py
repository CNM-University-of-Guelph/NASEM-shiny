from shiny import App, reactive, render, ui, req
import shiny.experimental as x
from shinywidgets import output_widget, render_widget, reactive_read

import pandas as pd
# from asyncio import sleep
# import shinyswatch
#import pdb #like browser()

# from itables.shiny import DT
# import itables.options as opt
# opt.maxBytes=0
# opt.maxRows=300

# Grid Table, has edits and row/column/cell selection - see: https://github.com/bloomberg/ipydatagrid/blob/main/examples/Selections.ipynb
from ipydatagrid import DataGrid


# pip install git+https://github.com/CNM-University-of-Guelph/NASEM-Model-Python
import nasem_dairy as nd

from utils import display_diet_values, get_feed_library_df


# get list of feeds available from the feed library in db
# used for user selection in shiny
unique_fd_list = nd.fl_get_feeds_from_db('diet_database.db')
var_desc = pd.read_csv("./variable_descriptions.csv").query("Description != 'Duplicate'")



# Function to add ui.div with new ingredient and percentage
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

    ui.nav("Feed Library",
        x.ui.card(
            x.ui.layout_column_wrap('200px',
                ui.p('View column groups:'),
                ui.input_switch('cols_show_all', 'Show all columns')
                ),
            ui.panel_conditional( "!input.cols_show_all",
                x.ui.layout_column_wrap(1/5,                  
                    ui.input_switch('cols_common', 'Commonly used',  value=True),                    
                    ui.input_switch("cols_amino_acids", "Amino Acids"),
                    ui.input_switch('cols_fatty_acids', 'Fatty Acids'),
                    ui.input_switch('cols_vitamins', 'Vitamins'),
                    ui.input_switch('cols_minerals', 'Minerals')
                    )
                )
            ),
            
        
        x.ui.card(
            x.ui.layout_sidebar(
                x.ui.sidebar(
                    ui.p("Feeds selected by user:"),
                    ui.output_data_frame('user_selected_feed_names'),
                    ui.br(),
                    ui.input_action_button('reset_user_selected_feed_names', "Clear list")
                ),
                ui.p("Click on a row in the table below to store the Feed Name in the side panel. This is a temporary list that will be shown you create your diet in the next step."),
                output_widget('grid_feed_library'),
            ),
            full_screen=True
        ),
                x.ui.card(
            ui.p("Advanced:"),
            ui.input_checkbox("hide_calf_feeds", "Hide calf related feeds:", True),
            full_screen=False
        ),
        ),
        ui.nav("Feed Inputs",
           ui.panel_title("Feed inputs"),
           x.ui.card(
            x.ui.layout_sidebar(
                x.ui.sidebar(
                    ui.p("Feeds selected by user:"),
                    ui.output_data_frame('user_selected_feed_names_2'),
                    ui.br(),
                    ui.input_action_button('reset_user_selected_feed_names_2', "Clear list")
                ),
                ui.output_ui("item_input"),
                ui.row(
                        ui.column(4, ui.input_action_button("add_button", "Add another feed")),
                        ui.column(4, ui.input_action_button("add_demo_diet", "Add demo diet"))
           ),
           ui.br(),
           ui.output_table("user_selections"),
            )
            ),

           
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
                ui.input_numeric("An_305RHA_MlkTP", "An_305RHA_MlkTP", 280, min = 0)
                ),
        ui.nav("Run Model",
               ui.panel_title("Run NASEM model"),
               ui.br(),
               ui.input_action_button("btn_run_model", "Run NASEM model"),
               ui.h4("Model Outputs"),
               ui.h5('Diet:'),
               ui.output_table('diet_data_model'),
               ui.h5('Key model predictions:'),
               ui.output_table('key_model_data'),
               ui.h5('All model predicitons'),
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
    inverse = True,
    # fillable=False,
    # *****************************************************************************************************
    # Current glitch prevents the filters working on feed library widget when using a x.ui. page_fillable() 
    # if fillable=False, but a sidebar is defined, it also reverts to True, so glitches.
    # Implementing copies of same sidebar on each page for now.
    # sidebar=
    #     x.ui.sidebar(
    #                 ui.p("Feeds selected by user from Feed Library:"),
    #                 ui.output_data_frame('user_selected_feed_names'),
    #                 ui.br(),
    #                 ui.input_action_button('reset_user_selected_feed_names', "Clear list")
    #             )


)


# ----------------------------------------------------------------------------------------------------------------
# Server

def server(input, output, session):
    #######################################################
    # Feed Library
    #######################################################

    def rename_df_cols_Fd_to_feed(df: pd.DataFrame) -> pd.DataFrame:
        '''
        Rename columns of the feed df to replace Fd_ with 'Feed_' 
        Takes a df and returns a df.
        '''
        return df.rename(columns= {col: f'Feed {col[3:]}' if col.startswith('Fd_') else col for col in df.columns} )

    
    df_full =  rename_df_cols_Fd_to_feed(get_feed_library_df('diet_database.db'))

    ########################
    # Filter columns based on user input

    # df_feed_lib_userfriendly.loc[:,'Feed DM':'Feed WSC']
    
    @reactive.Calc
    def df_feed_lib_userfriendly():
        '''
        Create's a smaller version of data for viewing only, based on user input related to :
        - Columns grouped by: 'Commonly used',  "Amino Acids", 'Fatty Acids', 'Vitamins', 'Minerals'
            - Commonly used refers to ID columns + DM, DE_Base, ADF, NDF, CP, RUP, NPN_CP, Ash, Ca, P, Mg
        - Remove all feeds related to calves e.g. milk or calf starter
        '''

        # calves:        
        if input.hide_calf_feeds() == True:
            df_calf_filter = (
                df_full
                .query("`Feed Category` != 'Calf Liquid Feed'")
                .query("`Feed Name`" + ".str.contains('Calf', case=False, na=False) == False")
        ) 
        else:
            df_calf_filter = df_full

        # split dataframe into their groups
        df_ID = df_calf_filter.loc[:,['Feed Name','Feed Category', 'Feed Type']]

        if input.cols_common() == True:
            df_common = df_calf_filter.loc[:,['Feed DM', 'Feed DE_Base', 'Feed ADF', 'Feed NDF', 'Feed DNDF48_NDF', 'Feed CP', 'Feed RUP_base', 'Feed NPN_CP', 'Feed Ash', 'Feed Ca', 'Feed P', 'Feed Mg', 'Feed K']]
        else:
            df_common = pd.DataFrame()

        
        if input.cols_amino_acids() == True:
            df_AA = df_calf_filter.loc[:,'Feed Arg_CP':'Feed Val_CP']
        else:
            df_AA = pd.DataFrame()
        
        if input.cols_fatty_acids() == True:
            df_FA = df_calf_filter.loc[:,'Feed CFat':'Feed OtherFA_FA'].drop('Feed Ash', axis =1)
        else:
            df_FA = pd.DataFrame()
        
        if input.cols_vitamins() == True:
            df_vit = df_calf_filter.loc[:,'Feed B_Carotene':'Feed VitE']
        else:
            df_vit = pd.DataFrame()

        if input.cols_minerals() == True:
            if input.cols_common() == True:
                df_minerals = df_calf_filter.loc[:,'Feed Ca':'Feed Zn'].drop(['Feed Ca', 'Feed P', 'Feed Mg', 'Feed K'], axis=1)
            else:
                df_minerals = df_calf_filter.loc[:,'Feed Ca':'Feed Zn']
        else:
            df_minerals = pd.DataFrame()


        if input.cols_show_all() == True:
            df_out = df_calf_filter
        else:
            df_out = df_ID.join([df_common, df_AA, df_FA, df_vit, df_minerals])

        
        return df_out

    



    ########################
    # Create DataGrid and render it
    # help for DataGrid attributes: https://github.com/bloomberg/ipydatagrid/blob/main/ipydatagrid/datagrid.py#L214
    @reactive.Calc
    def datagrid_feed_lib():
        return DataGrid(df_feed_lib_userfriendly(), 
                            auto_fit_columns = True,
                            selection_mode="row",
                            editable = False)
    
    @output
    @render_widget
    def grid_feed_library():
        return datagrid_feed_lib()

    ########################
    # Get the user selections from DataGrid
    # These should be stored to a reactive list so that they aren't lost if table filters change

    # initiliase reactive value that contains a list
    feed_library_index_stored = reactive.Value([])

    @reactive.Calc
    def prepare_user_selected_feed_names():
        '''
        Handles the specific selections from a datagrid to return a dataframe that is rendered 
        in the sidepanel to show users which feeds they've selected. 
        This is useful when building diets.
        '''
        # This is shiny version of writing this: datagrid_feed_lib.selections
        # or selected_cells, etc.
        row_selections = reactive_read(datagrid_feed_lib(), "selections")
        row_index = [list(range(row_number['r1'], row_number['r2']+1)) for row_number in row_selections]
        flattened_index = [i for row in row_index for i in row]
        print(flattened_index)
       
        return(flattened_index)
        # return(fd_lib_stored_copy)
        # return(feed_library_index_stored)
    
    
    @reactive.Effect
    def _():
        # take a dependency on the user selection, which updates every time a cell is clicked
        prepare_user_selected_feed_names()
        
        # then, execute this code but preventing other code taking a dependency on it - prevents infinite loop
        with reactive.isolate():
            fd_lib_stored_copy = feed_library_index_stored().copy()
            fd_lib_stored_copy.extend(prepare_user_selected_feed_names())
            # remove duplicates (by converting to set) and then set the reactiveValue as this new list

            feed_library_index_stored.set(list(set(fd_lib_stored_copy)))

    @reactive.Effect
    @reactive.event(input.reset_user_selected_feed_names, input.reset_user_selected_feed_names_2)
    def _():
        feed_library_index_stored.set([])


    @output
    @render.data_frame
    def user_selected_feed_names():
        
        user_selected_feeds = (df_feed_lib_userfriendly()
                               .reset_index(drop = True) # reset's index to match a 'row number' from selection with index (after filtering)
                               .loc[feed_library_index_stored(),'Feed Name'])
        return pd.DataFrame(user_selected_feeds)
    
    # ***********
    # Copy of above due to glitch
    @output
    @render.data_frame
    def user_selected_feed_names_2():
        user_selected_feeds = (df_feed_lib_userfriendly()
                               .reset_index(drop = True) # reset's index to match a 'row number' from selection with index (after filtering)
                               .loc[feed_library_index_stored(),'Feed Name'])
        return pd.DataFrame(user_selected_feeds)






    #######################################################
    # Feed Inputs
    #######################################################

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
        
    ########################
    # Add Demo diet
    @reactive.Effect
    @reactive.event(input.add_demo_diet)
    def _():
        ui.update_selectize(id = 'item_1',choices = unique_fd_list, selected = "Canola meal")
        ui.update_numeric(id = 'perc_1', value = 11)
        
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
        # ui.update_navs("navbar_id", selected="Animal Inputs")

        anim_list = ["An_Parity_rl", "Trg_MilkProd", "An_BW", "An_BCS", "An_LactDay", "Trg_MilkFatp", "Trg_MilkTPp", "Trg_MilkLacp", "DMI", "An_BW_mature", "Trg_FrmGain", "An_GestDay", "An_GestLength", "Trg_RsrvGain", "Fet_BWbrth", "An_AgeDay", "An_305RHA_MlkTP"]
        anim_defaults = [2, 35, 700, 3, 150, 3.8, 3.10, 4.85, 24.5, 700, 0.19, 46, 280, 0, 44.1, 1620, 280]
        
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
    #   # Get items from input by name
    # each 'feed' and '%' value is stored in these reactives (named 'item_1', etc) which means we can iterate through them and store their values in a list when we need them
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


    #######################################################
    # Animal inputs
    #######################################################
    # this takes each individual input from UI and stores it in a dictionary that can be used by model.
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
                'An_AgeDay': input.An_AgeDay(),
                'An_305RHA_MlkTP': input.An_305RHA_MlkTP()
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
    #######################################################
    # each of the inputs has been formatted from UI inputs to the required type needed by teh model.
    # e.g. currently diet_info is a df whereas animal_input is a dict.
    # Might make sense to use all dicts???

    @reactive.Calc
    @reactive.event(input.btn_run_model)
    def NASEM_out():
        return nd.NASEM_model(get_diet_info(), animal_input(), equation_selection(), 'diet_database.db', nd.coeff_dict)
    
    
    @reactive.Calc
    def full_model_output():
        '''
        Prepare model output data to be rendered or filtered further
        '''
        model_df = (pd.DataFrame
            .from_dict(
                NASEM_out()['model_results_full'], orient='index', columns=['Value']
                )
            .reset_index(
                names="Model Variable"
                )
            .assign(
                Value = lambda df: df['Value'].round(3)
                )
            .merge(var_desc, how = 'left')
            )
        return model_df

    @output
    @render.table
    def key_model_data():
        # Variables to return:
        vars_return = ['Mlk_Prod_comp','milk_fat', 'milk_protein', 'Mlk_Prod_MPalow', 'Mlk_Prod_NEalow', 'An_MEIn', 'Trg_MEuse', 'An_MPIn', 'An_MPuse_g_Trg']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        
    
    @output
    @render.table
    def model_data():
        return full_model_output()

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


app = App(app_ui, server,  debug=False)
