from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

def create_dashboard():
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("Smart Flow Scalper Dashboard"), className="text-center")
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='price-chart'), width=12)
            ]),
            dbc.Row([
                dbc.Col(html.Div(id='buy-signal', className='alert alert-success'), width=6),
                dbc.Col(html.Div(id='sell-signal', className='alert alert-danger'), width=6)
            ]),
            dbc.Row([
                dbc.Col(dcc.Interval(id='update-interval', interval=1000, n_intervals=0), width=12)
            ])
        ])
    ])

    return app

if __name__ == "__main__":
    app = create_dashboard()
    app.run_server(debug=True)