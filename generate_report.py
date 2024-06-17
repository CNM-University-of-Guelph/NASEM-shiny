
import re
# import IPython.display
import pandas as pd
import datetime
import pytz

# df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
# df2 = pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})


# markdown_table1 = df1.to_markdown()
# markdown_table2 = df2.to_markdown()

def generate_report(
    # Model Evaluation
    df_milk: pd.DataFrame,
    df_allowable_milk: pd.DataFrame,
    df_ME: pd.DataFrame,
    df_MP: pd.DataFrame,
    # Diet Analysis
    df_diet_summary: pd.DataFrame,
    df_NEL: pd.DataFrame,
    df_DCAD: pd.DataFrame,
    df_ration_ingredients: pd.DataFrame,
    df_energy_teaching: pd.DataFrame,
    df_full_model: pd.DataFrame,
    # df_animal_input_comparison: pd.DataFrame,
    dict_equation_selections: dict,
    df_snapshot: pd.DataFrame
    ):

    '''
    Generates a markdown report and converts to html.

    An object with the html stored as a string is returned, to be written to file later.
    '''
    # Get the current date and time
    current_datetime = datetime.datetime.utcnow()
    UTC_tz = pytz.timezone('UTC')
    current_time_UTC = UTC_tz.localize(current_datetime)

    eastern_tz = pytz.timezone('US/Eastern')
    current_datetime_eastern = current_time_UTC.astimezone(eastern_tz)
    current_datetime_str = current_datetime_eastern.strftime('%Y-%m-%d %H:%M:%S')


    df_equation_selections = pd.DataFrame(dict_equation_selections.items(), columns=['Variable Name', 'Value'])


    # Create or generate HTML content for each DataFrame
    html_milk = df_milk.to_html()
    html_allowable_milk = df_allowable_milk.to_html()
    html_ME = df_ME.to_html()
    html_MP = df_MP.to_html()
    html_diet_summary = df_diet_summary.to_html()
    html_NEL = df_NEL.to_html()
    html_DCAD = df_DCAD.to_html()
    html_ration_ingredients = df_ration_ingredients.to_html()
    html_energy_teaching = df_energy_teaching.to_html()
    html_full_model = df_full_model.to_html()
    # html_user_input_compare = df_animal_input_comparison.to_html()
    html_user_input_compare = pd.DataFrame().to_html()
    html_equation_selections = df_equation_selections.to_html()
    html_snapshot = df_snapshot.to_html()

    

    html = f"""
        <html>

        <head>
            <title>My Report</title>
            <!-- Include Bootstrap CSS -->
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
            <style>
                table.custom-table {{
                        width: auto;
                        padding: 10px;

                        margin: 0 auto;
                        /* Center the table on the page */
                    }}
            </style>
        </head>

        <body>
            <!-- Hidden record of date and time -->
            <input type="hidden" id="current-datetime" value="{current_datetime_eastern}">
            <div class="container">
                <h1> NASEM 2021 - Report </h1>
                <h2 class="bg-info text-white">Model Evaluation</h2>

                <h3>Model Snapshot</h3>
                <div class="table-responsive">
                    {html_snapshot}
                </div>

                <h3>Milk DataFrame</h3>
                <div class="table-responsive">
                    {html_milk}
                </div>

                <h3>Allowable Milk DataFrame</h3>
                <div class="table-responsive">
                    {html_allowable_milk}
                </div>

                <h3>ME DataFrame</h3>
                <div class="table-responsive">
                    {html_ME}
                </div>

                <h3>MP DataFrame</h3>
                <div class="table-responsive">
                    {html_MP}
                </div>
                <br>
                <br>

                <h2 class="bg-info text-white">Diet Analysis</h2>

                <h3>Diet Summary DataFrame</h3>
                <div class="table-responsive">
                    {html_diet_summary}
                </div>
                <br>

                <h3>NEL DataFrame</h3>
                <div class="table-responsive">
                    {html_NEL}
                </div>
                <br>

                <h3>DCAD DataFrame</h3>
                <div class="table-responsive">
                    {html_DCAD}
                </div>
                <br>

                <h3>Ration Ingredients DataFrame</h3>
                <div class="table-responsive">
                    {html_ration_ingredients}
                </div>

                <br>
                <br>
                <h2 class="bg-info text-white">Energy Teaching</h2>
                <div class="table-responsive">
                    {html_energy_teaching}
                </div>
                <br>
                <br>
                


                <div>
                    <br>
                    <p>Report generated on: {current_datetime_str}</p>
                </div>

            </div>
            <div class="container">
                <!-- Collapsible container with arrow -->
                <div class="accordion" id="collapsible-container">
                    <div class="card">
                        <div class="card-header" id="headingOne">
                            <h2 class="mb-0">
                                <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapseOne"
                                    aria-expanded="true" aria-controls="collapseOne">
                                    <span>&#x25BC;</span> Advanced
                                </button>
                            </h2>
                        </div>

                        <div id="collapseOne" class="collapse show" aria-labelledby="headingOne"
                            data-parent="#collapsible-container">

                            <h2 class="bg-info text-white">Advanced</h2>

                            <h3>All Model Predictions</h3>
                            <div class="table-responsive">
                                {html_full_model}
                            </div>
                            <br>
                            <br>
                            
                            <h2 class="bg-info text-white">User Inputs</h2>
                            <h3>User Inputs</h3>
                            <div class="table-responsive">
                                {html_user_input_compare}
                            </div>

                            <h3>Equation selections</h3>
                            <div class="table-responsive">
                                {html_equation_selections }
                            </div>

                        </div>
                    </div>

                    <!-- Repeat the above structure for other sections -->
                </div>
            </div>

            <!-- Include Bootstrap JS for collapsible functionality -->
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
            <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        </body>

        </html>
        """


    # Define the regex pattern for finding <table> elements
    pattern = r'<table\b[^>]*>'

    # Replace <table> elements 
    html_with_classes = re.sub(pattern, '<table class="table table-striped custom-table">', html)

    

    html_out = html_with_classes
    return html_out
