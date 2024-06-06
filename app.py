from shiny import App, reactive, render, ui, req
import shiny.experimental as x
from shinywidgets import output_widget, render_widget, reactive_read
from datetime import date
import pickle
import io
import pandas as pd
from pathlib import Path
import shinyswatch
# import pdb #like browser()

from faicons import icon_svg

# Grid Table, has edits and row/column/cell selection - see: https://github.com/bloomberg/ipydatagrid/blob/main/examples/Selections.ipynb
from ipydatagrid import DataGrid


# pip install git+https://github.com/CNM-University-of-Guelph/NASEM-Model-Python
import nasem_dairy as nd

from utils import display_diet_values, get_unique_feed_list, calculate_DMI_prediction, get_vars_as_df, validate_equation_selections
from generate_report import generate_report


# modules
from module_feed_library import feed_library_ui, feed_library_server
from module_inputs import animal_inputs_ui, animal_inputs_server

# Load global resources
feed_library_default = pd.read_csv('./NASEM_feed_library.csv').sort_values("Fd_Name")

var_desc = pd.read_csv("./variable_descriptions.csv").query("Description != 'Duplicate'")



# Function to add ui.div with new ingredient and percentage
def insert_new_ingredient(current_iter, feed_choices, feed_selected = None, kg_selected = 0):
    newItemDiv = ui.div(
            {"id" : "userfeed_" + current_iter}, # div ID
            ui.row(
                ui.column(6, ui.input_selectize("item_" + current_iter,
                                                #  "Choose feeds to use in ration:",
                                                label = "",
                                                choices = feed_choices,
                                                selected = feed_selected,
                                                multiple = False)),
                ui.column(3, ui.input_numeric('kg_' + current_iter, 
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
    


def insert_scenario_buttons():
    '''
    Used to add the scenario buttons (demo, assignment) back after inputs reset by user. 
    '''
    newItemDiv = ui.div(
            {"id" : "scenario_button_div"}, # div ID
            ui.row(
                ui.column(4, ui.input_action_button("add_demo_diet", "Add demo lactating diet", class_='btn-info')),
                # ui.column(4, ui.input_action_button("add_assignment_diet", 'Load assignment scenario', class_='btn-danger'))
            ),
            ui.br()
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

     

    ui.nav_panel(
        'Welcome',
        # shinyswatch.theme_picker_ui('cerulean'),
        ui.panel_title("Nutrient Requirements of Dairy Cattle - 8th Edition (NASEM 2021)"),
        # NOTE: using include_js() and include_css() fails to load both.
        ui.tags.link(href="custom.css", rel="stylesheet"),
        ui.tags.script(src="custom.js"),
            
        ui.br(),
        ui.p(
            "This app is a simplified version of the model described in the 8th Edition of the ", 
            ui.a('Nutrient Requirements of Dairy Cattle book.', 
                href = 'https://www.nationalacademies.org/our-work/nutrient-requirements-of-dairy-cattle-8th-edition',
                target = "_blank")
            ),
        ui.p("The current version of this app supports Lactating and Dry Cows and is being developed for teaching and research only. This software should not be used for on-farm or commercial decisions."),
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

    ui.nav_panel(
        "Inputs",
        animal_inputs_ui('nav_inputs')
        ),
    ui.nav_panel("Feed Library",
       feed_library_ui('nav_feed_library'),
       value = 'nav_feed_lib'
        ),

    ui.nav_panel("Diet",
                # ui.panel_title("Diet"),
                ui.card(
                    # ui.layout_sidebar(
                        
                        # ui.card(
                            ui.row( 
                                
                                ui.column(4, 
                                          ui.card(
                                          ui.p("Predicted Feed Intake:"),
                                          ui.output_text('predicted_DMI')
                                          )
                                          ),
                                
                                ui.column(3, ui.input_numeric("DMI", "Target dry matter intake (kg/d)", 26, min=0)),
                                ui.column(2, ui.p('Total diet intake (kg/d):'), ui.output_text('diet_total_intake')),
                                ui.column(2, ui.p('Difference (kg):'), ui.output_text("intake_difference")),
                            ),
                         #),
                       ui.card( 
                        ui.row(
                            ui.column(6, 
                                        
                                        ui.row(
                                            ui.column(6, ui.h2("Formulate ration:")),
                                            ui.column(6, ui.input_action_button("add_demo_diet", "Add demo lactating diet", class_='btn-info')),
                                            #  ui.column(6, ui.input_action_button("add_assignment_diet", 'Load assignment scenario', class_='btn-danger'))
                                            ),
                                            ui.br(),
                                            ui.output_ui("item_input"),
                                            ui.row(
                                                ui.column(4, ui.input_action_button("add_button", "Add another feed", class_='btn-success')),
                                                ui.column(4, ui.input_action_button('btn_load_user_selected_feeds', 'Populate with selected feeds')),
                                                ui.column(4, ui.input_action_button("btn_reset_feeds", "Reset ingredients list"))
                                                ),
                                                ),
                                ui.column(6, 
                                        ui.panel_well(
                                            ui.h2("Model Outputs - Snapshot"),
                                            ui.p(ui.em("The model is executed each time an ingredient selection or kg DM value changes. The following snapshot shows the calculated diet proportions of key components and some model outputs (different output is shown for dry cows):")),
                                            #   ui.row(
                                            #       ui.column(6, ui.output_table('snapshot_diet_data_model')),
                                            #       ui.column(6, ui.output_table('model_snapshot'))
                                            #       )
                                                
                                            ui.output_table('snapshot_diet_data_model'),

                                            # DEV
                                            # ui.panel_conditional(
                                            #     "animal_input_reactives()['An_StatePhys']() === 'Lactating Cow'",
                                            #     ui.output_table('model_snapshot')
                                            #     ),
                                            # ui.panel_conditional(
                                            #     "animal_input_reactives()['An_StatePhys']() !== 'Lactating Cow'",
                                            #     ui.output_table('model_snapshot_drycow')
                                            #     ),
                                            ui.output_ui('selected_snapshot')
                                                
                                                
                            ),)
                        )
                       ),                  
                       
                        ui.br(), ui.br(), ui.br(), ui.br(), 
                        # ui.br(),
                        # ui.output_table("user_selections")
                    # )
                ),
            ),
        ui.nav_panel("Outputs",
                ui.panel_title("NASEM Model Outputs"),
                ui.row(
                    ui.column(3, ui.p(ui.em("The model is executed each time an ingredient selection or kg DM value changes."))),
                    ui.column(2, ui.download_button("btn_download_report", "Download Report", class_='btn-warning'), offset = 1),
                    ui.column(3, ui.download_button("btn_pkl_download", "Download .NDsession file", class_='btn-warning'))
                ),
               
                ui.navset_card_tab(
                    ui.nav_panel(
                        'Model Evaluation',
                        ui.h5('Milk production estimates:'),
                        # ui.output_table('key_model_data_milk'),
                        ui.output_data_frame('key_model_data_milk'),
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

                    ui.nav_panel(
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
                    ui.nav_panel(
                        'Vitamins and Minerals',
                        ui.output_data_frame('macro_minerals'),
                        ui.br(),
                        ui.output_data_frame('micro_minerals')

                        ),
                    ui.nav_panel(
                        "Energy - teaching",
                        ui.output_table('key_model_data_energy_teaching')
                        ),

                    ui.nav_panel(
                        'Advanced',
                        # ui.h5('All model predictions'),
                        # ui.output_table('model_data'),
                        ui.br(),
                        ui.h4('extended output'),
                        ui.output_table('diet_info'),
                        ui.h4("Confirm Model inputs:"),
                        ui.output_table('animal_input_table_comparison'),
                        ui.output_table('equation_selection_table'),
                        # ui.output_text_verbatim('testing')
                    )
                ),
                ), 
    ui.nav_spacer(), 
    ui.nav_control(ui.input_dark_mode()), 
    sidebar=
        ui.sidebar(
            ui.tooltip(
                icon_svg("circle-info", margin_left='5px', height='1.2em'), 
                ui.p("This sidebar can be viewed from all tabs. Use the arrow to open and close as required.")
            ),
                    ui.p("Feeds selected by user from Feed Library. The Diet can be populated from this list."),
                    ui.output_data_frame('user_selected_feed_names'),
                    ui.br(),
                    ui.input_action_button('reset_user_selected_feed_names', "Clear list"),
                    # ui.output_data_frame('user_selected_feed_names'),
                    # ui.br(),
                    # ui.input_action_button('reset_user_selected_feed_names', "Clear list")
                open='closed',
                id = 'main_sidebar'
                ),

    title= "NASEM for python",
    # window_title= "NASEM dairy",
    id='navbar_id',
    inverse = False,
    fillable=False
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
    # shinyswatch.theme_picker_server()
    # Output text for printing during dev
    # @output
    # @render.text
    # def testing():
    #     # return(animal_input_reactives()['An_StatePhys']())
    #     return(animal_input_dict())

    @render.ui
    def selected_snapshot():
        if animal_input_reactives()['An_StatePhys']() == 'Lactating Cow':
            
            return  ui.output_table('model_snapshot')
        elif animal_input_reactives()['An_StatePhys']() == 'Dry Cow':
            return ui.output_table('model_snapshot_drycow')
        else:
            return ui.TagList()

    # Feed library
    user_selected_feed_library, user_selected_feeds = feed_library_server("nav_feed_library", feed_library_default = feed_library_default, user_selections_reset = input.reset_user_selected_feed_names)

    @reactive.Calc
    def unique_fd_list():
        return get_unique_feed_list(user_selected_feed_library())
    
    @output
    @render.data_frame
    def user_selected_feed_names():
        ''' 
        Get user selected feeds from module and format to output in sidebar UI
        '''
        return pd.DataFrame(user_selected_feeds())


    #######################################################
    # Open sidebar on first view of feed library page
    #######################################################
    feed_lib_tab_views = reactive.Value(0)

    @reactive.effect
    @reactive.event(input.navbar_id)
    def _():
        if input.navbar_id() == 'nav_feed_lib':
            feed_lib_tab_views.set(feed_lib_tab_views() + 1)
            print(feed_lib_tab_views())
        
        if feed_lib_tab_views() == 1:
            ui.update_sidebar('main_sidebar', show=True)



    #######################################################
    # Feed Inputs
    #######################################################

    # Initialize reactive values to store user selections
    user_feeds = reactive.Value(['item_1'])
    user_kgs = reactive.Value(['kg_1'])
    
    #used for 'iterate new ingredient' because variables can't be parsed into these functions
    # so, the values are assigned to these 2 reactives which are then used by the iterate_new_ingredient function to set up a new feed
    # originally used by demo diets
    feed_selected = reactive.Value(None)
    kg_selected = reactive.Value(0)

    # set up UI with initial buttons
    @output
    @render.ui
    def item_input():
        # Generate initial item input
        itemInput = ui.div(
            {"id" : "userfeed_1" },
            ui.row(
                ui.column(6, ui.input_selectize("item_1" ,
                                                 "Choose feeds to use in ration:",
                                                choices = unique_fd_list(), # leave blank until feed library is loaded
                                                multiple = False)),
                ui.column(3, ui.input_numeric('kg_1', 
                             label="Enter kg DM:", 
                             min=0, 
                             max=100, 
                             step = 0.2,
                             value=0)),
            )
        )
        return itemInput
    
    @reactive.Calc
    def iterate_new_ingredient():
        '''
        This is executed by the reactive event below, and keeps track of new UI created so that the feed name and kg can be used meaningfully in app.
        '''
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
    @reactive.event(input.btn_load_user_selected_feeds)
    def _():
        '''used to update feeds based on user selections'''
        # NOTE: this can be used for user session file
        feed_list = user_selected_feeds().to_list()

        for i, feed in enumerate(feed_list):
            if i == 0:
                ui.update_selectize(id = 'item_1', choices = unique_fd_list(), selected = feed)
                ui.update_numeric(id = 'kg_1', value = 0)
            else:
                feed_selected.set(feed) # type: ignore
                kg_selected.set(0)
                iterate_new_ingredient()
        
        # reset to defaults
        feed_selected.set(None)
        kg_selected.set(0)


    @reactive.Effect
    @reactive.event(input.btn_reset_feeds)
    def _():
        '''
        Used to reset feeds back to normal by removing an UI created and resetting reactive variables that store state.
        '''
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
        if input.add_demo_diet() > 0 or input.add_assignment_diet() > 0:
            insert_scenario_buttons()



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
    def get_diet_total():
        return get_diet_info()['kg_user'].sum(numeric_only=True)


    # # render table by calling the calc function for it's output       
    # @output
    # @render.table
    # def user_selections():
    #     return format_diet_info()

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
    def predicted_DMI():
        # Dt_NDF = NASEM_out()["diet_info"].loc['Diet','Fd_NDF'].copy()

        # IF model has been executed, then use the user-input selection
        if get_diet_total() > 0:
            req(NASEM_out())
            Dt_NDF = NASEM_out().get_value("Dt_NDF")

            eqn_selection = validate_equation_selections(equation_selection())

            # This doesn't have a button to execute - changes each time the animal inputs change
            pred_DMI = calculate_DMI_prediction(
                animal_input=animal_input_dict().copy(),
                DMIn_eqn= eqn_selection['DMIn_eqn'],
                diet_NDF = Dt_NDF,
                coeff_dict= nd.coeff_dict
            )
            return str(f"{pred_DMI} kg DM/d")
        else:
            # use equation that does not use diet:
            pred_DMI = calculate_DMI_prediction(
                animal_input=animal_input_dict().copy(),
                DMIn_eqn= 8,
                diet_NDF = 0,
                coeff_dict= nd.coeff_dict
            )
            return str(f"{pred_DMI} kg DM/d (using 'cow factors only' until diet is entered)")


    @reactive.Calc
    def total_diet_intake():
        return get_diet_info().copy()['kg_user'].sum()

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

        demo_dict = {
            'Corn silage, typical': 7,
            'Triticale silage, mid-maturity': 6.5,
            'Corn grain HM, fine grind': 7,
            'Wheat straw': 1.2,
            'Urea': 0.3,
            'VitTM Premix, generic': 0.5,
        }

        for feed, kg in demo_dict.items():
            feed_selected.set(feed) # type:ignore
            kg_selected.set(kg)
            iterate_new_ingredient()    

       
        # reset to defaults
        feed_selected.set(None)
        kg_selected.set(0)

      
        # remove button
        ui.remove_ui(selector="div:has(> #add_demo_diet)")


    #######################################################
    # Animal inputs
    #######################################################
    animal_input_dict, animal_input_reactives, equation_selection = animal_inputs_server('nav_inputs', input.DMI)

    
    #######################################################
    # Run Model
    #######################################################
    # each of the inputs has been formatted from UI inputs to the required type needed by teh model.
    # e.g. currently diet_info is a df whereas animal_input is a dict.
    # Might make sense to use all dicts???


    @reactive.Calc
    # @reactive.event(input.btn_run_model)
    def NASEM_out():
        # Check diet has > 0 kg
        req( get_diet_total() > 0)
            
        
        # modify input.DMIn_eqn() to be 0 for model
        modified_equation_selection = equation_selection().copy()
        # force 'targets' when running model:
        modified_equation_selection['DMIn_eqn'] = 0
        modified_equation_selection['mProd_eqn'] = 0 # Force it to use target (user input) MY for energy and protein requirements, etc

        modified_equation_selection['mPrt_eqn'] = 0
        modified_equation_selection['mFat_eqn'] = 0
        modified_equation_selection['MiN_eqn'] = 1
        modified_equation_selection['NonMilkCP_ClfLiq']  = 0
        modified_equation_selection['RumDevDisc_Clf'] = 0

        # {'Use_DNDF_IV': 0.0,


        # 'NonMilkCP_ClfLiq': 0.0,
        # 'MiN_eqn': 1.0,

        # 'mPrt_eqn': 0.0,
        # 'mFat_eqn': 1.0,
        # 'RumDevDisc_Clf': 0.0}
        #DMIn_eqn equation forced to 0 for shiny app

    
        model_output = nd.execute_model(get_diet_info(), animal_input_dict().copy(), modified_equation_selection, user_selected_feed_library(), nd.coeff_dict)
        return model_output
    
    
    @output
    @render.table
    # @reactive.event(NASEM_out, ignore_init=True)
    def animal_input_table_comparison():
        return df_user_input_compare()
    
    @reactive.Calc
    # @reactive.event(NASEM_out, ignore_init=True)
    def animal_input_RETURN() -> dict:
        return NASEM_out().get_value('animal_input')
    

    
    @reactive.Calc
    # @reactive.event(NASEM_out, ignore_init=True)
    def df_user_input_compare() -> pd.DataFrame:
        '''
        Compare user inputs from Shiny vs what gets returned by model.
        Especially important for tracing DMI changes.
        '''
        df_user_input_SHINY = pd.DataFrame(animal_input_dict().items(), columns=['Variable Name', 'Value_SHINY'])
        df_user_input_RETURN = pd.DataFrame(animal_input_RETURN().items(), columns=['Variable Name', 'Value_Model_Return'])

        df_user_input_compare  = df_user_input_SHINY.merge(
            df_user_input_RETURN, 
            on='Variable Name', 
            how='outer')
        
        return df_user_input_compare
        
   
    
    @output
    @render.table
    def equation_selection_table():
        return pd.DataFrame(equation_selection().items(), columns=['Variable Name', 'Value'])
    
    #######################################################
    # Model Outputs
    #######################################################
    # @reactive.Calc
    # @reactive.event(NASEM_out, ignore_init=True)
    # def full_model_output():
    #     '''
    #     Prepare model output data to be rendered or filtered further
    #     '''
    #     model_df = (pd.DataFrame
    #         .from_dict(
    #             NASEM_out()['model_results_full'], orient='index', columns=['Value']
    #             )
    #         .reset_index(
    #             names="Model Variable"
    #             )
    #         .assign(
    #             Value = lambda df: df['Value'].round(3)
    #             )
    #         .merge(var_desc, how = 'left')
    #         )
    #     return model_df
            

    ##################################################################
    # Model evaluation
    ##################################################################

    ###############################
    # Snapshot on Diet page
    @reactive.Calc
    def df_model_snapshot():
        # Variables to return:
        vars_return = ['Mlk_Prod_comp','MlkFat_Milk_p', 'MlkNP_Milk_p', 'Mlk_Prod_MPalow', 'Mlk_Prod_NEalow', 'An_RDPbal_g', 'Du_MiCP_g']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return).filter(items = ["Description", "Value"])
        new_var_names = {
            'Mlk_Prod_comp': 'Milk Production (kg/d)',
            'MlkFat_Milk_p': 'Milk Fat %',
            'MlkNP_Milk_p': 'Milk Protein %',
            'Mlk_Prod_MPalow': 'MP Allowable Milk Production (kg/d)',
            'Mlk_Prod_NEalow': 'NE Allowable Milk Production (kg/d)',
            'An_RDPbal_g': 'Animal RDP Balance (g)',
            'Du_MiCP_g': 'Duodenal Microbial CP (g) '
        }
        df_out = get_vars_as_df(vars_return, NASEM_out()).assign(
            Variable = lambda df: df['Variable'].map(new_var_names)
        )
        return df_out
    
    @output
    @render.table()
    def model_snapshot():
        return df_model_snapshot()
    
    @reactive.Calc
    def df_model_snapshot_drycow():
        # Variables to return:
        vars_return = ['An_MEIn', 'Trg_MEuse', 'An_MEbal', 'An_MPIn_g', 'An_MPuse_g_Trg', 'An_MPBal_g_Trg','An_RDPIn_g', 'Du_MiCP_g','An_RDPbal_g', 'An_DCADmeq']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return).filter(items = ["Description", "Value"])
        return get_vars_as_df(vars_return, NASEM_out())
    
    @output
    @render.table()
    def model_snapshot_drycow():
        return df_model_snapshot_drycow() 
    

    @output
    @render.table
    @reactive.event(NASEM_out)
    def snapshot_diet_data_model():
        return display_diet_values(NASEM_out().get_value("diet_data"), is_snapshot=True)
    ###############################

    @reactive.Calc
    def df_key_model_data_milk():
        # Variables to return:
        vars_return = ['Mlk_Prod_comp', 'MlkFat_Milk_p', 'MlkNP_Milk_p']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    
    # @output
    # @render.table
    # def key_model_data_milk():
    #     return df_key_model_data_milk()
    
    # @output
    @render.data_frame
    def key_model_data_milk():
        return render.DataTable(df_key_model_data_milk(), height='auto')

    
    @reactive.Calc
    def df_key_model_data_allowable_milk():
        # Variables to return:
        vars_return = ['Mlk_Prod_MPalow', 'Mlk_Prod_NEalow']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    
    @output
    @render.table
    def key_model_data_allowable_milk():
        return df_key_model_data_allowable_milk()
    


    @reactive.Calc
    def df_key_model_data_ME():
        # Variables to return:
        vars_return = ['An_MEIn', 'Trg_MEuse', 'An_NEIn']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    
    @output
    @render.table
    def key_model_data_ME():
        return df_key_model_data_ME()
    

    @reactive.Calc
    def df_key_model_data_MP():
        # Variables to return:
        vars_return = ['An_MPIn', 'An_MPuse_kg_Trg']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    
    @output
    @render.table
    def key_model_data_MP():
        return df_key_model_data_MP()
    


    @reactive.Calc
    def df_key_model_data_DCAD():
        # Variables to return:
        vars_return = ['An_DCADmeq']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    
    @output
    @render.table
    def key_model_data_DCAD():
        return df_key_model_data_DCAD()
    


    @reactive.Calc
    def df_key_model_data_NEL():
        # Variables to return:
        vars_return = ['An_NE', 'An_NE_In']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    @output
    @render.table
    def key_model_data_NEL():
        return df_key_model_data_NEL()
        
    
    
    @reactive.Calc 
    def df_key_model_data_energy_teaching():
        # Variables to return:
        vars_return = ['Trg_MEuse', 'An_MEmUse', 'An_MEgain', 'Gest_MEuse', 'Trg_Mlk_MEout', 'An_MEIn', 'Frm_NEgain', 'Rsrv_NEgain', 'GrUter_BWgain', 'An_MEIn', 'Mlk_Prod_NEalow', 'An_MEavail_Milk']
        # this reindexing will put them in the order of vars_return
        # return full_model_output().query('`Model Variable`.isin(@vars_return)').set_index('Model Variable').reindex(vars_return)
        return get_vars_as_df(vars_return, NASEM_out())
    
    @output
    @render.table
    def key_model_data_energy_teaching():
        return df_key_model_data_energy_teaching()



    
    # @output
    # @render.table
    # def model_data():
    #     return full_model_output()

    @output
    @render.table
    def diet_data_model():
        return display_diet_values(NASEM_out().get_value("diet_data"))
    
    @output
    @render.table
    def diet_info():
        return NASEM_out().get_value("diet_info")
    
    @output
    @render.table
    def feed_data():
        return NASEM_out().get_value('feed_data')
    

    
    @output
    @render.data_frame
    def macro_minerals():    
        return render.DataTable(NASEM_out().report_minerals()['macro_minerals'].round(3),height='auto')
    
    @output
    @render.data_frame
    def micro_minerals():    
        return render.DataTable(NASEM_out().report_minerals()['micro_minerals'].round(3), height='auto')
    
    

    ###################
    # Generate report
    @render.download(filename = lambda: f"NASEM_report-{date.today().isoformat()}.html")
    def btn_download_report():
        html_out = generate_report(
               df_milk = df_key_model_data_milk(),
               df_allowable_milk = df_key_model_data_allowable_milk(),
               df_ME = df_key_model_data_ME(),
               df_MP = df_key_model_data_MP(),
               df_diet_summary = display_diet_values(NASEM_out().get_value("diet_data")),
               df_DCAD = df_key_model_data_DCAD(),
               df_NEL = df_key_model_data_NEL(),
               df_ration_ingredients = get_diet_info(),
               df_energy_teaching = df_key_model_data_energy_teaching(),
               df_full_model=pd.DataFrame(),
            #    df_full_model = full_model_output(),
            #    df_animal_input_comparison = df_user_input_compare(), 
               dict_equation_selections = equation_selection(),
               df_snapshot= df_model_snapshot() if input.An_StatePhys() == 'Lactating Cow' else df_model_snapshot_drycow()
                      )
    
        # Use io.BytesIO to yield the HTML content 
        with io.StringIO() as buf:  # Use io.StringIO for string data
            buf.write(html_out)
            yield buf.getvalue()

        
    #######################
    # Save Session file 
    # a pickle file using the .NDsession extension

    # Download handler
    @render.download(filename = lambda: f"NASEM_simulation-{date.today().isoformat()}.NDsession")
    def btn_pkl_download():
        req(NASEM_out())
        output_dict = {
            'ModelOutput' : NASEM_out(),
            'FeedLibrary' : user_selected_feed_library()
        }
        with io.BytesIO() as buf:
            pickle.dump(output_dict, buf)
            yield buf.getvalue()

   


app_dir = Path(__file__).parent
app = App(app_ui, server, static_assets=app_dir / "www", debug=False)