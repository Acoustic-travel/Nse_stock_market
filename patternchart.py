from flask import Flask, render_template, request
import pandas as pd
from datetime import timedelta
import plotly.graph_objs as go
import plotly.io as pio
import os

DATA_PATH = "D:\\CODING\\_Out"  # Update this path if needed

app = Flask(__name__)

# Function to load CSV data for a given symbol and timeframe
def load_csv(symbol='ABB', timeframe='D'):
    try:
        path = os.path.join(DATA_PATH, timeframe, f"{symbol}_{timeframe}.csv")
        data = pd.read_csv(path, parse_dates=['Date'], dayfirst=True)
        return data
    except FileNotFoundError:
        return pd.DataFrame()  # Return an empty DataFrame if the file doesn't exist

@app.route('/', methods=['GET', 'POST'])
def home():
    symbol_name = request.args.get('SName', 'ABB')
    selected_date = request.form.get('selected_date')
    candlestick_chart_html = None
    error_message = None

    # Load data for the selected symbol
    df = load_csv(symbol_name, "D")
    
    if df.empty:
        error_message = f"No data found for symbol {symbol_name}. Please check the symbol and try again."
        return render_template('patternchart.html', SName=symbol_name, error_message=error_message)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')  # Ensure data is sorted by date

    if selected_date:
        try:
            # Convert the selected date to datetime
            selected_date = pd.to_datetime(selected_date)

            # Check if the selected date exists in the dataset
            if selected_date not in df['Date'].values:
                error_message = f"Selected date {selected_date.date()} not found in the dataset."
                return render_template('patternchart.html', SName=symbol_name, error_message=error_message)

            # Find the serial number corresponding to the selected date
            selected_serial = df[df['Date'] == selected_date].index[0] + 1

            # Calculate the serial number range
            start_serial = max(1, selected_serial - 10)
            end_serial = min(len(df), start_serial + 100)

            # Filter the data for the selected range
            filtered_df = df.iloc[start_serial - 1:end_serial].copy()  # Adjust for zero-based indexing
            filtered_df.reset_index(drop=True, inplace=True)
            filtered_df['Serial_No'] = range(start_serial, end_serial + 1)

            # Generate candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=filtered_df['Serial_No'],  # Use Serial_No for the x-axis
                open=filtered_df['Open'],
                high=filtered_df['High'],
                low=filtered_df['Low'],
                close=filtered_df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])
            fig.update_layout(
                title=f'{symbol_name} Price Action (Serial {start_serial} to {end_serial})',
                xaxis_title='Serial Number (Date Range)',
                yaxis_title='Price',
                xaxis=dict(
                    tickmode='array',
                    tickvals=filtered_df['Serial_No'],
                    ticktext=filtered_df['Date'].dt.strftime('%Y-%m-%d')  # Map dates to serial numbers
                ),
                template='plotly_dark',
                width=1350,  # Increase width
                height=750   # Increase height
            )
            candlestick_chart_html = pio.to_html(fig, full_html=False)
        except Exception as e:
            error_message = f"Error processing the selected date: {str(e)}"

    return render_template(
        'patternchart.html',
        SName=symbol_name,
        candlestick_chart_html=candlestick_chart_html,
        error_message=error_message
    )

if __name__ == '__main__':
    app.run(debug=True)