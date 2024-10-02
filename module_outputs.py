# module_outputs.py

from shiny import Inputs, Outputs, Session, module, render, ui, module, reactive, req
import pandas as pd
from datetime import date
import io
import pickle
from datetime import datetime

from version import __version__
from utils import display_diet_values, get_vars_as_df, get_clean_vars, prepare_df_render, coerce_non_text_to_numeric
from generate_report import generate_summary_report, generate_full_report
import nasem_dairy as nd

@module.ui
def outputs_ui():
    return ([ 
        ui.panel_title("NASEM Model Outputs"),
        ui.row(
            ui.column(3, ui.p(ui.em("The model is executed each time an ingredient selection or kg DM value changes."))),
            ui.column(2, ui.download_button("btn_download_report", "Download Summary Report", class_='btn-warning'), offset=1),
            ui.column(2, ui.download_button("btn_download_full_report_tables", "Download Full Report", class_='btn-warning')),
            ui.column(3, ui.download_button("btn_pkl_download", "Download .NDsession file", class_='btn-info'))
        ),
        ui.br(),
        ui.navset_card_tab(
            ui.nav_panel(
                'Model Evaluation',
                ui.div(
                    {"class": "left-align-container" },
                    ui.h5('Milk production estimates:'),
                    ui.output_data_frame('key_model_data_milk',),
                    ui.br(),
                    ui.h5('Milk production allowed (kg/d) from available NE or MP:'),
                    ui.output_data_frame('key_model_data_allowable_milk'),
                    ui.br(),
                    ui.h5('Metabolisable energy balance:'),
                    ui.output_data_frame('key_model_data_ME'),
                    ui.br(),
                    ui.h5('Metabolisable protein balance:'),
                    ui.output_data_frame('key_model_data_MP'),
                    ui.br(),
                )
                
            ),
            ui.nav_panel(
                'Diet Analysis',
                ui.h5('Diet summary:'),
                ui.output_data_frame('diet_summary_model'),
                ui.br(),
                ui.h5('NEL:'),
                ui.output_data_frame('key_model_data_NEL'),
                ui.br(),
                ui.h5('DCAD:'),
                ui.output_data_frame('key_model_data_DCAD'),
                ui.br(),
                ui.h5("Ration ingredients:"),
                ui.output_data_frame('user_diet'),
            ),
            ui.nav_panel(
                'Vitamins and Minerals',
                ui.h6('Macro Minerals'),
                ui.output_data_frame('macro_minerals'),
                ui.br(),
                ui.h6("Micro Minerals"),
                ui.output_data_frame('micro_minerals')
            ),
            # ui.nav_panel(
            #     "Energy - teaching",
            #     ui.output_data_frame('key_model_data_energy_teaching')
            # ),
            # ui.nav_panel(
            #     'Advanced',
            #     ui.br(),
            #     ui.h4('extended output'),
            #     ui.output_data_frame('diet_info'),
            #     ui.h4("Confirm Model inputs:"),
            #     ui.output_data_frame('animal_input_table_comparison'),
            #     ui.p("Equation Selections:"),
            #     ui.output_data_frame('equation_selection_table'),
            # ),
            ui.nav_panel(
                'Search Output',
                ui.card(
                    ui.card_header('Search ModelOutput:'),
                    ui.span(
                        ui.input_text('ModOut_search', label='Search term:', value='Mlk', placeholder=True), 
                        style='margin:0 auto'),
                    ui.output_data_frame('ModOut_search_return'),
                    full_screen=True
                ),
                ui.card(
                    ui.card_header("Show all model output?"),
                    ui.span(ui.input_switch("show_all_output", label='Show all model outputs?'),style='margin:0 auto'),
                    ui.output_data_frame('ModOut_all'),
                    full_screen=True
                )

            ),
        ),
    ]) 

@module.server
def outputs_server(input: Inputs, output: Outputs, session: Session, 
                   NASEM_out, 
                   user_selected_feed_library,
                   animal_input_dict,
                   df_model_snapshot
                   ):

    ######################################################
    # Prepare dataframes to render to UI or use in report
    ######################################################
    @reactive.Calc
    def df_key_model_data_milk():
        vars_return = ['Mlk_Prod_comp', 'MlkFat_Milk_p', 'MlkNP_Milk_p']
        return get_vars_as_df(vars_return, NASEM_out())

    @reactive.Calc
    def df_key_model_data_allowable_milk():
        vars_return = ['Mlk_Prod_MPalow', 'Mlk_Prod_NEalow']
        return get_vars_as_df(vars_return, NASEM_out())

    @reactive.Calc
    def df_key_model_data_ME():
        vars_return = ['An_MEIn', 'Trg_MEuse', 'An_NEIn']
        return get_vars_as_df(vars_return, NASEM_out())

    @reactive.Calc
    def df_key_model_data_MP():
        vars_return = ['An_MPIn', 'An_MPuse_kg_Trg']

        return get_vars_as_df(vars_return, NASEM_out())

    @reactive.Calc
    def df_key_model_data_DCAD():
        vars_return = ['An_DCADmeq']
        return get_vars_as_df(vars_return, NASEM_out())

    @reactive.Calc
    def df_key_model_data_NEL():
        vars_return = ['An_NE', 'An_NEIn']
        return get_vars_as_df(vars_return, NASEM_out())

    @reactive.Calc 
    def df_key_model_data_energy_teaching():
        vars_return = ['Trg_MEuse', 'An_MEmUse', 'An_MEgain', 'Gest_MEuse', 'Trg_Mlk_MEout', 'An_MEIn', 'Frm_NEgain', 'Rsrv_NEgain', 'GrUter_BWgain', 'An_MEIn', 'Mlk_Prod_NEalow', 'An_MEavail_Milk']
        return get_vars_as_df(vars_return, NASEM_out())

    ######################################################
    # Render tables for UI
    ######################################################

    @render.data_frame
    def key_model_data_milk():
        return prepare_df_render(df_key_model_data_milk())

    @render.data_frame
    def key_model_data_allowable_milk():
        return prepare_df_render(df_key_model_data_allowable_milk())

    @render.data_frame
    def key_model_data_ME():
        return prepare_df_render(df_key_model_data_ME())

    @render.data_frame
    def key_model_data_MP():
        return prepare_df_render(df_key_model_data_MP())

    @render.data_frame
    def key_model_data_DCAD():
        return prepare_df_render(df_key_model_data_DCAD())

    @render.data_frame
    def key_model_data_NEL():
        return prepare_df_render(df_key_model_data_NEL())

    @render.data_frame
    def key_model_data_energy_teaching():
        return prepare_df_render(df_key_model_data_energy_teaching())

    @render.data_frame
    def diet_summary_model():
        df = display_diet_values(NASEM_out())
        return prepare_df_render(df, 10, 80, cols_longer='Component')
     
    @render.data_frame
    def user_diet():
        df = NASEM_out().get_value('user_diet')
        return prepare_df_render(df, 5, 60, cols_longer='Feedstuff') 

    @render.data_frame
    def diet_info():
        df = NASEM_out().get_value("diet_info")
        return prepare_df_render(df, 20, 60, cols_longer='Feedstuff')
    
    @reactive.Calc
    def df_user_input_compare() -> pd.DataFrame:
        df_user_input_SHINY = pd.DataFrame(animal_input_dict().items(), columns=['Variable Name', 'Value_SHINY'])
        df_user_input_RETURN = pd.DataFrame(NASEM_out().get_value('animal_input').items(), columns=['Variable Name', 'Value_Model_Return'])

        df_user_input_compare = df_user_input_SHINY.merge(
            df_user_input_RETURN,
            on='Variable Name',
            how='outer')

        return df_user_input_compare

     
    @render.data_frame
    def animal_input_table_comparison():
        return prepare_df_render(df_user_input_compare(), cols_longer=None, use_DataTable=False)

     
    @render.data_frame
    def equation_selection_table():
        df = pd.DataFrame(NASEM_out().get_value('equation_selection').items(), columns=['Variable Name', 'Value'])
        return prepare_df_render(df, cols_longer=None, use_DataTable=False)

     
    @render.data_frame
    def macro_minerals():
        # df = NASEM_out().report_minerals()['macro_minerals'].round(3)
        df = coerce_non_text_to_numeric(NASEM_out().get_report('table7_1'), 2)
        return prepare_df_render(df, cols_longer=None, use_DataTable=False)

     
    @render.data_frame
    def micro_minerals():
        # df = NASEM_out().report_minerals()['micro_minerals'].round(3)
        df = coerce_non_text_to_numeric(NASEM_out().get_report('table7_2'), 2)
        return prepare_df_render(df, cols_longer=None, use_DataTable=False)

    @render.download(filename=lambda: f"NASEM_report-{date.today().isoformat()}.html")
    def btn_download_report():
        html_out = generate_summary_report(
            df_milk=df_key_model_data_milk(),
            df_allowable_milk=df_key_model_data_allowable_milk(),
            df_ME=df_key_model_data_ME(),
            df_MP=df_key_model_data_MP(),
            df_diet_summary=display_diet_values(NASEM_out()),
            df_DCAD=df_key_model_data_DCAD(),
            df_NEL=df_key_model_data_NEL(),
            df_ration_ingredients=NASEM_out().get_value('user_diet'),
            df_energy_teaching=df_key_model_data_energy_teaching(),
            df_animal_input_comparison=df_user_input_compare(),
            dict_equation_selections=NASEM_out().get_value('equation_selection'),
            df_snapshot=df_model_snapshot()
            # df_snapshot=df_model_snapshot() if animal_input_reactives()['An_StatePhys']() == 'Lactating Cow' else df_model_snapshot_drycow()
        )

        with io.StringIO() as buf:
            buf.write(html_out)
            yield buf.getvalue()


    @render.download(filename=lambda: f"NASEM-report-all-tables-{date.today().isoformat()}.html")
    def btn_download_full_report_tables():
        table_names = [
            "table1_1", "table1_2", "table1_3b", "table2_1", "table2_2", 
            "table3_1", "table4_1", "table4_2", "table4_3", "table5_1", 
            "table6_1", "table6_2", "table6_3", "table6_4", "table6_5", 
            "table7_1", "table7_2", "table7_3", "table8_1", "table8_2"
        ]

        # Assuming `model_output` is an instance of `nd.ModelOutput`
        html_report = generate_full_report(NASEM_out(), table_names)
        
        with io.StringIO() as buf:
            buf.write(html_report)
            yield buf.getvalue()


    #######################
    # Save Session file 
    # a pickle file using the .NDsession extension

    # Download handler
    @render.download(filename = lambda: f"NASEM_simulation-{date.today().isoformat()}.NDsession")
    def btn_pkl_download():
        req(NASEM_out())
        now = datetime.now()
        # Format the date and time as a string
        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")

        output_dict = {
            'ModelOutput' : NASEM_out(),
            'FeedLibrary' : user_selected_feed_library(),
            'SaveTime': formatted_datetime,
            "AppVersion": __version__,
            "ndVersion": nd.__version__
        }
        with io.BytesIO() as buf:
            pickle.dump(output_dict, buf)
            yield buf.getvalue()

    ################################
    # Model Search
    ################################
    @render.data_frame
    def ModOut_search_return():
        req(NASEM_out())
        if len(input.ModOut_search()) == 0:
            return pd.DataFrame({})
        else:
            df = NASEM_out().search(input.ModOut_search())
            if df.empty:
                return pd.DataFrame({})
            else:
                return render.DataGrid(df, summary=False, filters=True)
        
    @render.data_frame
    def ModOut_all():
        req(NASEM_out())
        
        if input.show_all_output():
             # Function to filter the dictionary to keep only numerical values
            def filter_dict(data):
                return {k: v for k, v in data.items() if isinstance(v, (int, float))}

            # Filter the dictionary
            filtered_dict = filter_dict(NASEM_out().export_to_dict())
    
            filtered_data = {var: get_clean_vars(var, NASEM_out()) for var in filtered_dict}
            


            # Convert the filtered dictionary to a DataFrame
            df = pd.DataFrame.from_dict(filtered_data, orient="index", columns=['Value']).reset_index(names="Name")
            return render.DataGrid(df, summary=False, filters=True)

    
