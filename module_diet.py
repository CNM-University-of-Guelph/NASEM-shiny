# module_diet.py

from shiny import Inputs, Outputs, Session, module, render, ui, reactive, req
import pandas as pd
from faicons import icon_svg
import htmltools
import nasem_dairy as nd

from utils import (
    get_unique_feed_list,
    display_diet_values, 
    calculate_DMI_prediction, 
    validate_equation_selections, 
    prepare_df_render,
    get_vars_as_df,
    DM_intake_equation_strings) 


def insert_new_ingredient(current_iter, feed_choices, feed_selected, kg_selected, perc_selected, session_ns ):
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
            ui.column(3, ui.input_numeric('perc_' + current_iter,
                                          label="",
                                          min=0,
                                          max=100,
                                          step=0.2,
                                          value=perc_selected)),
        )
    )
    ui.insert_ui(newItemDiv,
                #  selector=f"#{session_ns}-item_input",
                 selector=f"div#userfeed_1",
                 where="beforeEnd",
                 immediate=True) # this allows js to access ui and disable perc in correct order


def remove_ingredient(current_iter):
    print(f'removing UI: userfeed_{current_iter}')
    ui.remove_ui(selector="div#userfeed_" + str(current_iter))

@module.ui
def diet_ui():
    return ([
        ui.layout_columns(
                ui.layout_columns(
                    ui.input_selectize(
                        "DMIn_eqn",
                        label =  ui.TagList(
                            ui.span("Select DM Intake equation for prediction: ", 
                                    style = htmltools.css(color='black', font_weight='bold')), 
                            ui.em("Target intake always used in model outputs.")
                            ),
                        choices = DM_intake_equation_strings(),
                        selected = 9, # type: ignore
                        multiple = False,
                        width='500px',
                        ),
                    ui.div(
                        ui.div("Predicted Feed Intake:", class_ = "callout-title2-black"),
                        ui.output_text('predicted_DMI'), 
                    ),
                    col_widths = (6,-1,5),
                    class_ = "callout callout-note"
                ),

                ui.layout_columns(
                    ui.span(
                        ui.input_numeric(
                            "DMI", 
                            ui.span(
                                ui.span("Target dry matter intake (kg/d):", class_ = "callout-title2-black"),
                                ui.tooltip(                               
                                    icon_svg("circle-info", margin_left='10px', height='1em'), 
                                    ui.em("This DM intake will be used throughout all model calculations. Predictions to left should guide what is entered here."),
                                    placement = 'left',
                                    ),
                            style = 'display: inline-flex; align-items: center;'),
                        25, 
                        min=0),
                        class_ = "callout-inner callout-tip",
                        style=htmltools.css(padding_bottom='0px')
                    ),
                    ui.span(
                        ui.p('Diet Sum (kg/d):', class_ = "callout-title2-black"), 
                        ui.span(ui.output_text('diet_total_intake'), class_='form-control form-control-disabled'),
                        style=htmltools.css(padding_top='0.5rem')
                        ),
                    ui.span(
                        ui.p('Difference (kg):', class_ = "callout-title2-black"), 
                        ui.span(ui.output_text("intake_difference"),class_='form-control form-control-disabled'),
                        style=htmltools.css(padding_top='0.5rem')
                        ),
                    
                    col_widths = (6, 3, 3),
                    class_ = "callout callout-caution",
                ),
            col_widths=(6,6),
            style = htmltools.css(margin_bottom='8px')
        ),
        ui.card(
            # ui.row(
            ui.layout_columns(
                # ui.column(6,
                ui.div(
                        ui.row(
                            ui.column(6, ui.h2("Formulate diet:")),
                            ui.column(6, ui.input_action_button("add_demo_diet", 
                                                                "Add demo lactating diet", 
                                                                class_='btn-info')),
                        ),
                        ui.br(),
                        ui.div(
                            {"id" : "userfeed_1" },
                            ui.row(
                                ui.column(6, ui.input_selectize("item_1" ,
                                                                "Choose feeds to use in ration:",
                                                                choices = {},
                                                                multiple = False)),
                                ui.column(3, ui.input_numeric('kg_1', 
                                            label="Enter kg DM:", 
                                            min=0, 
                                            max=100, 
                                            step = 0.2,
                                            value=0)),
                                ui.column(3, ui.input_numeric('perc_1',
                                            label = '% DM:',
                                            min = 0, 
                                            max = 100,
                                            step = 1, 
                                            value = 0))             
                            )
                        ),
                        ui.layout_column_wrap(
                            ui.input_action_button("add_button", "Add another feed", class_='btn-success'),
                            ui.input_action_button('btn_load_user_selected_feeds', 'Add feeds from sidebar', class_='btn-warning'),
                            ui.input_action_button("btn_reset_feeds", "Reset feeds", class_ = 'btn-danger'),
                        ),
                ),
                # ui.column(6,
                    ui.div(
                        ui.panel_well(
                             ui.span( 
                                    ui.h2("Model Outputs - Snapshot"),
                                        ui.tooltip(                               
                                            icon_svg("circle-info", margin_left='10px', height='1.8em'), 

                                            ui.tags.li(ui.em("The model is executed each time an ingredient selection or kg DM value changes.")),
                                            ui.tags.li(ui.em("The snapshot shows calculated diet proportions of key components and some predicted model outputs")),
                                            ui.tags.li(ui.em("Different outputs shown for dry cows")),
                                            placement = 'left',
                                        ),
                            style = 'display: inline-flex; align-items: center;'
                            ),

                           
                            ui.output_data_frame('snapshot_diet_data_model'),
                            ui.output_data_frame('model_snapshot')
                        ),
                        
                ),
                col_widths=(6,6)
            ),
            min_height='500px',
            style = htmltools.css(__bs_card_spacer_y='0.5rem'),
        ),
    ]) 

@module.server
def diet_server(input: Inputs, output: Outputs, session: Session, 
                NASEM_out, 
                animal_input_dict, 
                # equation_selection,
                animal_input_reactives,
                user_selected_feed_library,
                user_selected_feeds,
                session_upload_ModOut):
    
    #######################################################
    # Feed Inputs
    #######################################################
    #used for 'iterate new ingredient' because variables can't be parsed into these functions
    # so, the values are assigned to these 2 reactives which are then used by the iterate_new_ingredient function to set up a new feed
    # originally used by demo diets
    feed_selected = reactive.Value(None)
    kg_selected = reactive.Value(0)
    perc_selected = reactive.Value(0)

    # Initialize reactive values to store user selections
    user_feeds = reactive.Value(['item_1'])
    user_kgs = reactive.Value(['kg_1'])
    user_percs = reactive.Value(['perc_1'])

    @reactive.Calc
    def unique_fd_list():
        return get_unique_feed_list(user_selected_feed_library())
    
    
    @reactive.effect
    def _():
        ui.update_selectize('item_1', choices=unique_fd_list())



    @reactive.Calc
    def iterate_new_ingredient():
        '''
        This is executed by the reactive event below, and keeps track of new UI 
        created so that the feed name and kg can be used meaningfully in app.
        '''
        reset_flag.set(False)
        current_iter =  str(len(user_feeds()) + 1)

        # copy, append and re-set items and percentages, to keep track of inputs
        xout = user_feeds().copy()
        xout.append('item_' + current_iter)
        user_feeds.set(xout)

        kgout = user_kgs().copy()
        kgout.append('kg_' + current_iter)
        user_kgs.set(kgout)

        pout = user_percs().copy()
        pout.append('perc_' + current_iter)
        user_percs.set(pout)

        insert_new_ingredient(current_iter = current_iter, 
                              feed_choices = unique_fd_list(), 
                              feed_selected=feed_selected(), 
                              kg_selected=kg_selected(),
                              perc_selected=perc_selected(),
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
        feed_list = user_selected_feeds().to_list()

        for i, feed in enumerate(feed_list):
            if i == 0:
                ui.update_selectize(id = 'item_1', choices = unique_fd_list(), selected = feed)
                ui.update_numeric(id = 'kg_1', value = 0, min=0)
                ui.update_numeric(id = 'perc_1', value = 0, min=0)
            else:
                feed_selected.set(feed) # type: ignore
                kg_selected.set(0)
                perc_selected.set(0)
                iterate_new_ingredient()
        
        # reset to defaults
        feed_selected.set(None)
        kg_selected.set(0)
        perc_selected.set(0)

    # starts as True because first row is never removed. is set to False for iterate new ingredient
    reset_flag = reactive.value(True)

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
        user_percs.set(['perc_1'])

        # Update initial UI elements:
        ui.update_selectize(id = 'item_1', choices=unique_fd_list())
        ui.update_numeric(id = 'kg_1', value = 0, min=0)

        # add demo button back:
        if input.add_demo_diet() > 0:
            await session.send_custom_message("toggleUIHandler", {
                    "UIObjectId": session.ns("add_demo_diet"), "action" : "enable"
                })
        reset_flag.set(True)


    @reactive.Calc
    def get_user_diet():
        # Get items from input by name
        # returns a dataframe as a reactive
        # each 'feed' and 'kg' value is stored in these reactives (named 'item_1', etc) 
        # which means we can iterate through them and store their values in a list when we need them
        items = [getattr(input, x) for x in user_feeds()]
        kg = [getattr(input, x) for x in user_kgs()]

        # Safely convert items to strings, handling None types
        feedstuff = [str(x()) if x() is not None else '' for x in items]
        # Safely convert kg to floats, handling None types
        kg_user = [float(x()) if x() is not None else 0.0 for x in kg]

        tmp_user_diet = pd.DataFrame({'Feedstuff': feedstuff, 
                                      'kg_user': kg_user})

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
        # IF model has been executed, then use the user-input selection
        eqn_DMI = validate_equation_selections({'DMIn_eqn' : input.DMIn_eqn()})
        
        if get_diet_total_intake() > 0:
            req(NASEM_out())
            # This doesn't have a button to execute - changes each time the animal inputs change

            pred_DMI = calculate_DMI_prediction(
                animal_input=animal_input_dict().copy(),
                DMIn_eqn= eqn_DMI['DMIn_eqn'],
                model_output=NASEM_out(),
                coeff_dict= nd.coeff_dict
            )
            
            return str(f"{pred_DMI} kg DM/d")
        else:
            # use equation that does not use diet:
            pred_DMI = calculate_DMI_prediction(
                animal_input=animal_input_dict().copy(),
                DMIn_eqn= eqn_DMI['DMIn_eqn'],
                model_output=None,
                coeff_dict= nd.coeff_dict
            )
            return str(f"{pred_DMI} kg DM/d (using 'animal factors only' until diet is entered)")

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
        ui.update_selectize(id='item_1', choices=unique_fd_list(), selected="Corn silage, typical")
        ui.update_numeric(id='kg_1', value=9, min=0)

        demo_dict = {
            'Wheat straw': 1,
            'Corn grain HM, fine grind': 5,
            'Triticale silage, mid-maturity': 6.4,
            'Calcium phosphate (di)': 0.2,
            'Sodium bicarbonate': 0.2,
            'Soybean meal, expellers': 3,
            'Urea': 0.15,
        }

        for feed, kg in demo_dict.items():
            feed_selected.set(feed)
            kg_selected.set(kg)
            perc_selected.set(0)
            iterate_new_ingredient()

        feed_selected.set(None)
        kg_selected.set(0)
        perc_selected.set(0)
        
        # disable button to prevent loading multiple times. On reset, this button 
        # is enabled again.
        await session.send_custom_message("toggleUIHandler", {
                "UIObjectId": session.ns("add_demo_diet"), "action" : "disable"
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

            df_lac_snapshot = (
                get_vars_as_df(vars_return, NASEM_out())
                .drop(columns='Model Variable')
                .reindex(columns=['Description', 'Value']))
            return df_lac_snapshot
               
        elif animal_input_reactives()['An_StatePhys']() == 'Dry Cow':
            vars_return = ['An_MEIn', 'Trg_MEuse', 'An_MEbal', 'An_MPIn_g', 
                           'An_MPuse_g_Trg', 'An_MPBal_g_Trg','An_RDPIn_g', 
                           'Du_MiCP_g','An_RDPbal_g', 'An_DCADmeq']
            
            df_dry_snapshot = (
                get_vars_as_df(vars_return, NASEM_out())
                .drop(columns='Model Variable')
                .reindex(columns=['Description', 'Value'])
                )
            return df_dry_snapshot
        
        else:
            return pd.DataFrame()


    @render.data_frame
    def model_snapshot():
        return prepare_df_render(df_model_snapshot(), 10, 90, cols_longer=['Description'])


    @render.data_frame
    @reactive.event(NASEM_out)
    def snapshot_diet_data_model():
        '''
        A snapshot of the diet composition
        '''
        df = display_diet_values(NASEM_out(), is_snapshot=True)
        return prepare_df_render(df, 1, 90, cols_longer='Component') 


    @reactive.Effect
    # @reactive.event(user_kgs)
    def _():
        total_intake = get_diet_total_intake()
        for kg_id, perc_id in zip(user_kgs(), user_percs()):
            kg_value = getattr(input, kg_id)()

            if total_intake > 0 and kg_value is not None:
                perc_value = (kg_value / total_intake) * 100
                perc_value = float(f"{perc_value:.3g}") # 3 significant figures
            else:
                perc_value = 0
            ui.update_numeric(id=perc_id, value=perc_value, min=0)

    @reactive.effect
    async def _():
            perc_IDs = [session.ns(p) for p in user_percs()]
            # req(all([await session.run_js(f"document.getElementById('{el_id}') !== null") for el_id in perc_IDs]))

            await session.send_custom_message("disableUIList", {
                    "UIObjectIds": perc_IDs
                })
            
    ########################################
    # reset diet and reload from usr session
    ########################################
   
    
    # @reactive.effect
    # @reactive.event(session_upload_ModOut )
    # def _():
    #     # get number of UI elements
    #     current_iter =  len(user_feeds())+1
        
    #     # remove UI elements
    #     [remove_ingredient(i) for i in range(2,current_iter)]

    #     # reset reactive values to store user selections
    #     user_feeds.set(['item_1'])
    #     user_kgs.set(['kg_1'])
    #     user_percs.set(['perc_1'])

    #     # Update initial UI elements:
    #     ui.update_selectize(id = 'item_1', choices=unique_fd_list())
    #     ui.update_numeric(id = 'kg_1', value = 0, min=0)

    #     reset_flag.set(True)


        

    @reactive.effect
    @reactive.event(session_upload_ModOut)
    def _():
        '''If usr uploads pickle session file, replace diet from previous session. '''

        if reset_flag() == False:
            m = ui.modal(
                ui.p('Feeds already entered in Diet. Please reset before uploading .NDsession.'),
                title='Diet warning',
                easy_close=True,
            )
            ui.modal_show(m)

        elif session_upload_ModOut() is not None and isinstance(session_upload_ModOut(), nd.ModelOutput):


            # # disable demo diet:



            # # re-populate diet
            user_diet = session_upload_ModOut().get_value('user_diet')
            # strip white space from column names (seems to add spaces after Feedstuff when an ingredient is missing
            user_diet.columns = user_diet.columns.str.strip()

            # Handle the first entry manually
            first_entry = user_diet.iloc[0]
            ui.update_selectize(id='item_1', choices=unique_fd_list(), selected=first_entry['Feedstuff'])
            ui.update_numeric(id='kg_1', value=first_entry['kg_user'], min=0)

            print(f'test: {user_feeds()}')
            # Iterate over the remaining entries
            for index, row in user_diet.iloc[1:].iterrows():
                print(user_feeds())
                feed_selected.set(row['Feedstuff'])
                kg_selected.set(row['kg_user'])
                perc_selected.set(0)
                iterate_new_ingredient()
            print('done')

            # reset helpers before finishing
            feed_selected.set(None)
            kg_selected.set(0)
            perc_selected.set(0)
            
        else:
            #not sure if this is possible
            print('no .NDsession diet')



    return(get_user_diet, get_diet_total_intake, input.DMI, df_model_snapshot)