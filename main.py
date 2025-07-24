import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category10

app = FastAPI()

# Load the excel file once at startup
EXCEL_FILE = '1120_OSC_2MHz.xlsx'
SHEET_NAME = 'Statistics'

df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
# Ensure numeric columns are numeric
for col in ['VDD, V', 'VDD_TRIM, V'] + [str(i) for i in range(1, 51)]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    # Simple form for parameter selection
    html = """
    <html>
    <head><title>OSC statistics</title></head>
    <body>
    <h1>Select Range</h1>
    <form action='/plot' method='get'>
      Min VDD: <input type='number' step='0.1' name='vdd_min' value='5.0'><br>
      Max VDD: <input type='number' step='0.1' name='vdd_max' value='5.5'><br>
      VDD_TRIM: <input type='number' step='0.1' name='vdd_trim' value='5.5'><br>
      <input type='submit' value='Plot'>
    </form>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get('/plot', response_class=HTMLResponse)
def plot(vdd_min: float, vdd_max: float, vdd_trim: float):
    mask = (
        (df['VDD, V'] >= vdd_min) &
        (df['VDD, V'] <= vdd_max) &
        (df['VDD_TRIM, V'] == vdd_trim)
    )
    subset = df.loc[mask]

    if subset.empty:
        return HTMLResponse('<h2>No data for selected parameters</h2>')

    p = figure(title='Measurement vs Chip', x_axis_label='Chip', y_axis_label='Value')

    palette = Category10[10]
    color_index = 0
    for _, row in subset.iterrows():
        x = []
        y = []
        for i in range(1, 51):
            val = row.get(str(i))
            if pd.notna(val):
                x.append(i)
                y.append(val)
        if not y:
            continue
        color = palette[color_index % len(palette)]
        color_index += 1
        label = str(row['FULL_TEST_TXT'])
        p.line(x, y, legend_label=label, color=color)

    p.legend.location = 'top_left'
    script, div = components(p)

    html = f"""
    <html>
    <head>
        <title>Plot</title>
        <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-3.7.3.min.css" type="text/css" />
        <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.7.3.min.js"></script>
    </head>
    <body>
    {div}
    {script}
    <br><a href='/'>Back</a>
    </body>
    </html>
    """
    return HTMLResponse(html)
