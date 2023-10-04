import markdown2
import re
# import IPython.display
import pandas as pd

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
    df_ration_ingredients: pd.DataFrame):

    '''
    Generates a markdown report and converts to html.

    An object with the html stored as a string is returned, to be written to file later.
    '''
    
    # Create or generate HTML content for each DataFrame
    html_milk = df_milk.to_html()
    html_allowable_milk = df_allowable_milk.to_html()
    html_ME = df_ME.to_html()
    html_MP = df_MP.to_html()
    html_diet_summary = df_diet_summary.to_html()
    html_NEL = df_NEL.to_html()
    html_DCAD = df_DCAD.to_html()
    html_ration_ingredients = df_ration_ingredients.to_html()

    # Create the HTML report with headings
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>My HTML Report</title>
    </head>
    <body>
        <h1>Model Evaluation</h1>

        <h2>Milk DataFrame</h2>
        {html_milk}

        <h2>Allowable Milk DataFrame</h2>
        {html_allowable_milk}

        <h2>ME DataFrame</h2>
        {html_ME}

        <h2>MP DataFrame</h2>
        {html_MP}

        <h1>Diet Analysis</h1>

        <h2>Diet Summary DataFrame</h2>
        {html_diet_summary}

        <h2>NEL DataFrame</h2>
        {html_NEL}

        <h2>DCAD DataFrame</h2>
        {html_DCAD}

        <h2>Ration Ingredients DataFrame</h2>
        {html_ration_ingredients}
    </body>
    </html>
    """

    # # Convert DataFrames to Markdown tables
    # markdown_milk = pd.DataFrame(df_milk).to_html()
    # markdown_allowable_milk = df_allowable_milk.to_markdown()
    # markdown_ME = df_ME.to_markdown()
    # markdown_MP = df_MP.to_markdown()
    # markdown_diet_summary = df_diet_summary.to_markdown()
    # markdown_NEL = df_NEL.to_markdown()
    # markdown_DCAD = df_DCAD.to_markdown()
    # markdown_ration_ingredients = df_ration_ingredients.to_markdown()


    # # Define your Markdown template
    # markdown_template = f"""
    # # NASEM 2021 Shiny App Report

    # # Model Evaluation

    # ## Milk DataFrame
    # {markdown_milk}

    # ## Allowable Milk DataFrame
    # {markdown_allowable_milk}

    # ## ME DataFrame
    # {markdown_ME}

    # ## MP DataFrame
    # {markdown_MP}

    # # Diet Analysis

    # ## Diet Summary DataFrame
    # {markdown_diet_summary}

    # ## NEL DataFrame
    # {markdown_NEL}

    # ## DCAD DataFrame
    # {markdown_DCAD}

    # ## Ration Ingredients DataFrame
    # {markdown_ration_ingredients}
    # """

    # print(markdown_template)
    # print(type(markdown_template))

    # converter = markdown2.Markdown(extras=["tables"])  
    # html_out = converter.convert(markdown_template)

    # print(html_out)
    # html = converter.convert(markdown_template)

    html_head = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>My Report</title>
    <!-- Include Bootstrap CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        table.custom-table {
        width: auto;
        padding: 10px;
        
        margin: 0 auto; /* Center the table on the page */
        }
    </style>  
    </head>
    """ 

    
    # Define the regex pattern for finding <table> elements
    pattern = r'<table\b[^>]*>'

    # Replace <table> elements 
    html_with_classes = re.sub(pattern, '<table class="table table-striped custom-table">', html)


    html_out = html_head + html_with_classes

    # view in interactive window:
    # display(IPython.display.HTML(html_out))

    # save HTML file
    # with open('sample.html', 'w') as f:
    #     f.write(html_out)


    return html_out
