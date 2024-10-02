import re
import pandas as pd
import datetime

import nasem_dairy as nd

def generate_summary_report(
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
    df_animal_input_comparison: pd.DataFrame,
    dict_equation_selections: dict,
    df_snapshot: pd.DataFrame
    ):

    '''
    Generates a markdown report and converts to HTML.

    The HTML is returned as a string, ready to be written to a file or displayed.
    '''
    # Get the current UTC date and time
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')

    # Convert the dictionary of equation selections to a DataFrame
    df_equation_selections = pd.DataFrame(dict_equation_selections.items(), columns=['Variable Name', 'Value'])

    # Convert each DataFrame to HTML
    html_milk = df_milk.to_html()
    html_allowable_milk = df_allowable_milk.to_html()
    html_ME = df_ME.to_html()
    html_MP = df_MP.to_html()
    html_diet_summary = df_diet_summary.to_html()
    html_NEL = df_NEL.to_html()
    html_DCAD = df_DCAD.to_html()
    html_ration_ingredients = df_ration_ingredients.to_html()
    html_energy_teaching = df_energy_teaching.to_html()
    html_user_input_compare = df_animal_input_comparison.to_html()
    html_equation_selections = df_equation_selections.to_html()
    html_snapshot = df_snapshot.to_html()

    # HTML structure with client-side timezone detection and filler intro
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
                }}
            </style>
            <script>
                // Function to display the current time in the user's local timezone
                function displayUserTime() {{
                    var now = new Date();
                    var options = {{ timeZoneName: 'short' }};
                    var userTime = now.toLocaleString(undefined, options);
                    document.getElementById('user-time').innerText = userTime;
                }}
            </script>
        </head>
        <body onload="displayUserTime()">
            <!-- Date and time display -->
            <div class="container">
                <h1>NASEM 2021 - Report</h1>
                <p><strong>Report generated on (UTC):</strong> {current_datetime_str}</p>
                <p><strong>Report generated on (your timezone):</strong> <span id="user-time"></span></p>
                <br>
                <!-- Introductory paragraph -->
                <p>
                    <strong>Introduction:</strong> This report provides a summary of key NASEM 2021 model outputs
                    based on the user selected inputs and diet. See the Full Report for tables generated to match the
                    output from the windows version of the NASEM Dairy-8 software distributed with the book.
                    <br>
                    It also includes a record of some of the user input values at the bottom.
                </p>

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
                <br><br>

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
                <br><br>

                <h2 class="bg-info text-white">Energy Teaching</h2>
                <div class="table-responsive">
                    {html_energy_teaching}
                </div>
                <br><br>

                <h2 class="bg-info text-white">User Inputs</h2>
                <div class="table-responsive">
                    {html_user_input_compare}
                </div>
                <br>

                <h3>Equation Selections</h3>
                <div class="table-responsive">
                    {html_equation_selections}
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

    # Replace <table> elements with custom classes
    html_with_classes = re.sub(pattern, '<table class="table table-striped custom-table">', html)

    return html_with_classes





def generate_full_report(ModelOutput: nd.ModelOutput, table_names):
    '''
    Generates a full report by fetching each table, converting to HTML, and compiling them into a single HTML document.
    
    :param ModelOutput: The model output object from nasem_dairy that provides the get_report method.
    :param table_names: List of table names to generate the report for.
    :return: The compiled HTML string.
    '''
    
    # Get the UTC time for the report generation
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')

    # Start HTML compilation
    html = f"""
    <html>
    <head>
        <title>Full NASEM Report</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            table.custom-table {{
                width: auto;
                padding: 10px;
                margin: 0 auto;
            }}
        </style>
        <script>
            function expandAll() {{
                var accordions = document.getElementsByClassName('collapse');
                for (var i = 0; i < accordions.length; i++) {{
                    accordions[i].classList.add('show');
                }}
            }}
            function collapseAll() {{
                var accordions = document.getElementsByClassName('collapse');
                for (var i = 0; i < accordions.length; i++) {{
                    accordions[i].classList.remove('show');
                }}
            }}
            // Function to display the current time in the user's local timezone
            function displayUserTime() {{
                var now = new Date();
                var options = {{ timeZoneName: 'short' }};
                var userTime = now.toLocaleString(undefined, options);
                document.getElementById('user-time').innerText = userTime;
            }}
        </script>
    </head>
    <body onload="displayUserTime()">
        <div class="container">
            <h1>NASEM 2021 - Full Report</h1>
            <p>Report generated on (UTC): {current_datetime_str}</p>
            <p>Report generated on (your timezone): <span id="user-time"></span></p>

            <!-- Introductory paragraph -->
            <p>
                <strong>Introduction:</strong> This report provides NASEM 2021 model outputs
                based on the user selected inputs and diet that are formatted to match the tables generated in the
                output from the windows version of the NASEM Dairy-8 software distributed with the book.
            </p>

            <!-- Expand/Collapse Buttons -->
            <button class="btn btn-primary" onclick="expandAll()">Expand All</button>
            <button class="btn btn-secondary" onclick="collapseAll()">Collapse All</button>

            <br><br>

            <div class="accordion" id="report-accordion">
    """

    def sentence_case(text):
        """Converts a string like 'table1_1' to 'Table 1.1'."""
        # Replace underscores with spaces
        text_with_spaces = text.replace("_", " ")
        
        # Find numeric patterns and replace them with a dot separator (1_1 -> 1.1)
        text_with_dots = re.sub(r'(\d+) (\d+)', r'\1.\2', text_with_spaces)
        
        # Capitalize the first word and return the formatted string
        return text_with_dots.capitalize()


    # Loop through the table names and generate HTML for each one
    for i, table_name in enumerate(table_names, start=1):
        try:
            # Fetch the DataFrame using the get_report method from the ModelOutput object
            df = ModelOutput.get_report(table_name)
            # Convert DataFrame to HTML
            html_table = df.to_html(classes="table table-striped custom-table")
            
            formatted_table_name = sentence_case(table_name)

            # Add this table to the report
            html += f"""
            <div class="card">
                <div class="card-header" id="heading{i}">
                    <h2 class="mb-0">
                        <button class="btn btn-link" type="button" data-toggle="collapse" 
                                data-target="#collapse{i}" aria-expanded="true" aria-controls="collapse{i}">
                            <span>&#x25BC;</span> {table_name}
                        </button>
                    </h2>
                </div>
                <div id="collapse{i}" class="collapse" aria-labelledby="heading{i}" data-parent="#report-accordion">
                    <div class="card-body">
                        <h3>{formatted_table_name}</h3>
                        <div class="table-responsive">
                            {html_table}
                        </div>
                    </div>
                </div>
            </div>
            """
        except Exception as e:
            # If an error occurs (e.g., table not found), display an error message
            html += f"""
            <div class="alert alert-danger" role="alert">
                Error loading table {table_name}: {str(e)}
            </div>
            """

    # Close the accordion and HTML document
    html += """
            </div> <!-- End of accordion -->
        </div> <!-- End of container -->
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    """

    # Define the regex pattern for finding <table> elements
    pattern = r'<table\b[^>]*>'

    # Replace <table> elements with custom classes
    html_with_classes = re.sub(pattern, '<table class="table table-striped custom-table">', html)

    return html_with_classes
