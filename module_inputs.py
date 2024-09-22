import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui, module, reactive, req
# from shinywidgets import output_widget, render_widget, reactive_read
# from ipydatagrid import DataGrid
import pickle
import nasem_dairy as nd
import htmltools

@module.ui
def animal_inputs_ui():
    return ([
        ui.navset_card_tab( 
            ui.nav_panel(
                'Information',
                ui.card(
                    ui.card_header("Get started", class_= 'bg-success'),
                    ui.tags.li("Select each tab to enter inputs for the model"),
                    ui.tags.li("These values represent the animal and the target milk production"),
                    ui.tags.li("These initial values help the model calculate 'requirements' for nutrients"),
                    ui.tags.li("The model will also predict milk production (kg/d), milk fat (%) and milk protein (%) based on other factors (including the diet)"),
                    # ui.tags.li("Normally these numbers would represent the average value for a group of animals."),
                    
                    style = htmltools.css(max_width='750px', margin='1rem auto')
                ),
                # ui.br(),
                ui.card(
                    ui.card_header('Load previous session', class_= 'bg-info'), 
                    ui.tags.li("A .NDsession file can be uploaded here to re-populate all inputs to match a previous simulation."),
                    ui.tags.li("See the Outputs tab to download a .NDsession file after running the model."),
                    ui.br(),
                    ui.input_file('pkl_upload', 
                                "Upload .NDsession file from a previous session.", 
                                accept='.NDsession', width='500px'),
                    ui.br(),
                    ui.output_ui('display_usr_session_modified_time'),
                    style = htmltools.css(max_width='750px', margin='1rem auto')
                ),
               
            ),
            ui.nav_panel(
                'Animal Description',
                ui.layout_column_wrap(
                    ui.card(
                        ui.input_selectize(
                            'An_StatePhys', 
                            label = ui.span('Select physiological state:', style='font-weight:bold'), 
                            choices = {'Lactating Cow': 'Lactating Cow', 'Dry Cow': 'Dry Cow'}, # 'Heifer': 'Heifer', 'Calf': 'Calf'
                            selected = 'Lactating Cow'
                            ),
                        ui.div(
                            ui.span("Note", class_='callout-title'), 
                            ui.p("Changing this will automatically update some other inputs. Check all inputs after modifying this."),
                            class_='callout callout-tip'),
                        class_="bg-light"
                    ),
                    ui.card(
                        ui.input_selectize(
                            'An_Breed', 
                            label = ui.span('Select breed:', style='font-weight:bold'),  
                            choices = {'Holstein':'Holstein', 'Jersey':'Jersey'}, 
                            selected = 'Holstein'
                        ),
                        class_="bg-light"
                    ),
                    
                    # ui.br(),
                    ui.card(
                        ui.input_numeric(
                            "An_BW", 
                            ui.span("Animal bodyweight (kg):", style='font-weight:bold'), 
                            700, 
                            min=0),
                        ui.input_numeric(
                            "An_BCS", 
                            ui.span("Animal body condition score (0-5):", style='font-weight:bold'), 
                            3, 
                            min=0, 
                            max=5),
                        class_="bg-light"
                    ),
                   
                    # ui.br(),
                    ui.card(
                        # converted to days in server:
                        ui.input_numeric(
                            "An_AgeMonth", 
                            ui.span("Animal age (months):", style='font-weight:bold'),
                            54, min=0),
                        ui.input_numeric(
                            "An_Parity_percent_first", 
                            ui.span("Percent of cows in first lactation:", style='font-weight:bold'), 
                            33, min=0, max=100),
                        class_="bg-light"
                    ),
                ),

                
                
                
            ),
            # ui.nav_panel(
            #     'Animal Management',
            #     ui.panel_conditional(
            #         "input.An_StatePhys === 'Lactating Cow'",
            #         ui.input_numeric("An_LactDay", "Average days in milk:", 100, min=0)
            #     ),
            #     ui.input_numeric("An_GestDay", "Average days pregnant (d)", 46, min=0),
            #     ui.br(),
            #     ui.p(
            #         ui.em("Body frame weight refers to the real growth of a younger animal. Body reserves refers to any fluctuations in body weight of a mature animal, e.g. due to lactation.")
            #         ),
            #     ui.input_numeric("Trg_FrmGain", "Target gain in body frame weight (kg fresh weight/d)", 0.60, min=0),
            #     ui.input_numeric("Trg_RsrvGain", "Target gain or loss of body reserves (kg fresh weight/d)", 0.10, min=0),

            #     ),
            ui.nav_panel(
                'Animal Management',
                ui.div(
                    ui.layout_column_wrap(
                        ui.card(
                            ui.panel_conditional(
                                "input.An_StatePhys === 'Lactating Cow'",
                                ui.input_numeric(
                                    "An_LactDay", 
                                    label=ui.span("Average days in milk:", style='font-weight:bold'), 
                                    value=100, 
                                    min=0
                                ),
                            ),
                            ui.input_numeric(
                                "An_GestDay", 
                                label=ui.span("Average days pregnant (d):", style='font-weight:bold'), 
                                value=46, 
                                min=0
                            ),
                            class_="bg-light"
                        ),
                        ui.card(
                            ui.input_numeric(
                                "Trg_FrmGain", 
                                label=ui.span("Target gain in body frame weight (kg fresh weight/d):", style='font-weight:bold'), 
                                value=0.60, 
                                min=0
                            ),
                            ui.input_numeric(
                                "Trg_RsrvGain", 
                                label=ui.span("Target gain or loss of body reserves (kg fresh weight/d):", style='font-weight:bold'), 
                                value=0.10, 
                                min=0
                            ),
                            ui.div(
                                ui.span("Note", class_='callout-title'),
                                ui.p(
                                    ui.em(
                                        "Body frame weight refers to the real growth of a younger animal. Body reserves refers to any fluctuations in body weight of a mature animal, e.g. due to lactation."
                                    )
                                ),
                                class_='callout callout-tip'
                            ),
                            class_="bg-light"
                        ),
                        
                    ),
                    style= htmltools.css(min_width='50%', margin='0 auto')
                )
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
                ui.input_numeric("An_BW_mature", "Animal mature bodyweight (kg):", 700, min=0),
               
                
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
                        # ui.input_selectize(
                        #     "DMIn_eqn",
                        #     label = "Select DM Intake equation to use for predicting intake on Diet page (default is 'lactating, cow factors only'). Does not change model, user input DMI is always used in this app.",
                        #     choices = DM_intake_equation_strings(),
                        #     selected = 8, # type: ignore
                        #     multiple = False,
                        #     width='500px'
                        #     ),                        
                        ui.input_radio_buttons(
                            "mProd_eqn", 
                            "Milk production equation to use for calcs (currently hard-coded to use Trg_MilkProd):",
                            choices = {0: 'Trg_MilkProd', 1: 'component based predicted', 
                                       2: 'NE Allowable', 3: 'MP Allowable', 4: 'min(NE,MPAllow)'},  # type: ignore
                            selected = 1 # type: ignore
                            ), 

                        ui.input_radio_buttons(
                            "mPrt_eqn", 
                            ("Milk Protein equations and AA coefficients to use."
                             "Target TP will use target TP for protein equations and NRC coefficients in AA equations.",
                             "Predict TP with NRC equations and coefficients (NRC 2021)", 
                             "VT1 coefficients from Dec. 20, 2020 - Virginia Tech (no Phe, Thr, Trp, or Val)",
                             "VT2 coefficients from April, 2022 solutions after further data cleaning - Virginia Tech (no Arg, Phe, Trp, or Val)"
                             ), 
                            choices = {0: "Target TP", 1: "Predicted: NRC", 2: "Predicted: VT1", 3: "Predicted: VT2"},
                            selected = 1),

                        ui.input_radio_buttons("mFat_eqn", "Milk Fat prediction equation", 
                                               choices = {0: "Trg_MilkFatp", 1: "Predicted milk fat production"}, 
                                               selected = 1),

                        ui.input_radio_buttons("MiN_eqn", "Microbial Nitrogen (MiN) equation to use.", 
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
                      
                        ui.input_radio_buttons("NonMilkCP_ClfLiq", "Calves: Non-milk protein source in calf liquid feeds?", choices={0: "No", 1: "Yes"}),
            
                        ui.input_radio_buttons("RumDevDisc_Clf", 
                                               "Calves: Rumen development discount", 
                                               choices={0: "No dry feed discount for ME due to undeveloped rumen.", 
                                                        1: "Use a 10% discount on dry feed if Liq>1.5% of BW"})
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
                'Trg_Dt_DMIn' : user_selected_DMI(), # This input is passed in from main app.py 
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
        '''Note: DMIn_eqn is on module_diet and hardcoded in NASEM_out()'''
        return {
            'Use_DNDF_IV' : input.Use_DNDF_IV(), 
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

            ui.insert_ui(
                ui.div(
                    ui.em('Dry cow is selected so no milk production data can be entered.'),
                    id = 'drycow_input_warning'
                ), 
                selector = "#milk_production_conditional_panel", # place the new UI's below the initial item input
                where = "afterEnd")
            
            ui.update_numeric('An_GestDay', value = 250)
            ui.update_numeric('Trg_FrmGain', value = 0.1)
            ui.update_numeric('Trg_RsrvGain', value = 0)
            ui.update_numeric('Trg_MilkProd', value = 0)
        
        elif animal_input_reactives()['An_StatePhys']() == 'Lactating Cow':
            ui.update_selectize('DMIn_eqn', selected='9')

            ui.remove_ui(selector="div#drycow_input_warning")
            
            ui.update_numeric('An_GestDay', value = 46)
            ui.update_numeric('Trg_FrmGain', value = 0)
            ui.update_numeric('Trg_RsrvGain', value = 0)
            ui.update_numeric('Trg_MilkProd', value = 35)
    
    ########################
    # Load session file
    ########################
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
    
        
    @render.ui
    def display_usr_session_modified_time():
        ''' This has the added function of instant dependency on pkl upload, leading to immediate modal warnings if something wrong.'''
        pkl_session_upload()
        return ui.div(
            {"class": "callout callout-tip", "role": "alert" },
            ui.div("Session Restored", class_ = "callout-title"),
            ui.markdown(
                f"""
                - .NDsession loaded from:  {pkl_session_upload()['SaveTime']}
                """
            )
        )
    

    # Unpack session dictionary
    def session_upload_library():
        return pkl_session_upload()['FeedLibrary']

    def session_upload_ModelOuput():
        return pkl_session_upload()['ModelOutput']
    
    ##############################
    # Update ui from session file
    ##############################
    @reactive.Effect
    def _():
        usr_ModOut = session_upload_ModelOuput()

        selectize_ids = ['An_StatePhys', 'An_Breed']

        for var_name in selectize_ids:
            val = usr_ModOut.get_value(var_name)
            ui.update_selectize(var_name, selected=val)


        numeric_ids = [
            'An_BW', 'An_BCS', 
            'An_LactDay', 'An_GestDay', 'Trg_FrmGain', 'Trg_RsrvGain', 
            'Trg_MilkProd', 'Trg_MilkFatp', 'Trg_MilkTPp', 'Trg_MilkLacp', 
            'An_BW_mature', 'An_GestLength', 'Fet_BWbrth', 'An_305RHA_MlkTP', 
            'An_AgeDryFdStart', 'Env_TempCurr', 'Env_DistParlor', 'Env_TripsParlor', 
            'Env_Topo'
        ]

        for var_name in numeric_ids:
            val = usr_ModOut.get_value(var_name)
            ui.update_numeric(var_name, value=val)




        radio_buttons = [
            'mProd_eqn', 'mPrt_eqn', 'mFat_eqn', 'MiN_eqn', 
            'Use_DNDF_IV', 'Monensin_eqn', 'NonMilkCP_ClfLiq', 'RumDevDisc_Clf'
        ]
        for var_name in radio_buttons:
            val = usr_ModOut.get_value(var_name)
            ui.update_radio_buttons(var_name, selected=val)

        # special cases:
        # special_cases = ['An_Parity_percent_first', 'An_AgeMonth']
        An_Parity_percent_first = (2 - usr_ModOut.get_value('An_Parity_rl')) * 100
        ui.update_numeric('An_Parity_percent_first', value = An_Parity_percent_first)

        An_AgeMonth =  usr_ModOut.get_value('An_AgeDay')/30.3
        ui.update_numeric('An_AgeMonth',value = An_AgeMonth)
        

        ui.notification_show('Inputs re-loaded from uploaded .NDsession successfully', type='message')


    return(animal_input_dict, animal_input_reactives, equation_selection, session_upload_library, session_upload_ModelOuput)
