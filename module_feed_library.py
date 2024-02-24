import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui, module, reactive, req
from shinywidgets import output_widget, render_widget, reactive_read
from ipydatagrid import DataGrid

from utils import get_teaching_feeds, get_unique_feed_list, rename_df_cols_Fd_to_feed

@module.ui
def feed_library_ui():
     return ([
        ui.card(
                ui.layout_column_wrap(
                    ui.p('View column groups:'),
                    ui.input_switch('cols_show_all', 'Show all columns'),
                    ui.accordion(
                        ui.accordion_panel("Advanced", ui.input_checkbox("hide_calf_feeds", "Hide calf related feeds:", True), value="Advanced"),
                        open=False
                        ),
                    width = 1/4,
                    fill=False,
                    heights_equal='row'
                    ),
                ui.panel_conditional( "!input.cols_show_all",
                    ui.layout_column_wrap(                  
                        ui.input_switch('cols_common', 'Commonly used',  value=True),                    
                        ui.input_switch("cols_amino_acids", "Amino Acids"),
                        ui.input_switch('cols_fatty_acids', 'Fatty Acids'),
                        ui.input_switch('cols_vitamins', 'Vitamins'),
                        ui.input_switch('cols_minerals', 'Minerals'),
                        width=1/5
                        )
                    ),

                ),

        ui.card(
            ui.layout_sidebar(
                ui.sidebar(
                        ui.input_switch('use_teaching_fd_library', 'Use teaching feed library', value=True),
                        ui.br(),
                        ui.input_file('user_lib_upload', 'Upload custom feed library (.csv)', accept='.csv'),
                        ui.br(),
                        ui.p("Feeds selected by user:"),
                        ui.output_data_frame('user_selected_feed_names'),
                        ui.br(),
                        ui.input_action_button('reset_user_selected_feed_names', "Clear list")
                    ),
                ui.p("Click on a row in the table below to store the Feed Name in the side panel. This is a temporary list that will be shown you create your diet in the next step."),
                output_widget('grid_feed_library', fill = True),
                ui.output_text_verbatim('file_upload_summary')
                ),
            full_screen=True,
            min_height= '600px'
            )
        ])


@module.server
def feed_library_server(input: Inputs, output: Outputs, session: Session, feed_library_default: pd.DataFrame, user_selections_reset):
    '''
    input,output,session = required Shiny arguments
    feed_library_default = default NASEM feed library that should be parsed to module on load
    user_selections_reset = an input.button event that will trigger the stored user_selections to be cleared from list

    Returns:
    - user_selected_feed_library
    - user_selected_feeds
    '''
    #######################################################
    # Feed Library
    #######################################################
    # set up feed library so that it can change based on user inputs
    # for now there is a bool for 'teaching' where the table is filtered
   

    @reactive.Calc
    def user_selected_feed_library():
        
        if input.use_teaching_fd_library():
            teaching_feeds =  get_teaching_feeds()

            df_user_lib = feed_library_default.query('Fd_Name.isin(@teaching_feeds)')
            return df_user_lib
        
        if input.user_lib_upload() is None:
            print('No file uploaded and teaching mode not selected')
            df_user_lib = feed_library_default
        
        else:
            print(input.user_lib_upload()[0])
            f = input.user_lib_upload()[0]
            
            if f['type'] == 'text/csv':
                # print('file == text/csv')
                # read in file
                df_in = pd.read_csv(f['datapath'])
                
                # Check if all column names are present
                req_cols = feed_library_default.columns
                
                if not all(col_name in df_in.columns for col_name in req_cols):
                    raise ValueError("Not all required columns are present in the uploaded feed library.")
                
                # sort data and assign for use        
                df_user_lib = df_in.sort_values("Fd_Name")
            
            else:
                print('User upload failed - using default lib')
                df_user_lib = feed_library_default

        # print(df_user_lib.info())
        return df_user_lib


    
    @reactive.Calc
    def df_feed_library():
        '''
        This step is required to rename columns to match nasem_dairy code. 
        '''
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
        # This take a dependency on the user selection, which updates every time a cell is clicked
        prepare_user_selected_feed_names()
        
        # then, execute this code but preventing other code taking a dependency on it - prevents infinite loop
        with reactive.isolate():
            fd_lib_stored_copy = feed_library_index_stored().copy()

            # add on user selected feed names to reactive list
            fd_lib_stored_copy.extend(prepare_user_selected_feed_names())
            
            # remove duplicates (by converting to set) and then set the reactiveValue as this new list
            feed_library_index_stored.set(list(set(fd_lib_stored_copy)))


    @reactive.Effect
    @reactive.event(input.reset_user_selected_feed_names, user_selections_reset)
    def _():
        ''' Reset the user selections from DataGrid clicking events. Clears the list in UI.'''
        feed_library_index_stored.set([])

    @reactive.Calc
    def user_selected_feeds():
            return(
                    df_feed_lib_userfriendly()
                    .reset_index(drop = True) # reset's index to match a 'row number' from selection with index (after filtering)
                    .loc[feed_library_index_stored(),'Feed Name'])


    # @reactive.Calc
    # def user_selected_feeds_list():
    #         return user_selected_feeds().to_list()

    @output
    @render.data_frame
    def user_selected_feed_names():
        return pd.DataFrame(user_selected_feeds())
    
    # @reactive.Effect 
    # def _():
    #     print(df_feed_library().info())
    return(user_selected_feed_library, user_selected_feeds)