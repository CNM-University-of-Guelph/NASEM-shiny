from shiny import App, reactive, render, ui

app_ui = ui.page_fluid(
    ui.panel_title("Percentage Calculator"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.output_ui("item_input"),
            ui.input_action_button("add_button", "Add another item"),
        ),
        ui.panel_main(
            ui.output_text_verbatim("user_selections_items"),
            ui.output_text_verbatim("user_selections_perc"),
        ),
    ),
)

def server(input, output, session):
    # Initialize reactive values to store user selections
    user_feeds = reactive.Value(['item_1'])
    user_percentages = reactive.Value(['perc_1'])

    def update_user_inputs(reac_list, current):
        xout = reac_list().copy()
        xout.append(current)
        reac_list.set(xout)

    # Generate a new item input whenever the "Add another item" button is clicked
    @reactive.Effect
    @reactive.event(input.add_button)
    def _():
        current_iter =  str(len(user_feeds) + 1)

        #add to list of items and percentages, to keep track of inputs
        update_user_inputs(user_feeds(), current = 'item_' + current_iter)
        update_user_inputs(user_percentages(), current = 'perc_' + current_iter)

        newItemDiv = ui.div(
            {"id" : "userfeed_" + current_iter}, # div ID
            ui.input_select('item_' + current_iter, 
                            label="Select an item:", 
                            choices=["Item A", "Item B", "Item C"]),
            ui.input_numeric('perc_' + current_iter, 
                             label="Enter percentage:", 
                             min=0, max=100, value=0),
        )
        ui.insert_ui(newItemDiv, selector = "#item_input", where = "beforeEnd")

    @output
    @render.ui
    def item_input():
        # Generate initial item input
        itemInput = ui.div(
            {"id" : "userfeed_1" },
            ui.input_select("item_1", label="Select an item:", choices=["Item A", "Item B", "Item C"]),
            ui.input_numeric("percentage_1", label="Enter percentage:", min=0, max=100, value=0),
        )
        return itemInput

    # @reactive.Calc
    # def get_input_values():
    #     # Get items from input by name
    #     items = [input.x.get() for x in user_feeds()]
    #     percentages = [input.x.get() for x in user_percentages()]

    #     return 

       
    @output
    @render.text
    def user_selections_items():
        items = [input.x.get() for x in user_feeds()]
        return {items}
    
    @output
    @render.text
    def user_selections_percentages():
        percentages = [input.x.get() for x in user_percentages()]
        # Create a data frame from the reactive values and display it as a table
        return percentages

app = App(app_ui, server)
