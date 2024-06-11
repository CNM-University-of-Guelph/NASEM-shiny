import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui, module, reactive, req
# from shinywidgets import output_widget, render_widget, reactive_read
# from ipydatagrid import DataGrid
import pickle
import nasem_dairy as nd

from utils import DM_intake_equation_strings

@module.ui
def animal_inputs_ui():
    return ([
        ui.navset_card_tab( 
            ui.nav_panel(
                'Info',
                ui.p("Info text"),
                ui.br(),
                ui.input_file('pkl_upload', 
                              "Upload .NDsession file from a previous session.", 
                              accept='.NDsession', width='500px'),
                ui.br()
            ),
            ui.nav_panel(
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
                    choices = {'Lactating Cow': 'Lactating Cow', 'Dry Cow': 'Dry Cow'}, # 'Heifer': 'Heifer', 'Calf': 'Calf'
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
            ui.nav_panel(
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

            ui.nav_panel(
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


            ui.nav_panel(
                'Advanced',
                
               # ui.panel_title("Equation selections"),
                
               
                
                ui.input_numeric("An_GestLength", "Gestation length (d)", 280, min=0),
                ui.input_numeric("Fet_BWbrth", "Calf birth weight (kg)", 44.1, min=0),

                ui.input_numeric("An_305RHA_MlkTP", "Milk True Protein rolling heard average (kg/305 d)", 396, min = 0),

                ui.input_numeric("An_AgeDryFdStart", "Day starter feed is first offered to calves", 14, min=0),
                ui.input_numeric("Env_TempCurr", "Current mean daily temperature (°C)", 22, min=-50, max=50),
                ui.input_numeric("Env_DistParlor", "Distance from the barn or paddock to the parlor (meters)", 0, min=0),
                ui.input_numeric("Env_TripsParlor", "Number of daily trips to and from the parlor", 0, min=0),
                ui.input_numeric("Env_Topo", "Positive elevation change per day (meters)", 0, min=0),

                ui.accordion(
                    ui.accordion_panel(
                        'Equation selections',
                        ui.input_selectize(
                            "DMIn_eqn",
                            label = "Select DM Intake equation to use for predicting intake on Diet page (default is 'lactating, cow factors only'). Does not change model, user input DMI is always used in this app.",
                            choices = DM_intake_equation_strings(),
                            selected = 8, # type: ignore
                            multiple = False,
                            width='500px'
                            ),                        
                        ui.input_radio_buttons(
                            "mProd_eqn", 
                            "Milk production equation to use for calcs (currently hard-coded to use Trg_MilkProd):",
                            choices = {0: 'Trg_MilkProd', 1: 'component based predicted', 
                                       2: 'NE Allowable', 3: 'MP Allowable', 4: 'min(NE,MPAllow)'},  # type: ignore
                            selected = 1 # type: ignore
                            ), 

                        ui.input_radio_buttons(
                            "mPrt_eqn", 
                            ("Milk Protein equations and coefficients to use."
                             "NRC is NRC2021", 
                             "VT1 coefficients from Dec. 20, 2020 - Virginia Tech (no Phe, Thr, Trp, or Val)",
                             "VT2 coefficients from April, 2022 solutions after further data cleaning - Virginia Tech (no Arg, Phe, Trp, or Val)"
                             ), 
                            choices = {0: "NRC", 1: "VT1", 2: "VT2"},
                            selected = 0),

                        ui.input_radio_buttons("mFat_eqn", "Milk Fat prediction equation", 
                                               choices = {0: "Trg_MilkFatp", 1: "Predicted milk fat production"}, 
                                               selected = 1),

                        ui.input_radio_buttons("MiN_eqn", "MiN equation", 
                                               choices={1: "NRC (2021)", 2: "Hanigan (2021)", 3: "White (2017)"}, selected=1),
                     
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
                      
                        ui.input_radio_buttons("NonMilkCP_ClfLiq", "Non milk protein source?", choices={0: "No", 1: "Yes"}),
            
                        ui.input_radio_buttons("RumDevDisc_Clf", "Rumen development discount", choices={0: "No", 1: "Yes"})
                    ) 
                )
                
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
                # 'DMI' : 10,
                'An_BW_mature': input.An_BW_mature(),
                'Trg_FrmGain': input.Trg_FrmGain(),
                'An_GestDay': input.An_GestDay(),
                'An_GestLength': input.An_GestLength(),
                'Trg_RsrvGain': input.Trg_RsrvGain(),
                'Fet_BWbrth': input.Fet_BWbrth(),
                'An_AgeDay': An_AgeDay(), 
                'An_305RHA_MlkTP': input.An_305RHA_MlkTP(),
                'An_StatePhys': input.An_StatePhys(),
                'An_Breed': input.An_Breed(),
                'An_AgeDryFdStart' : input.An_AgeDryFdStart(),
                'Env_TempCurr' : input.Env_TempCurr(),
                'Env_DistParlor' : input.Env_DistParlor(),
                'Env_TripsParlor' : input.Env_TripsParlor(),
                'Env_Topo' : input.Env_Topo(),

                # 'An_AgeDryFdStart': 14, #Day starter feed is first offered
                # 'Env_TempCurr': 22, #,current mean daily temperature in degrees C
                # 'Env_DistParlor': 0,#distance from the barn or paddock to the parlor in meters
                # 'Env_TripsParlor': 0,#, number of daily trips to and from the parlor; generally 2 trips per milking times number of milkings
                # 'Env_Topo': 0 #,the positive elevation change per day in meters
                
                }
    
    @reactive.Calc
    def animal_input_reactives() -> dict:
        return {
            'An_StatePhys': input.An_StatePhys
        }
    

    @reactive.Calc
    def equation_selection() -> dict:
        return {
            'Use_DNDF_IV' : input.Use_DNDF_IV(), 
            'DMIn_eqn': input.DMIn_eqn(), 
            'mProd_eqn': input.mProd_eqn(), 
            'mPrt_eqn': input.mPrt_eqn(),
            'mFat_eqn': input.mFat_eqn(),
            'Monensin_eqn': input.Monensin_eqn(),
            'NonMilkCP_ClfLiq': input.NonMilkCP_ClfLiq(),
            'RumDevDisc_Clf': input.RumDevDisc_Clf(),
            'MiN_eqn': input.MiN_eqn()
            }
    
    ########################
    # Dry Cow UI setup
    ########################

    @reactive.Effect
    def _():
        if animal_input_reactives()['An_StatePhys']() == 'Dry Cow':
            ui.update_selectize('DMIn_eqn', selected='10')

            ui.insert_ui(ui.div(
                {'id' : 'drycow_input_warning'},
                ui.em('Dry cow is selected so no milk production data can be entered.')), 
                 selector = "#milk_production_conditional_panel", # place the new UI's below the initial item input
                 where = "afterEnd")
            
            ui.update_numeric('An_GestDay', value = 220)
            ui.update_numeric('Trg_FrmGain', value = 0.1)
            ui.update_numeric('Trg_RsrvGain', value = 0)
            ui.update_numeric('Trg_MilkProd', value = 0)
        
        elif animal_input_reactives()['An_StatePhys']() == 'Lactating Cow':
            ui.update_selectize('DMIn_eqn', selected='8')

            ui.remove_ui(selector="div#drycow_input_warning")
            
            ui.update_numeric('An_GestDay', value = 46)
            ui.update_numeric('Trg_FrmGain', value = 0.6)
            ui.update_numeric('Trg_RsrvGain', value = 0.1)
            ui.update_numeric('Trg_MilkProd', value = 35)
    
    ########################
    # Load session file
    @reactive.Calc
    def pkl_session_upload():
        pkl_input = req(input.pkl_upload())
        
        print(pkl_input[0])
        file_path = pkl_input[0]["datapath"]
        with open(file_path, 'rb') as f:
            pkl_dict = pickle.load(f)

        # Check pickle file
        if not isinstance(pkl_dict, dict) or 'ModelOutput' not in pkl_dict or not isinstance(pkl_dict['ModelOutput'], nd.ModelOutput):
            m = ui.modal(
                ui.p('The uploaded file does not contain a valid ModelOutput entry. Please try again.'),
                title='Upload failed',
                easy_close=True,
            )
            ui.modal_show(m)
            return {}

        if 'FeedLibrary' not in pkl_dict or not isinstance(pkl_dict['FeedLibrary'], pd.DataFrame):
            m = ui.modal(
                ui.p('The uploaded file does not contain a valid Feed Library entry. Please try again.'),
                title='Upload failed',
                easy_close=True,
            )
            ui.modal_show(m)
            return {}
        
        ui.notification_show('.NDsession upload successful', type='message')
        return pkl_dict
    
    @reactive.effect
    def _():
        ''' This has the added function of instant dependency on pkl upload, leading to immediate modal warnings if something wrong.'''
        print(pkl_session_upload())
    

    # Unpack session dictionary
    def session_upload_library():
        return pkl_session_upload()['FeedLibrary']

    def session_upload_ModelOuput():
        return pkl_session_upload()['ModelOutput']


    return(animal_input_dict, animal_input_reactives, equation_selection, session_upload_library)
