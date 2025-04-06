import os

def fix_dashboard_outputs():
    """Fix the dashboard output mismatch"""
    app_path = r"c:\Users\Ngum\Documents\My projects\trade\mt5-smart-flow-scalper\src\dashboard\app_new.py"
    
    # Backup the file
    backup_path = app_path + ".backup_outputs"
    os.system(f"copy {app_path} {backup_path}")
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Ensure the callback outputs match what's returned
    callback_outputs = """    [Output('price-chart', 'figure'),
     Output('current-price', 'children'),
     Output('price-change', 'children'),
     Output('price-change', 'style'),
     Output('live-price', 'children'),
     Output('ema-20-value', 'children'),
     Output('ema-50-value', 'children'),
     Output('rsi-value', 'children'),
     Output('macd-value', 'children'),
     Output('latest-signals', 'children'),
     Output('trade-history', 'children'),
     Output('update-status', 'children'),
     Output('update-status', 'style'),
     Output('signal-panel', 'children')]"""
    
    # Fix 2: Ensure the return values match the outputs
    empty_return = """    return (empty_fig, price_display, price_change_text, price_change_style, live_price,
            ema_20_value, ema_50_value, rsi_value, macd_value, latest_signals, 
            trade_history_display, update_status, update_status_style, signal_panel)"""
    
    normal_return = """    return (fig, current_price, price_change_text, price_change_style, live_price,
            ema_20_value, ema_50_value, rsi_value, macd_value, 
            html.Div(latest_signals_components), trade_history_display, 
            update_status, update_status_style, signal_panel)"""
    
    # Fix 3: Enhanced color theme with more vibrant buy/sell colors
    new_theme = """# Theme colors
DARK_THEME = {
    'background': '#1E1E1E',
    'text': '#FFFFFF',
    'grid': '#333333',
    'buy': '#00C853',   # Brighter green for buy signals
    'sell': '#FF1744',  # Brighter red for sell signals
    'panel': '#2A2A2A',
    'header': '#303030',
    'accent': '#00B7FF'
}"""
    
    # Fix 4: Enhanced signal display with more prominent colors
    enhanced_buy_signal = """html.Div([
                    html.Div("BUY SIGNAL", style={
                        'backgroundColor': DARK_THEME['buy'],
                        'color': 'white',
                        'padding': '10px 20px',
                        'borderRadius': '4px',
                        'fontWeight': 'bold',
                        'display': 'inline-block',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.3)',
                        'border': '2px solid #00FF7F'
                    }),
                    html.Div(f"at {buy_time} (${buy_price:,.2f})", style={
                        'marginTop': '8px',
                        'marginBottom': '12px',
                        'fontSize': '16px',
                        'fontWeight': 'bold'
                    })
                ])"""
                
    enhanced_sell_signal = """html.Div([
                    html.Div("SELL SIGNAL", style={
                        'backgroundColor': DARK_THEME['sell'],
                        'color': 'white',
                        'padding': '10px 20px',
                        'borderRadius': '4px',
                        'fontWeight': 'bold',
                        'display': 'inline-block',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.3)',
                        'border': '2px solid #FF4500'
                    }),
                    html.Div(f"at {sell_time} (${sell_price:,.2f})", style={
                        'marginTop': '8px',
                        'marginBottom': '12px',
                        'fontSize': '16px',
                        'fontWeight': 'bold'
                    })
                ])"""
    
    # Replace the callback output definition
    if "[Output('price-chart', 'figure')," in content:
        start = content.find("[Output('price-chart', 'figure'),")
        end = content.find("],", start)
        if start > 0 and end > 0:
            content = content[:start] + callback_outputs + content[end:]
    
    # Replace the return statements
    if "return (empty_fig," in content:
        start = content.find("return (empty_fig,")
        end = content.find(")", start) + 1
        if start > 0 and end > 0:
            content = content[:start] + empty_return + content[end:]
    
    if "return (fig," in content:
        start = content.find("return (fig,")
        end = content.find(")", start) + 1
        if start > 0 and end > 0:
            content = content[:start] + normal_return + content[end:]
    
    # Replace the theme colors
    if "DARK_THEME = {" in content:
        start = content.find("DARK_THEME = {")
        end = content.find("}", start) + 1
        if start > 0 and end > 0:
            content = content[:start] + new_theme + content[end:]
    
    # Replace the buy signal component
    if "html.Div(\"BUY SIGNAL\", style={" in content:
        start = content.find("html.Div([")
        end = content.find("])", start) + 2
        if start > 0 and end > 0:
            content = content[:start] + enhanced_buy_signal + content[end:]
    
    # Replace the sell signal component 
    if "html.Div(\"SELL SIGNAL\", style={" in content:
        start = content.find("html.Div([")
        end = content.find("])", start) + 2
        if start > 0 and end > 0:
            content = content[:start] + enhanced_sell_signal + content[end:]
    
    # Write the fixed content back
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed dashboard outputs in {app_path}")
    print(f"Original file backed up to {backup_path}")
    
    # Bonus: Create CSS file with animation effects
    css_dir = os.path.dirname(app_path) + "/assets"
    os.makedirs(css_dir, exist_ok=True)
    
    css_content = """
    /* Signal animations */
    @keyframes pulse-buy {
        0% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 200, 83, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0); }
    }
    
    @keyframes pulse-sell {
        0% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 23, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0); }
    }
    
    /* Add animation classes to dashboard */
    .buy-signal {
        animation: pulse-buy 2s infinite;
    }
    
    .sell-signal {
        animation: pulse-sell 2s infinite;
    }
    
    /* Improve chart visibility */
    .js-plotly-plot .plotly .modebar {
        background-color: rgba(42, 42, 42, 0.7) !important;
    }
    
    /* Improve price display */
    .price-up {
        color: #00C853;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .price-down {
        color: #FF1744;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    """
    
    with open(f"{css_dir}/style.css", 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print(f"Created CSS file with enhanced styles at {css_dir}/style.css")

def enhance_signals():
    """Add more visual enhancements to signals"""
    app_path = r"c:\Users\Ngum\Documents\My projects\trade\mt5-smart-flow-scalper\src\dashboard\app_new.py"
    
    # Additional visual enhancements for candlestick chart
    chart_enhancements = """
    # Make buy/sell markers more visible
    fig.add_trace(go.Scatter(
        x=buy_signals['time'],
        y=buy_signals['low'] - (buy_signals['high'] - buy_signals['low']) * 0.2,
        mode='markers',
        marker=dict(symbol='triangle-up', size=15, color=DARK_THEME['buy'], line=dict(width=2, color='white')),
        name='Buy Signal'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=sell_signals['time'],
        y=sell_signals['high'] + (sell_signals['high'] - sell_signals['low']) * 0.2,
        mode='markers',
        marker=dict(symbol='triangle-down', size=15, color=DARK_THEME['sell'], line=dict(width=2, color='white')),
        name='Sell Signal'
    ), row=1, col=1)
    """
    
    # Add better price highlighting
    price_highlighting = """
    # Add dynamic price class based on change
    if len(signals) >= 2:
        price_change_abs = latest['close'] - signals.iloc[-2]['close']
        price_change_pct = price_change_abs / signals.iloc[-2]['close'] * 100
        price_change_text = f"Change: {price_change_abs:+,.2f} ({price_change_pct:+,.2f}%)"
        price_class = 'price-up' if price_change_abs >= 0 else 'price-down'
        
        price_change_style = {
            'color': DARK_THEME['buy'] if price_change_abs >= 0 else DARK_THEME['sell'],
            'fontSize': '16px',
            'fontWeight': 'bold',
            'marginBottom': '15px',
            'padding': '5px 10px',
            'borderRadius': '4px',
            'backgroundColor': f"rgba({'0,200,83' if price_change_abs >= 0 else '255,23,68'}, 0.1)",
            'display': 'inline-block'
        }
        
        # Make live price more prominent
        live_price = html.Span(f"${latest['close']:,.2f}", className=price_class)
    else:
        price_change_text = "Change: N/A"
        price_change_style = {'color': '#999', 'fontSize': '14px', 'marginBottom': '15px'}
        live_price = f"${latest['close']:,.2f}"
    """

    # This function will be implemented if needed
    pass

if __name__ == "__main__":
    fix_dashboard_outputs()