import os

def add_autotrading_indicator():
    """Add AutoTrading status indicator to the dashboard"""
    app_path = r"c:\Users\Ngum\Documents\My projects\trade\mt5-smart-flow-scalper\src\dashboard\app_new.py"
    
    # Backup the file
    backup_path = app_path + ".backup_autotrading"
    os.system(f"copy {app_path} {backup_path}")
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add autotrading status indicator in the header
    header_component = """html.Div(style={
            'backgroundColor': DARK_THEME['header'],
            'padding': '20px',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
        }, children=[
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
                html.Div(children=[
                    html.H1("Smart Flow Scalper Dashboard", style={
                        'marginBottom': '5px',
                        'color': DARK_THEME['accent']
                    }),
                    html.H3(id='symbol-title', children="GainX 800 (M5 Timeframe)", style={
                        'marginTop': '0'
                    }),
                ]),
                html.Div(style={'display': 'flex', 'alignItems': 'center'}, children=[
                    html.Div(id='autotrading-status', style={
                        'marginRight': '20px',
                        'padding': '8px 12px',
                        'borderRadius': '4px',
                        'fontWeight': 'bold',
                        'backgroundColor': 'rgba(255, 23, 68, 0.7)',  # Default to red/disabled
                        'color': 'white',
                        'display': 'flex',
                        'alignItems': 'center',
                    }, children=[
                        html.Span("AutoTrading: ", style={'marginRight': '5px'}),
                        html.Span("Checking...")
                    ]),
                    html.Div(style={'minWidth': '220px'}, children=[
                        html.Label("Select Symbol", style={'display': 'block', 'marginBottom': '5px', 'color': '#999'}),
                        dcc.Dropdown(
                            id='symbol-dropdown',
                            options=[{'label': symbol, 'value': symbol} for symbol in AVAILABLE_SYMBOLS],
                            value='GainX 800',
                            style={
                                'backgroundColor': DARK_THEME['panel'],
                                'color': 'white',
                                'border': f'1px solid {DARK_THEME["grid"]}',
                            }
                        ),
                    ]),
                ]),
            ])"""
    
    # Find and replace the header component
    if "html.Div(style={'backgroundColor': DARK_THEME['header']," in content:
        start = content.find("html.Div(style={'backgroundColor': DARK_THEME['header'],")
        end = content.find("])],", start) + 3
        content = content[:start] + header_component + content[end:]
    
    # Add autotrading status callback
    autotrading_callback = """
    # Check AutoTrading status
    @app.callback(
        [Output('autotrading-status', 'children'),
         Output('autotrading-status', 'style')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_autotrading_status(n):
        if not mt5.initialize():
            return [
                [html.Span("MT5: ", style={'marginRight': '5px'}), 
                 html.Span("Disconnected")],
                {'backgroundColor': 'rgba(255, 23, 68, 0.7)', 'color': 'white', 'padding': '8px 12px',
                 'borderRadius': '4px', 'fontWeight': 'bold', 'display': 'flex', 'alignItems': 'center'}
            ]
        
        trade_allowed = mt5.terminal_info().trade_allowed
        
        if trade_allowed:
            return [
                [html.Span("AutoTrading: ", style={'marginRight': '5px'}), 
                 html.Span("Enabled")],
                {'backgroundColor': 'rgba(0, 200, 83, 0.7)', 'color': 'white', 'padding': '8px 12px',
                 'borderRadius': '4px', 'fontWeight': 'bold', 'display': 'flex', 'alignItems': 'center'}
            ]
        else:
            return [
                [html.Span("AutoTrading: ", style={'marginRight': '5px'}), 
                 html.Span("DISABLED")],
                {'backgroundColor': 'rgba(255, 23, 68, 0.7)', 'color': 'white', 'padding': '8px 12px',
                 'borderRadius': '4px', 'fontWeight': 'bold', 'display': 'flex', 'alignItems': 'center'}
            ]
    """
    
    # Add the callback before the return app statement
    if "return app" in content:
        insert_pos = content.rfind("return app")
        content = content[:insert_pos] + autotrading_callback + "\n    " + content[insert_pos:]
    
    # Write the modified content back
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Added AutoTrading indicator to dashboard in {app_path}")
    print(f"Original file backed up to {backup_path}")

if __name__ == "__main__":
    add_autotrading_indicator()