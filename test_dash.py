import dash
from dash import html

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dash Test - If you see this, Dash is working!")
])

if __name__ == "__main__":
    print("Starting Dash test server at http://127.0.0.1:8050")
    print("(If browser doesn't open, copy this URL manually)")
    # Use app.run instead of app.run_server for newer Dash versions
    app.run(debug=True, port=8050)