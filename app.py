from shiny import App, reactive, render, ui, req
import shiny.experimental as x
from shinywidgets import output_widget, render_widget, reactive_read
from datetime import date
import io
import pandas as pd
import shinyswatch
# import pdb #like browser()


# Grid Table, has edits and row/column/cell selection - see: https://github.com/bloomberg/ipydatagrid/blob/main/examples/Selections.ipynb
from ipydatagrid import DataGrid


# pip install git+https://github.com/CNM-University-of-Guelph/NASEM-Model-Python
import nasem_dairy as nd

from utils import display_diet_values, rename_df_cols_Fd_to_feed, DM_intake_equation_strings, get_unique_feed_list, get_teaching_feeds
from generate_report import generate_report


# Load global resources
feed_library_default = pd.read_csv('./NASEM_feed_library.csv').sort_values("Fd_Name")

var_desc = pd.read_csv("./variable_descriptions.csv").query("Description != 'Duplicate'")



# Function to add ui.div with new ingredient and percentage
def insert_new_ingredient(current_iter, feed_choices, feed_selected = None, kg_selected = 0):
    newItemDiv = ui.div(
            {"id" : "userfeed_" + current_iter}, # div ID
            ui.row(
                ui.column(4, ui.input_selectize("item_" + current_iter,
                                                #  "Choose feeds to use in ration:",
                                                label = "",
                                                choices = feed_choices,
                                                selected = feed_selected,
                                                multiple = False)),
                ui.column(2, ui.input_numeric('kg_' + current_iter, 
                            label = "",
                            min=0, 
                            max=100, 
                            step = 0.2,
                            value = kg_selected)),
            )
        )
    ui.insert_ui(newItemDiv, 
                 selector = "#item_input", # place the new UI's below the initial item input
                 where = "beforeEnd")
    

def insert_demo_button():
    newItemDiv = ui.div(
            {"id" : "demo_diet_button_div"}, # div ID
            ui.row(
                ui.column(4, ui.input_action_button("add_demo_diet", "Add demo diet", class_='btn-info'))
            )
            )
    ui.insert_ui(newItemDiv, 
                 selector = "#item_input", # place the new UI's below the initial item input
                 where = "beforeBegin")
    
def remove_ingredient(current_iter):
    ui.remove_ui(selector="div#userfeed_"+str(current_iter))

##############################################################################################
# Shiny App
##############################################################################################

app_ui = ui.page_navbar(
    #  shinyswatch.theme.materia(),

    ui.nav(
        'Welcome',
        ui.h2("Nutrient Requirements of Dairy Cattle - 8th Edition (NASEM 2021)"),
        ui.br(),
        ui.p(
            "This app is a simplified version of the model described in the 8th Edition of the ", 
            ui.a('Nutrient Requirements of Dairy Cattle book.', 
                href = 'https://www.nationalacademies.org/our-work/nutrient-requirements-of-dairy-cattle-8th-edition',
                target = "_blank")
            ),
        ui.p("The current version is being developed for teaching and research only. This software should not be used for on-farm or commercial decisions."),
        ui.br(),ui.br(),
        ui.panel_well(
            ui.h4("Acknowledgements"),
            ui.p('This Shiny App was written in python by Dave Innes to interact with a version of the model translated into python by Braeden Fieguth from the original R code that is included with the book ',
                ui.a('and online.', 
                    href = 'https://nap.nationalacademies.org/resource/25806/Installation_Instructions_NASEM_Dairy8.pdf'),
                    target = "_blank"
                ),
            ui.p("The latest version of the underlying code can be viewed ", 
                 ui.a('on GitHub.',
                       href = 'https://github.com/CNM-University-of-Guelph/NASEM-Model-Python',
                       target = '_blank')
                ),
        x.ui.card_image('./absc_logo.png', height='120px', width = '300px', fill=False)
        )
        ), 


    ui.nav(
        "Inputs",
        ui.navset_tab_card( 
            ui.nav(
                'Animal Description',
                ui.input_selectize(
                    'An_Breed', 
                    label = 'Select breed:', 
                    choices = {'Holstein':'Holstein', 'Jersey':'Jersey'}, 
                    selected = 'Holstein'
                ),
                ui.input_selectize(
                    'An_StatePhys', 
                    label = 'Select physiological state:', 
                    choices = {'Lactating Cow': 'Lactating Cow', 'Dry Cow': 'Dry Cow', 'Calf':'Calf'}, 
                    selected = 'Lactating Cow'
                    ),
                ui.br(),

                ui.input_numeric("An_BW", "Animal bodyweight (kg):", 700, min=0),
                ui.input_numeric("An_BW_mature", "Animal mature bodyweight (kg):", 700, min=0),

                ui.input_numeric("An_BCS", "Animal body condition score (0-5):", 3, min=0, max=5),
                ui.br(),
                
                # converted to days in server:
                ui.input_numeric("An_AgeMonth", "Animal age (months):", 54, min=0),
                
                ui.input_numeric("An_Parity_percent_first", "Percent of cows in first lactation:", 33, min=0, max=100),
                
                
                
            ),
            ui.nav(
                'Animal Management',
                ui.input_numeric("An_LactDay", "Average days in milk:", 100, min=0),
                ui.input_numeric("An_GestDay", "Average days pregnant (d)", 46, min=0),
                ui.br(),
                ui.p(
                    ui.em("Body frame weight refers to the real growth of a younger animal. Body reserves refers to any fluctuations in body weight of a mature animal, e.g. due to lactation.")
                    ),
                ui.input_numeric("Trg_FrmGain", "Target gain in body frame weight (kg fresh weight/d)", 0.60, min=0),
                ui.input_numeric("Trg_RsrvGain", "Target gain or loss of body reserves (kg fresh weight/d)", 0.10, min=0),

                ),

            ui.nav(
                'Milk Production',
                ui.h3("Milk Yield"),
                ui.input_numeric("Trg_MilkProd", "Target milk production (kg/d)", 35, min=0),
                
                ui.br(),
                
                ui.h3("Milk Components"),
                ui.input_numeric("Trg_MilkFatp", "Target milk fat %", 3.8, min=0, ),
                ui.input_numeric("Trg_MilkTPp", "Target milk true protein %", 3.1, min=0, ),
                ui.input_numeric("Trg_MilkLacp", "Target milk lactose %", 4.85, min=0, )
                ),


            ui.nav(
                'Advanced',
                
                ui.panel_title("Equation selections"),
                
                # There are 3 NDF Digestability estimates, 0=Lg based, 1=DNDF48 for forages, 2=DNDF48 for all
                ui.input_radio_buttons(
                    "Use_DNDF_IV", 
                    "Use_DNDF_IV (NASEM default is Lg based)",
                    choices = {0:"Lg based", 1:"DNDF48 for forages", 2:"DNDF48 for all"}, # type: ignore
                    ), 

                ui.input_selectize(
                    "DMIn_eqn",
                    label = "Select DM Intake equation to use for predicting intake on Diet page (default is 'lactating, cow factors only'). Does not change model, user input DMI is always used in this app.",
                    choices = DM_intake_equation_strings(),
                    selected = 8, # type: ignore
                    multiple = False
                    ),
                
                ui.input_numeric("An_GestLength", "Gestation length (d)", 280, min=0),
                ui.input_numeric("Fet_BWbrth", "Calf birth weight (kg)", 44.1, min=0),

                ui.input_numeric("An_305RHA_MlkTP", "Milk True Protein rolling heard average (kg/305 d)", 396, min = 0),
                
                )
            )

        ),
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
                    ui.input_switch('use_teaching_fd_library', 'Use teaching feed library', value=True),
                    ui.br(),
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


        ui.nav("Diet",
                # ui.panel_title("Diet"),
                x.ui.card(
                    x.ui.layout_sidebar(
                        x.ui.sidebar(
                            ui.p("Feeds selected by user:"),
                            ui.output_data_frame('user_selected_feed_names_2'),
                            ui.br(),
                            ui.input_action_button('reset_user_selected_feed_names_2', "Clear list")
                            ),
                        
                        x.ui.card(
                            ui.row( 
                                ui.column(4, ui.input_action_button('btn_calc_DMI', 'Predict DMI (from animal inputs)', class_='btn-secondary'), ui.output_text('predicted_DMI')),
                                ui.column(3, ui.input_numeric("DMI", "Target dry matter intake (kg/d)", 25, min=0)),
                                ui.column(2, ui.p('Total diet intake (kg/d):'), ui.output_text('diet_total_intake')),
                                ui.column(2, ui.p('Difference (kg):'), ui.output_text("intake_difference")),
                            ),
                        ),
                        
                       ui.br(),
                       ui.h2("Formulate ration:"),
                        ui.row(
                                ui.column(4, ui.input_action_button("add_demo_diet", "Add demo diet", class_='btn-info'))
                            ),
                       ui.output_ui("item_input"),
                        ui.row(
                                ui.column(4, ui.input_action_button("add_button", "Add another feed", class_='btn-success')),
                                ui.column(4, ui.input_action_button("btn_reset_feeds", "Reset ingredients list"))
                            ),
                        ui.br(), ui.br(), ui.br(), ui.br()
                            
                       
                     
                        # ui.br(),
                        # ui.output_table("user_selections")
                    )
                ),
            ),
        ui.nav("Run Model",
                ui.panel_title("Run NASEM model"),
                ui.br(),
                ui.row(
                    ui.column(3, ui.input_action_button("btn_run_model", "Run NASEM model", class_='btn-warning')),
                    ui.column(3, ui.br()),
                    ui.column(3, ui.download_button("btn_download_report", "Download Report")),
                    

                ),

                
                ui.br(),

                ui.navset_tab_card(
                    ui.nav(
                        'Model Evaluation',
                        ui.h5('Milk production estimates:'),
                        ui.output_table('key_model_data_milk'),
                        ui.br(),
                        ui.h5('Milk production allowed (kg/d) from available NE or MP:'),
                        ui.output_table('key_model_data_allowable_milk'),
                        ui.br(),
                        ui.h5('Metabolisable energy balance:'),
                        ui.output_table('key_model_data_ME'),
                        ui.br(),
                        ui.h5('Metabolisable protein balance:'),
                        ui.output_table('key_model_data_MP'),
                        ui.br(),


                        ),

                    ui.nav(
                        'Diet Analysis',
                        ui.h5('Diet summary:'),
                        ui.output_table('diet_data_model'),
                        ui.br(),

                        ui.h5('NEL:'),
                        ui.output_table('key_model_data_NEL'),
                        ui.br(),

                        ui.h5('DCAD:'),
                        ui.output_table('key_model_data_DCAD'),
                        ui.br(),

                        ui.h5("Ration ingredients:"),
                        ui.output_table('raw_diet_info'),
                    ),
                    ui.nav(
                        'Vitamins and Minerals',
                        ui.output_table('mineral_intakes')

                        ),
                    ui.nav(
                        "Energy - teaching",
                        ui.output_table('key_model_data_energy_teaching')
                        ),

                    ui.nav(
                        'Advanced',
                        ui.h5('All model predicitons'),
                        ui.output_table('model_data'),
                        ui.br(),
                        ui.h4('extended output'),
                        ui.output_table('diet_info'),
                        ui.h4("Confirm Model inputs:"),
                        ui.output_table('animal_input_table_comparison'),
                        ui.output_table('equation_selection_table')
                    )
                ),

                # ui.h4("Model Outputs"),
                # ui.br(),
                # ui.br(),
                # ui.h4("Confirm Model inputs:"),
                # ui.output_table('animal_inputs_table'),
                # ui.output_table('equation_selection_table'),


                ), 
        title= "NASEM for python",
        id='navbar_id',
        inverse = True,
    # fillable=False,
    # # *****************************************************************************************************
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
    # set up feed library so that it can change based on user inputs
    # for now there is a bool for 'teaching' where the table is filtered
    # It relies on the pandas df being loaded in the global and called 'feed_library_default'

    @reactive.Calc
    def user_selected_feed_library():
        if input.use_teaching_fd_library():
            teaching_feeds =  get_teaching_feeds()

            df_out = feed_library_default.query('Fd_Name.isin(@teaching_feeds)')
        else:
            df_out = feed_library_default
        return df_out

    @reactive.Calc
    def unique_fd_list():
        return get_unique_feed_list(user_selected_feed_library())
    
    @reactive.Calc
    def df_feed_library():
        return rename_df_cols_Fd_to_feed(user_selected_feed_library())

    

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
                df_feed_library()
                .query("`Feed Category` != 'Calf Liquid Feed'")
                .query("`Feed Name`" + ".str.contains('Calf', case=False, na=False) == False")
        ) 
        else:
            df_calf_filter = df_feed_library()

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
                            editable = True)
    
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
    user_kgs = reactive.Value(['kg_1'])
    
    #used for demo data
    feed_selected = reactive.Value(None)
    kg_selected = reactive.Value(0)

    @reactive.Calc
    def iterate_new_ingredient():
        current_iter =  str(len(user_feeds()) + 1)

        # copy, append and re-set items and percentages, to keep track of inputs
        xout = user_feeds().copy()
        xout.append('item_' + current_iter)
        user_feeds.set(xout)

        pout = user_kgs().copy()
        pout.append('kg_' + current_iter)
        user_kgs.set(pout)

        insert_new_ingredient(current_iter = current_iter, 
                              feed_choices = unique_fd_list(), 
                              # these reactive Values are normally blank except for when demo diet parses values:
                              feed_selected=feed_selected(), 
                              kg_selected=kg_selected()
                              )
        return current_iter
        
    # Generate a new item input whenever the "Add another item" button is clicked
    @reactive.Effect
    @reactive.event(input.add_button)
    def _():
        iterate_new_ingredient()



    @reactive.Effect
    @reactive.event(input.btn_reset_feeds)
    def _():
        # get number of UI elements
        current_iter =  len(user_feeds())+1
        
        # remove UI elements
        [remove_ingredient(i) for i in range(2,current_iter)]

        # reset reactive values to store user selections
        user_feeds.set(['item_1'])
        user_kgs.set(['kg_1'])

        # Update initial UI elements:
        ui.update_selectize(id = 'item_1', choices=unique_fd_list())
        ui.update_numeric(id = 'kg_1', value = 0)

        # add demo button back:
        if input.add_demo_diet() > 0:
            insert_demo_button()









        
  

    # set up UI with initial buttons
    @output
    @render.ui
    def item_input():
        # Generate initial item input
        itemInput = ui.div(
            {"id" : "userfeed_1" },
            ui.row(
                ui.column(4, ui.input_selectize( "item_1" ,
                                                 "Choose feeds to use in ration:",
                                                choices = unique_fd_list(), # leave blank until feed library is loaded
                                                multiple = False)),
                ui.column(2, ui.input_numeric('kg_1', 
                             label="Enter kg DM:", 
                             min=0, 
                             max=100, 
                             step = 0.2,
                             value=0)),
            )
        )
        return itemInput

    @reactive.Calc
    def get_diet_info():
    # Get items from input by name
    # returns a dataframe as a reactive
    # each 'feed' and 'kg' value is stored in these reactives (named 'item_1', etc) which means we can iterate through them and store their values in a list when we need them
        items = [getattr(input, x) for x in user_feeds()]
        kg = [getattr(input, x) for x in user_kgs()]
        
        # This is required to convert lists of reactive values to data frame.
        tmp_diet_info = pd.DataFrame({'Feedstuff' : [str(x()) for x in items], 
                             'kg_user' : [float(x()) for x in kg]})
        
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
    
    #########################################################
    # DMI intake numbers for Diet page
    #########################################################
    
    # Predict DMI for lactating cow
    @output
    @render.text
    @reactive.event(input.btn_calc_DMI)
    def predicted_DMI():
        
        if input.DMIn_eqn() == '8': 
            pred_DMI = nd.calculate_Dt_DMIn_Lact1(
                An_Parity_rl(), # adjusted from user input already
                input.Trg_MilkProd(), 
                input.An_BW(), 
                input.An_BCS(),
                input.An_LactDay(), 
                input.Trg_MilkFatp(), 
                input.Trg_MilkTPp(), 
                input.Trg_MilkLacp()
                )
            pred_DMI = str(round(pred_DMI, 2))+' kg'
        else:
            print("Only able to calculate intake for DMIn_eqn == 8")
            pred_DMI = 'NA - check DMIn_eqn'

        return pred_DMI

    @reactive.Calc
    def total_diet_intake():
        return get_diet_info().copy().sum(numeric_only=True)[0]

    @output
    @render.text
    def diet_total_intake():
        return total_diet_intake()
    
    @output
    @render.text
    def intake_difference():
        '''
        Calculate the difference in intake between target DMI and diet total kg DM for 'Diet' page
        '''
        return round((total_diet_intake()-input.DMI()),3)



      
    ########################
    # Add Demo diet
    ########################
    @reactive.Effect
    @reactive.event(input.add_demo_diet)
    def _():
        ui.update_selectize(id = 'item_1', choices = unique_fd_list(), selected = "Canola meal")
        ui.update_numeric(id = 'kg_1', value = 2.5)
        
        demo_feeds = ['Corn silage, typical', 'Triticale silage, mid-maturity', 'Corn grain HM, fine grind', 'Wheat straw','Urea', 'VitTM Premix, generic']
        demo_kgs = [7, 6.5, 7, 1.2, 0.3, 0.5]

        for feed, kg in  zip(demo_feeds, demo_kgs):
            # Can't pass arguments to event.Calc ? - using reactives
            feed_selected.set(feed) # type: ignore
            kg_selected.set(kg)
            iterate_new_ingredient()
        
        # reset to defaults
        feed_selected.set(None)
        kg_selected.set(0)

        # animal:
        # change page that is being viewed:
        # ui.update_navs("navbar_id", selected="Animal Inputs")
        # anim_list = ["An_Parity_rl", "Trg_MilkProd", "An_BW", "An_BCS", "An_LactDay", "Trg_MilkFatp", "Trg_MilkTPp", "Trg_MilkLacp", "DMI", "An_BW_mature", "Trg_FrmGain", "An_GestDay", "An_GestLength", "Trg_RsrvGain", "Fet_BWbrth", "An_AgeDay", "An_305RHA_MlkTP"]
        # anim_defaults = [2, 35, 700, 3, 150, 3.8, 3.10, 4.85, 24.5, 700, 0.19, 46, 280, 0, 44.1, 1620, 280]
        
        # for an_item, an_val in zip(anim_list, anim_defaults):
        #     ui.update_numeric(id = an_item, value = an_val)
       
        # remove button
        ui.remove_ui(selector="div:has(> #add_demo_diet)")

    #######################################################
    # Animal inputs
    #######################################################
    # this takes each individual input from UI and stores it in a dictionary that can be used by model.
    @reactive.Calc
    def An_AgeDay():
        # adjust inputs to match NASEM requirements
        return input.An_AgeMonth() * 30.3
    
    @reactive.Calc
    def An_Parity_rl():
        # convert to:  Value from 1-2 representing % of multiparous cows, 2 = 100% multiparous  
        return input.An_Parity_percent_first() / 100 + 1


    @reactive.Calc
    def animal_input_SHINY() -> dict:
        return {
                'An_Parity_rl': An_Parity_rl(),
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
                'An_AgeDay': An_AgeDay(), 
                'An_305RHA_MlkTP': input.An_305RHA_MlkTP(),
                'An_StatePhys': input.An_StatePhys(),
                'An_Breed': input.An_Breed()
                }

    @reactive.Calc
    def animal_input_RETURN() -> dict:
        return NASEM_out()['animal_input']
    
    @reactive.Calc
    def df_user_input_compare() -> pd.DataFrame:
        '''
        Compare user inputs from Shiny vs what gets returned by model.
        Especially important for tracing DMI changes.
        '''
        df_user_input_SHINY = pd.DataFrame(animal_input_SHINY().items(), columns=['Variable Name', 'Value_SHINY'])
        df_user_input_RETURN = pd.DataFrame(animal_input_RETURN().items(), columns=['Variable Name', 'Value_Model_Return'])

        df_user_input_compare  = df_user_input_SHINY.merge(
            df_user_input_RETURN, 
            on='Variable Name', 
            how='outer')
        return df_user_input_compare
    
    @output
    @render.table
    def animal_input_table_comparison():
        return df_user_input_compare()

    
    
    @reactive.Calc
    def equation_selection():
        return {'Use_DNDF_IV' : input.Use_DNDF_IV(), 'DMIn_eqn': input.DMIn_eqn()}
    
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

    # TODO: somehow update or modify NASEM_model to accept user-modified: datagrid_feed_lib()

    @reactive.Calc
    @reactive.event(input.btn_run_model)
    def NASEM_out():
        print("Executed NASEM_model()")
        # modify input.DMIn_eqn() to be 0 for model
        modified_equation_selection = equation_selection().copy()
        modified_equation_selection['DMIn_eqn'] = 0

        return nd.NASEM_model(get_diet_info(), animal_input_SHINY().copy(), modified_equation_selection, user_selected_feed_library(), nd.coeff_dict)
    
    #######################################################
    # Model Outputs
    #######################################################
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
        # return var_desc

    

    ##################################################################
    # Model evaluation
    ##################################################################
   
    @reactive.Calc
    def df_key_model_data_milk():
        # Variables to return:
        vars_return = ['Mlk_Prod_comp','milk_fat', 'milk_protein']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)

    @output
    @render.table
    def key_model_data_milk():
        return df_key_model_data_milk()
    

    
    @reactive.Calc
    def df_key_model_data_allowable_milk():
        # Variables to return:
        vars_return = ['Mlk_Prod_MPalow', 'Mlk_Prod_NEalow']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
    
    @output
    @render.table
    def key_model_data_allowable_milk():
        return df_key_model_data_allowable_milk()
    


    @reactive.Calc
    def df_key_model_data_ME():
        # Variables to return:
        vars_return = ['An_MEIn', 'Trg_MEuse', 'An_NE_In']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)

    @output
    @render.table
    def key_model_data_ME():
        return df_key_model_data_ME()
    

    @reactive.Calc
    def df_key_model_data_MP():
        # Variables to return:
        vars_return = ['An_MPIn', 'An_MPuse_kg_Trg']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)

    @output
    @render.table
    def key_model_data_MP():
        return df_key_model_data_MP()
    


    @reactive.Calc
    def df_key_model_data_DCAD():
        # Variables to return:
        vars_return = ['An_DCADmeq']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)

    @output
    @render.table
    def key_model_data_DCAD():
        return df_key_model_data_DCAD()
    


    @reactive.Calc
    def df_key_model_data_NEL():
        # Variables to return:
        vars_return = ['An_NE', 'An_NE_In']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)

    @output
    @render.table
    def key_model_data_NEL():
        return df_key_model_data_NEL()
        
    
    
    @reactive.Calc
    def df_key_model_data_energy_teaching():
        # Variables to return:
        vars_return = ['Trg_MEuse', 'An_MEmUse', 'An_MEgain', 'Gest_MEuse', 'Trg_Mlk_MEout', 'An_MEIn', 'Frm_NEgain', 'Rsrv_NEgain', 'GrUter_BWgain', 'An_MEIn', 'Mlk_Prod_NEalow', 'An_MEavail_Milk']
        # this reindexing will put them in the order of vars_return
        return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)

    @output
    @render.table
    def key_model_data_energy_teaching():
        return df_key_model_data_energy_teaching()



    
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
    

    
    @output
    @render.table
    def mineral_intakes():
        mineral_df = (
            NASEM_out()['mineral_intakes']
            .assign(
                Diet_percent = lambda df: df['Dt_micro'].fillna(df['Dt_macro']))
                .drop(columns=['Dt_macro', 'Dt_micro','Abs_mineralIn'])
                .reset_index(names='Mineral')
                .round(2)
                )
        return mineral_df
    

    ###################
    # Generate report
    @session.download(filename = lambda: f"NASEM_report-{date.today().isoformat()}.html")
    def btn_download_report():
        html_out = generate_report(
               df_milk = df_key_model_data_milk(),
               df_allowable_milk = df_key_model_data_allowable_milk(),
               df_ME = df_key_model_data_ME(),
               df_MP = df_key_model_data_MP(),
               df_diet_summary = display_diet_values(NASEM_out()["diet_info"]),
               df_DCAD = df_key_model_data_DCAD(),
               df_NEL = df_key_model_data_NEL(),
               df_ration_ingredients = get_diet_info(),
               df_energy_teaching = df_key_model_data_energy_teaching(),
               df_full_model = full_model_output(),
               df_animal_input_comparison = df_user_input_compare(), 
               dict_equation_selections = equation_selection()
                      )
    
        # Use io.BytesIO to yield the HTML content
        with io.StringIO() as buf:  # Use io.StringIO for string data
            buf.write(html_out)
            yield buf.getvalue()

        


app = App(app_ui, server,  debug=False)
