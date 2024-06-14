# pyright: reportArgumentType=false
# pyright: reportUnusedFunction=false
from shiny import App, reactive, render, ui, req
import shiny.experimental as x
# from shinywidgets import output_widget, render_widget, reactive_read
from datetime import date
import pandas as pd
from pathlib import Path
import shinyswatch
# import pdb #like browser()

from faicons import icon_svg

# Grid Table, has edits and row/column/cell selection - see: https://github.com/bloomberg/ipydatagrid/blob/main/examples/Selections.ipynb
# from ipydatagrid import DataGrid


# pip install git+https://github.com/CNM-University-of-Guelph/NASEM-Model-Python
import nasem_dairy as nd

from utils import (feed_library_default)


# modules
from module_feed_library import feed_library_ui, feed_library_server
from module_inputs import animal_inputs_ui, animal_inputs_server
from module_outputs import outputs_ui, outputs_server
from module_diet import diet_ui, diet_server


################################################################################
# Shiny App
################################################################################

app_ui = ui.page_navbar(

    ui.nav_panel(
        'Welcome',
        # shinyswatch.theme_picker_ui('cerulean'),
        ui.tags.script("""
        document.getElementById('logo').onclick = function() {
            Shiny.setInputValue('show_img_modal', Math.random());
        }
    """),
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
            
            ui.p(
                "The source code for the latest python implementation of the model can be viewed ", 
                ui.a('on GitHub',
                        href = 'https://github.com/CNM-University-of-Guelph/NASEM-Model-Python',
                        target = '_blank'
                    ),    
                icon_svg("github", margin_left='3px', height='1.2em'),
                ),

            ui.p(
                "The source code for this Shiny app (and instructions for running on local computer) can be viewed ", 
                ui.a('on GitHub',
                       href = 'https://github.com/CNM-University-of-Guelph/NASEM-shiny',
                       target = '_blank'),
                icon_svg("github", margin_left='3px', height='1.2em'),       
                ),
            ui.tags.img(src="absc_logo.png", style="height: 120px; width: auto;")
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
        diet_ui('nav_diet')
        ),
    ui.nav_panel(
            "Outputs", 
            outputs_ui('nav_outputs')
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
            open='closed',
            id = 'main_sidebar'
            ),

    # title= "NASEM for python",
    title = ui.span(
        ui.tags.img(src="logo2.webp", style="height: 40px; width: auto;"), 
        style = 'display: inline-flex;',
        id = 'logo'),
    # window_title= "NASEM dairy",
    id='navbar_id',
    inverse = False,
    fillable=False,

)


# ------------------------------------------------------------------------------
# Server

def server(input, output, session):
    @reactive.effect
    @reactive.event(input.show_img_modal)
    def show_img_modal():
        m = ui.modal(
            ui.tags.img(src="logo.webp", style="width: 100%;"),
            ui.em("Dave Innes, Braeden Fieguth and John Cant, University of Guelph."),
            easyClose=True,
            size='l'
        )
        ui.modal_show(m)
    # shinyswatch.theme_picker_server()

     #######################################################
    # Animal inputs
    #######################################################
    nav_diet_ns = session.ns('nav_diet')
    animal_input_dict, animal_input_reactives, equation_selection, usr_session_lib, session_upload_ModelOuput = animal_inputs_server(
        'nav_inputs', 
        input[nav_diet_ns("DMI")]
        )   
    
    
    #######################################################
    # Feed library
    #######################################################  
    user_selected_feed_library, user_selected_feeds = feed_library_server(
        "nav_feed_library", 
        feed_library_initial= feed_library_default, 
        user_selections_reset = input.reset_user_selected_feed_names,
        session_upload_library = usr_session_lib
        )
        

    #######################################################################
    # Model execution
    # Note: The order of operations matters here because the
    # 'Diet' tab takes NASEM_out as an input outside of reactive context.
    # i.e. NASEM_out reactive needs to be before Diet module in this file
    #######################################################################
    @reactive.Calc
    def NASEM_out():
        # Require that diet has > 0 kg before proceeding
        req( diet_total_intake() > 0)  
        
        # modify input.DMIn_eqn() to be 0 for model
        modified_equation_selection = equation_selection().copy()
        # force 'target' DMI when running model:
        modified_equation_selection['DMIn_eqn'] = 0

        # Force it to use predictions for mPrt_eqn - the target protein equations are not well tested 
        modified_equation_selection['mPrt_eqn'] = 1
        modified_equation_selection['mFat_eqn'] = 1
        # modified_equation_selection['mProd_eqn'] = 1 Defaults to 'component based'
    
        model_output = nd.execute_model(
            user_diet(), 
            animal_input_dict().copy(), 
            modified_equation_selection, 
            user_selected_feed_library(), 
            )
        
        return model_output
    

    #######################################################
    # Diet
    #######################################################
    # Diet Server
    user_diet, diet_total_intake, user_selected_DMI, df_model_snapshot = (
        diet_server(
            'nav_diet',                
            NASEM_out = NASEM_out, 
            animal_input_dict = animal_input_dict, 
            # equation_selection = equation_selection,
            animal_input_reactives = animal_input_reactives,
            user_selected_feed_library = user_selected_feed_library,
            user_selected_feeds = user_selected_feeds,
            session_upload_ModOut = session_upload_ModelOuput
        )
    ) 
    #######################################################
    # Outputs
    #######################################################
    outputs_server('nav_outputs', 
        NASEM_out, 
        user_selected_feed_library, 
        animal_input_dict,
        df_model_snapshot
        )


    #######################################################
    # Sidebar
    #######################################################
    @render.data_frame
    def user_selected_feed_names():
        ''' 
        Get user selected feeds from module and format to output in sidebar UI
        '''
        return pd.DataFrame(user_selected_feeds())
    
    
    # Open sidebar on first view of feed library page:
    feed_lib_tab_views = reactive.Value(0)

    @reactive.effect
    @reactive.event(input.navbar_id)
    def _():
        if input.navbar_id() == 'nav_feed_lib':
            feed_lib_tab_views.set(feed_lib_tab_views() + 1)

    @reactive.effect
    def _():
        if feed_lib_tab_views() == 1:
            ui.update_sidebar('main_sidebar', show=True)


app_dir = Path(__file__).parent
app = App(app_ui, server, static_assets=app_dir / "www", debug=False)