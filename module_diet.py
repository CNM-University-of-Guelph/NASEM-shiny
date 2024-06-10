# module_diet.py

from shiny import Inputs, Outputs, Session, module, render, ui, reactive, req
import pandas as pd

import nasem_dairy as nd

from utils import (
    get_unique_feed_list,
    display_diet_values, 
    calculate_DMI_prediction, 
    validate_equation_selections, 
    prepare_df_render,
    get_vars_as_df) 


def insert_new_ingredient(current_iter, feed_choices, feed_selected, kg_selected, session_ns ):
    newItemDiv = ui.div(
        {"id": "userfeed_" + current_iter},
        ui.row(
            ui.column(6, ui.input_selectize("item_" + current_iter,
                                            label="",
                                            choices=feed_choices,
                                            selected=feed_selected,
                                            multiple=False)),
            ui.column(3, ui.input_numeric('kg_' + current_iter,
                                          label="",
                                          min=0,
                                          max=100,
                                          step=0.2,
                                          value=kg_selected)),
        )
    )
    ui.insert_ui(newItemDiv,
                 selector=f"#{session_ns}-item_input",
                 where="beforeEnd")


def remove_ingredient(current_iter):
    ui.remove_ui(selector="div#userfeed_" + str(current_iter))

@module.ui
def diet_ui():
    return ([
        # ui.nav_panel(
        #     "Diet",
            ui.card(
                ui.row(
                    ui.column(4,
                            ui.p("Predicted Feed Intake:"),
                            ui.output_text('predicted_DMI')
                    ),
                    ui.column(3, ui.input_numeric("DMI", "Target dry matter intake (kg/d)", 26, min=0)),
                    ui.column(2, ui.p('Total diet intake (kg/d):'), ui.output_text('diet_total_intake')),
                    ui.column(2, ui.p('Difference (kg):'), ui.output_text("intake_difference")),
                ),
                ui.card(
                    ui.row(
                        ui.column(6,
                                ui.row(
                                    ui.column(6, ui.h2("Formulate ration:")),
                                    ui.column(6, ui.input_action_button("add_demo_diet", "Add demo lactating diet", class_='btn-info')),
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
                                    ui.p(ui.em("The model is executed each time an ingredient selection or kg DM value changes. " 
                                               "The following snapshot shows the calculated diet proportions of key components and" 
                                               " some model outputs (different output is shown for dry cows):")),
                                    ui.output_data_frame('snapshot_diet_data_model'),
                                    ui.output_data_frame('model_snapshot')
                                ),
                        )
                    )
                ),
                min_height='650px'
            )
        # )
    ]) 

@module.server
def diet_server(input: Inputs, output: Outputs, session: Session, 
                NASEM_out, 
                animal_input_dict, 
                equation_selection,
                animal_input_reactives,
                user_selected_feed_library,
                user_selected_feeds):
    
    #######################################################
    # Feed Inputs
    #######################################################
    #used for 'iterate new ingredient' because variables can't be parsed into these functions
    # so, the values are assigned to these 2 reactives which are then used by the iterate_new_ingredient function to set up a new feed
    # originally used by demo diets
    feed_selected = reactive.Value(None)
    kg_selected = reactive.Value(0)

    # Initialize reactive values to store user selections
    user_feeds = reactive.Value(['item_1'])
    user_kgs = reactive.Value(['kg_1'])

    @reactive.Calc
    def unique_fd_list():
        return get_unique_feed_list(user_selected_feed_library())

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
        This is executed by the reactive event below, and keeps track of new UI 
        created so that the feed name and kg can be used meaningfully in app.
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
                              feed_selected=feed_selected(), 
                              kg_selected=kg_selected(),
                              session_ns = session.ns
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
    async def _():
        '''
        Used to reset feeds back to normal by removing an UI created and 
        resetting reactive variables that store state.
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
            await session.send_custom_message("toggleButtonHandler", {
                    "buttonId": session.ns("add_demo_diet"), "action" : "enable"
                })


    @reactive.Calc
    def get_user_diet():
        # Get items from input by name
        # returns a dataframe as a reactive
        # each 'feed' and 'kg' value is stored in these reactives (named 'item_1', etc) 
        # which means we can iterate through them and store their values in a list when we need them
        items = [getattr(input, x) for x in user_feeds()]
        kg = [getattr(input, x) for x in user_kgs()]

        tmp_user_diet = pd.DataFrame({'Feedstuff': [str(x()) for x in items],
                                      'kg_user': [float(x()) for x in kg]})

        tmp_user_diet['Feedstuff'] = tmp_user_diet['Feedstuff'].str.strip()
        tmp_user_diet['Index'] = tmp_user_diet['Feedstuff']
        tmp_user_diet = tmp_user_diet.set_index('Index')

        return tmp_user_diet

    @reactive.Calc
    def get_diet_total_intake() -> float:
        return get_user_diet()['kg_user'].sum(numeric_only=True)

    #########################################################
    # DMI intake 
    #########################################################
    @render.text
    def predicted_DMI():
        # Dt_NDF = NASEM_out()["diet_info"].loc['Diet','Fd_NDF'].copy()
        print('start predDMI')
        # IF model has been executed, then use the user-input selection
        if get_diet_total_intake() > 0:
            print('step2')
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

    @render.text
    def diet_total_intake():
        return get_diet_total_intake()

    @render.text
    def intake_difference():
        return round((get_diet_total_intake() - input.DMI()), 3)
    
          
    ########################
    # Add Demo diet
    ########################

    @reactive.Effect
    @reactive.event(input.add_demo_diet)
    async def _():
        ui.update_selectize(id='item_1', choices=unique_fd_list(), selected="Canola meal")
        ui.update_numeric(id='kg_1', value=2.5)

        demo_dict = {
            'Corn silage, typical': 7,
            'Triticale silage, mid-maturity': 6.5,
            'Corn grain HM, fine grind': 7,
            'Wheat straw': 1.2,
            'Urea': 0.3,
            'VitTM Premix, generic': 0.5,
        }

        for feed, kg in demo_dict.items():
            feed_selected.set(feed)
            kg_selected.set(kg)
            iterate_new_ingredient()

        feed_selected.set(None)
        kg_selected.set(0)

        # disable button to prevent loading multiple times. On reset, this button 
        # is enabled again.
        await session.send_custom_message("toggleButtonHandler", {
                "buttonId": session.ns("add_demo_diet"), "action" : "disable"
            })



    ##################################################################
    # Model evaluation & 'snapshots'
    ##################################################################
    
    @reactive.Calc
    def df_model_snapshot():
        '''
        A 'snapshot' of the model output, which varies between lactating and 
        dry cows. Other animal classes could be added here, with similar pattern.
        '''
        if animal_input_reactives()['An_StatePhys']() == 'Lactating Cow':
            vars_return = ['Mlk_Prod_comp','MlkFat_Milk_p', 'MlkNP_Milk_p', 
                           'Mlk_Prod_MPalow', 'Mlk_Prod_NEalow', 'An_RDPbal_g', 
                           'Du_MiCP_g']
                                
            new_var_names = {
                'Mlk_Prod_comp': 'Milk Production (kg/d)',
                'MlkFat_Milk_p': 'Milk Fat %',
                'MlkNP_Milk_p': 'Milk Protein %',
                'Mlk_Prod_MPalow': 'MP Allowable Milk Production (kg/d)',
                'Mlk_Prod_NEalow': 'NE Allowable Milk Production (kg/d)',
                'An_RDPbal_g': 'Animal RDP Balance (g)',
                'Du_MiCP_g': 'Duodenal Microbial CP (g) '
            }

            df_lac_snapshot = get_vars_as_df(vars_return, NASEM_out()).assign(
                Variable = lambda df: df['Model Variable'].map(new_var_names)
            )
            return df_lac_snapshot
               
        elif animal_input_reactives()['An_StatePhys']() == 'Dry Cow':
            vars_return = ['An_MEIn', 'Trg_MEuse', 'An_MEbal', 'An_MPIn_g', 
                           'An_MPuse_g_Trg', 'An_MPBal_g_Trg','An_RDPIn_g', 
                           'Du_MiCP_g','An_RDPbal_g', 'An_DCADmeq']
            
            df_dry_snapshot = get_vars_as_df(vars_return, NASEM_out())
            return df_dry_snapshot
        
        else:
            return pd.DataFrame()


    @render.data_frame
    def model_snapshot():
        return prepare_df_render(df_model_snapshot(), 10, 50, cols_longer=['Description'])


    @render.data_frame
    @reactive.event(NASEM_out)
    def snapshot_diet_data_model():
        '''
        A snapshot of the diet composition
        '''
        df = display_diet_values(NASEM_out(), is_snapshot=True)
        return prepare_df_render(df, 1, 90, cols_longer='Component') 


    return(get_user_diet, get_diet_total_intake, input.DMI, df_model_snapshot)