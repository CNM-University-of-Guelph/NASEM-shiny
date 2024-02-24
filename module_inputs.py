import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui, module, reactive, req
from shinywidgets import output_widget, render_widget, reactive_read
from ipydatagrid import DataGrid

from utils import DM_intake_equation_strings

@module.ui
def animal_inputs_ui():
    return ([
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
                    choices = {'Lactating Cow': 'Lactating Cow', 'Dry Cow': 'Dry Cow'}, #'Calf':'Calf'
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
                ui.panel_conditional(
                    "input.An_StatePhys === 'Lactating Cow'",
                    ui.input_numeric("An_LactDay", "Average days in milk:", 100, min=0)
                ),
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
                ui.panel_conditional("input.An_StatePhys === 'Lactating Cow'",
                    {"id" : "milk_production_conditional_panel" },
                    ui.h3("Milk Yield"),
                    ui.input_numeric("Trg_MilkProd", "Target milk production (kg/d)", 35, min=0),
                    
                    ui.br(),
                    
                    ui.h3("Milk Components"),
                    ui.input_numeric("Trg_MilkFatp", "Target milk fat %", 3.8, min=0, ),
                    ui.input_numeric("Trg_MilkTPp", "Target milk true protein %", 3.1, min=0, ),
                    ui.input_numeric("Trg_MilkLacp", "Target milk lactose %", 4.85, min=0, )
                    ),
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

                ui.input_radio_buttons(
                    "Monensin_eqn", 
                    "Use Monensin equations?",
                    choices = {0:"No", 1:"Yes"}, # type: ignore
                    ),     

                ui.input_radio_buttons(
                    "mProd_eqn", 
                    "Milk production equation to use for calcs (currently hard-coded to use Trg_MilkProd):",
                    choices = {0: 'Trg_MilkProd', 1: 'component based predicted', 2: 'NE Allowable', 3: 'MP Allowable', 4: 'min(NE,MPAllow)'},  # type: ignore
                    selected=1 # type: ignore
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
    ])




@module.server
def animal_inputs_server(input: Inputs, output: Outputs, session: Session, user_selected_DMI):

     # this takes each individual input from UI and stores it in a dictionary that can be used by model.
    @reactive.Calc
    def An_AgeDay():
        # adjust inputs to match NASEM requirements
        return input.An_AgeMonth() * 30.3
    
    @reactive.Calc
    def An_Parity_rl():
        # convert to:  Value from 1-2 representing % of multiparous cows, 1 = 100% primi;  2 = 100% multiparous  
        return 2 - ( input.An_Parity_percent_first() / 100 )


    @reactive.Calc
    def animal_input_dict() -> dict:
        return {
                'An_Parity_rl': An_Parity_rl(),
                'Trg_MilkProd': input.Trg_MilkProd(),
                'An_BW': input.An_BW(),
                'An_BCS': input.An_BCS(),
                'An_LactDay': input.An_LactDay(),
                'Trg_MilkFatp': input.Trg_MilkFatp(),
                'Trg_MilkTPp': input.Trg_MilkTPp(),
                'Trg_MilkLacp': input.Trg_MilkLacp(),
                'DMI' : user_selected_DMI(), # This input is passed in from main app.py 
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
    def animal_input_reactives() -> dict:
        return {
            'An_StatePhys': input.An_StatePhys
        }
    

    @reactive.Calc
    def equation_selection() -> dict:
        return {'Use_DNDF_IV' : input.Use_DNDF_IV(), 'DMIn_eqn': input.DMIn_eqn(), 'mProd_eqn': input.mProd_eqn(), 'Monensin_eqn': input.Monensin_eqn()}
    

    return(animal_input_dict, animal_input_reactives, equation_selection)
