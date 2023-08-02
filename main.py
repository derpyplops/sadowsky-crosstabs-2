import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from reportlab.platypus import Paragraph
from reportlab.platypus import PageBreak


df = pd.read_csv('/Users/jon/projects/sadowsky/toplines/output_df_test.csv')

def generate_crosstabs_v5(df):
    # Identify the variables that have 'Strongly agree' as one of the responses
    agree_variables = df[df['value_name'] == 'Strongly agree']['variable_name'].unique()
    
    # Filter the dataframe for rows with these variables
    variable_df = df[df['variable_name'].isin(agree_variables)]
    
    # Create an empty dictionary to store the crosstabs
    crosstabs = {}
    
    # Iterate over the unique 'variable_name' values in the filtered dataframe
    for variable in variable_df['variable_name'].unique():
        # Filter the dataframe for rows with the current 'variable_name'
        var_df = variable_df[variable_df['variable_name'] == variable]
        
        # Create an empty dataframe to store the combined crosstab for this variable
        combined_crosstab = pd.DataFrame()
        
        # Iterate over the desired 'xtab_col' values, including 'all' first
        for xtab in ['all', 'AGE', 'GENDER', 'party']:
            # Filter the dataframe for rows with the current 'xtab_col'
            xtab_df = var_df[var_df['xtab_col'] == xtab]
            
            # If the filtered dataframe is not empty, create a crosstab
            if not xtab_df.empty:
                crosstab = pd.crosstab([xtab_df['variable_name'], xtab_df['value_name']], 
                                       xtab_df['xtab_val'], 
                                       xtab_df['weighted_mean'], 
                                       aggfunc='sum').reset_index().set_index(['variable_name', 'value_name'])
                
                # Multiply all values by 100 and round to the nearest whole number
                crosstab = (crosstab * 100).round(0)
                
                # If the combined crosstab is not empty, merge the new crosstab with it
                if not combined_crosstab.empty:
                    combined_crosstab = pd.merge(combined_crosstab, crosstab, on=['variable_name', 'value_name'], how='outer')
                # If the combined crosstab is empty, replace it with the new crosstab
                else:
                    combined_crosstab = crosstab
        
        # Add the combined crosstab to the dictionary
        crosstabs[variable] = combined_crosstab
    
    return crosstabs

# Generate the crosstabs
crosstabs_v5 = generate_crosstabs_v5(df)

# Print the first table to check the results
crosstabs_v5[list(crosstabs_v5.keys())[0]]

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus.tables import TableStyle

# Create a PDF document
doc = SimpleDocTemplate("crosstabs_report.pdf", pagesize=landscape(letter))

# Get a sample style sheet
styles = getSampleStyleSheet()

# Initialize a list that will store the elements
elements = []

# Create a table style
table_style = TableStyle([
    ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
])

# Iterate over the variables and crosstabs
tables_written = 0
for variable, crosstab in crosstabs_v5.items():

    # Add a title with the variable name
    title = Paragraph('<font size=12><b>{}</b></font>'.format(variable), styles['Normal'])
    elements.append(title)

    # Add a spacer
    elements.append(Spacer(1, 30))

    # Convert the crosstab to a list of lists, removing the first column
    data = [[""] + crosstab.columns.tolist()] + [[row[1]] + [int(x) if not pd.isna(x) else 0 for x in row[2:]] for row in crosstab.reset_index().values.tolist()]

    # Create a table with the data
    table = Table(data)

    # Add the style to the table
    table.setStyle(table_style)
    
    # Add the table to the elements
    elements.append(table)

    # Add a spacer at the bottom of the table
    elements.append(Spacer(1, 30))

    tables_written += 1

    if tables_written == 2:
        tables_written = 0
        elements.append(PageBreak())

# Build the PDF
doc.build(elements)
