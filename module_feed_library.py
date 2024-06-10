import pandas as pd
from shiny import Inputs, Outputs, Session, module, render, ui, module, reactive, req
# from shinywidgets import output_widget, render_widget, reactive_read
# from ipydatagrid import DataGrid
from faicons import icon_svg
import io

from utils import get_teaching_feeds, rename_df_cols_Fd_to_feed, pad_cols_UI_df

@module.ui
def feed_library_ui():
    return ([
        ui.navset_underline(
            ui.nav_panel(
                ui.h6('Feed Library'),
                    ui.card(
                        ui.card_header( 
                           ui.tooltip(
                                ui.span( 
                                    ui.em('Info'), 
                                    icon_svg("circle-info", margin_left='10px', height='1.2em'), 
                                    # style = 'display: inline-flex; align-items: center;'
                                    ),
                            ui.tags.li("Click on column names to arrange rows or use filters.") ,
                            ui.tags.li("Select columns to view using View Settings"),
                            ui.tags.li("Expand the table by hovering over bottom right corner and clicking button."),
                            placement = 'right',
                            class_="custom-tooltip"
                            # options={'max-width': '300px'}
                            ),
                            ui.span(
                                ui.output_ui('set_usr_session_library'),
                                style = 'display: inline-flex; align-items: center;'
                            ),
                            
                            ui.popover(
                                ui.span(
                                    ui.em('View Settings     '),
                                    icon_svg('gears'),
                                    style="position:absolute; top: 12px; right: 7px;",
                                ),
                                ui.p("Row filtering:"),
                                ui.input_checkbox('use_teaching_fd_library', 'Filter feeds for teaching', value=False),
                                ui.input_checkbox("hide_calf_feeds", "Hide calf related feeds", True),
                                ui.br(),
                                ui.p("Column Views:"),
                                ui.input_switch('cols_show_all', 'Show all columns'),
                                ui.panel_conditional( "!input.cols_show_all",
                                    ui.input_switch('cols_common', 'Show commonly used columns',  value=True),
                                    ui.input_switch("cols_amino_acids", "Amino Acids"),
                                    ui.input_switch('cols_fatty_acids', 'Fatty Acids'),
                                    ui.input_switch('cols_vitamins', 'Vitamins'),
                                    ui.input_switch('cols_minerals', 'Minerals'),
                                    ),
                            placement="left",
                            id="card_popover",
                            ),
                    ),
                        ui.output_data_frame('datagrid_feed_library'),
                        full_screen=True
                    )
                
                
            ),
            ui.nav_panel(
                ui.h6('Upload custom feed library'),
                # ui.column(4, ui.input_action_button('btn_feed_lib_upload', 'Upload custom feed library', class_='btn-primary'))
                ui.br(),
                ui.card(
                    {"style": "width:60%;margin: 0 auto"},
                    ui.markdown(
                        """
                        ### Instructions
                        Download the default library to use as a template of required columns.

                        Not all columns are available on feed tests, so it is suggested that users who want to 
                        add their own feeds should copy an existing feed and update with known values.

                        """),
                    ui.download_button('download_lib_default', 'Download default feed library', class_='btn-info', width='50%'),
                    
                    ui.input_file('user_lib_upload', ui.strong('Upload custom feed library (.csv)'), accept='.csv', width='100%'), 
                    ui.div(
                        {"class": "callout callout-warning", "role": "alert" },
                        ui.div("Note!", class_ = "callout-title"),
                        ui.markdown(
                            """
                            The feed library contains rows that use 0's and/or blank 
                            value (i.e. no value that is interpreted as NaN). 
                            Blank or missing values are interpreted differently than 0's in the model.
                            
                            *It appears that this may be a source of error in all versions of the model and further testing is required.*
                            """
                        ),
                    ),

                )
            
            ),
            ui.nav_spacer(),
        ),
     ])


@module.server
def feed_library_server(input: Inputs, output: Outputs, session: Session, feed_library_initial, user_selections_reset, session_upload_library):
    '''
    input,output,session = required Shiny arguments
    feed_library_initial = default NASEM feed library that should be parsed to module on load, as a reactive (either via session upload or default, see app.py)
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

    session_library = reactive.value(feed_library_initial)

    @render.ui
    def set_usr_session_library():
        '''If usr uploads pickle session file, replace default library with previous sessoin library. Still allows additional upload of new library.'''
        if session_upload_library() is not None and isinstance(session_upload_library(), pd.DataFrame):
            print("using library restored from .NDsession")
            session_library.set(session_upload_library())

            # Add UI message to remind that using library from restored session
            return ui.span('Library has been restored from .NDsession. A new custom library can still be uploaded.', style='color:darkred; font-style:italic; margin-left:40px')
        else:
            #not sure if this is possible
            print("restore default library")
            session_library.set(feed_library_initial)
            return ui.TagList
        
    @reactive.effect
    def _():
        print(session_library.get())

    @reactive.Calc
    def user_selected_feed_library():
        if input.use_teaching_fd_library():
            teaching_feeds =  get_teaching_feeds()

            df_user_lib = session_library.get().query('Fd_Name.isin(@teaching_feeds)')
            return df_user_lib
        
            
        if input.user_lib_upload() is None:
            
            print('No file uploaded and teaching mode not selected')
            df_user_lib = session_library.get()
        
        else:
            f = input.user_lib_upload()[0]
            
            if f['type'] == 'text/csv':
                # read in file
                df_in = pd.read_csv(f['datapath'])
                
                # Check if all column names are present
                req_cols = session_library.get().columns
                
                if not all(col_name in df_in.columns for col_name in req_cols):
                    print("Not all required columns are present in the uploaded feed library.")
                    m = ui.modal(
                        ui.p('Not all required columns are present in the uploaded feed library. Reverting to default feed library.'),
                        ui.p('Please download the default feed library to use as a template for adding new feeds.'),
                        title = 'Upload failed',
                        easy_close=True,
                    )
                    ui.modal_show(m)
                    df_user_lib = session_library.get()
                else:
                    # sort data and assign for use
                    df_user_lib = df_in.sort_values("Fd_Name")
            
            else:
                print('User upload failed - using default lib')
                df_user_lib = session_library.get()

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
    # @reactive.Calc
    # def datagrid_feed_lib():
    #     return DataGrid(df_feed_lib_userfriendly(), 
    #                         auto_fit_columns = True,
    #                         selection_mode="row",
    #                         editable = True)
    
    # @output
    # @render_widget
    # def grid_feed_library():
    #     return datagrid_feed_lib()
    
    @render.data_frame
    def datagrid_feed_library():
        df = df_feed_lib_userfriendly().copy()
        #pad column names to extend width. The \u00A0 is a non-breaking space (as spaces are being stripped by DataGrid)
        df = pad_cols_UI_df(df, 25, n_length_longer=70, cols_longer=['Feed Name'])
        return render.DataGrid(df, selection_mode="rows", editable=False, filters=True)

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
        # row_selections = reactive_read(datagrid_feed_lib(), "selections")

        # row_selections = datagrid_feed_library().input_cell_selection()["rows"] 
        # row_index = [list(range(row_number['r1'], row_number['r2']+1)) for row_number in row_selections]
        # flattened_index = [i for row in row_index for i in row]

        flattened_index = datagrid_feed_library.cell_selection()["rows"]

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
    # @reactive.event(input.reset_user_selected_feed_names, user_selections_reset)
    @reactive.event(user_selections_reset)
    def _():
        ''' Reset the user selections from DataGrid clicking events. Clears the list in UI.'''
        feed_library_index_stored.set([])


    @reactive.Calc
    def user_selected_feeds():
        df = (df_feed_lib_userfriendly()
               .reset_index(drop = True) # reset's index to match a 'row number' from selection with index (after filtering)
               .loc[feed_library_index_stored(),'Feed Name'])
        return df

    
    ################################
    # Downloads and Uploads

    @reactive.effect
    @reactive.event(input.user_lib_upload)
    async def _():
        file_uploaded = input.user_lib_upload() is not None
        if file_uploaded:
            # uncheck boxes that are about to be disabled:
            ui.update_checkbox('use_teachng_fd_library', value=False)
            ui.update_checkbox('hide_calf_feeds', value=False)
            # Disable checkboxes that are unique to built-in library
            checkbox_ids = [
                session.ns("use_teaching_fd_library"),
                session.ns("hide_calf_feeds")
            ]
            await session.send_custom_message("disableUIList", {
                "UIObjectIds": checkbox_ids
            })


    @render.download(filename='default_NASEM_library.csv')
    def download_lib_default():
        # Use io.BytesIO to yield the csv content 
        with io.StringIO() as buf:  # Use io.StringIO for string data
            df_feed_library().to_csv(buf)
            # buf.write()
            yield buf.getvalue()
    
    return(user_selected_feed_library, user_selected_feeds)