from shiny import App, reactive, render, ui

from NASEM_functions import *
from ration_balancer import *

# get list of feeds available from the feed library in db
# used for user selection in shiny
unique_fd_list = fl_get_feeds_from_db('diet_database.db')

app_ui = ui.page_fluid(
    ui.h2("Diet Selection"),
 
    ui.input_selectize(
        "feeds_to_use",
        "Choose feeds to use in ration:",
        unique_fd_list,
        multiple = True
        ),
    ui.output_text_verbatim('selected_feed_to_use')
)


def server(input, output, session):
    @output
    @render.text
    def selected_feed_to_use():
        return f"{input.feeds_to_use()}"
    



app = App(app_ui, server)
