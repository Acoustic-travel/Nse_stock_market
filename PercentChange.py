from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

def Loadcsv(Symbol=' ', TimeFrame=' '):
    data = pd.read_csv(f'D:\\CODING\\_Out\\{TimeFrame}\\{Symbol}_{TimeFrame}.csv', parse_dates=['Date'], dayfirst=True)
    data.dropna(subset=['Date'], inplace=True)
    data.drop(columns=['Volume', 'RSI', 'MBand', 'UBand', 'LBand', 'SMA20Diff'], inplace=True, errors='ignore')
    serial_no = range(1, len(data) + 1)
    data.insert(0, 'Serial_No', serial_no)
    data['PerChng'] = data['PerChng'].round(0)
    return data

def GetHighLow(data, filter_data, L=7, Step='F'):
    output_data = []
    for index, row in filter_data.iterrows():
        Serial_No = row['Serial_No']
        if Step == 'F':
            close_value = data.loc[data['Serial_No'] == Serial_No + L, 'Close'].values[0] if Serial_No + L in data['Serial_No'].values else "N/A"
            filter_original_data = data[(data['Serial_No'] > Serial_No) & (data['Serial_No'] <= Serial_No + L)]
        else:
            filter_original_data = data[(data['Serial_No'] < Serial_No) & (data['Serial_No'] >= Serial_No - L)]
            close_value = data.loc[data['Serial_No'] == Serial_No - L, 'Close'].values[0] if Serial_No - L in data['Serial_No'].values else "N/A"
        
        max_high = filter_original_data['High'].max()
        min_low = filter_original_data['Low'].min()
        close = row['Close']

        if Step == 'F' and close_value != "N/A":
            max_percentage = (max_high - close) / close * 100
            min_percentage = (min_low - close) / close * 100
            close_percentage = (close_value - close) / close * 100
            output_data.append({
                'Serial_No': Serial_No,
                'Max High': round(max_high, 1),
                'Min Low': round(min_low, 1),
                'Close Value': round(close_value, 1),
                'Max (%)': round(max_percentage, 1),
                'Min (%)': round(min_percentage, 1),
                'Close (%)': round(close_percentage, 1)
            })
        elif close_value != "N/A":
            From_HL = (close - min_low) * 99 / (max_high - min_low) + 1
            output_data.append({
                'Serial_No': Serial_No,
                'Max High': round(max_high, 1),
                'Min Low': round(min_low, 1),
                'Close Value': round(close, 1),
                'From_HL (%)': round(From_HL, 1)
            })
    return pd.DataFrame(output_data)

def get_available_symbols(timeframe):
    folder_path = f'D:\\CODING\\_Out\\{timeframe}\\'
    symbols = []
    # List all files in the specified folder
    for file in os.listdir(folder_path):
        if file.endswith(f'_{timeframe}.csv'):
            symbol = file.replace(f'_{timeframe}.csv', '')
            symbols.append(symbol)
    return symbols

def build_response(df_result_filtered, average_max, average_min, average_close):
    response = df_result_filtered.to_dict(orient='records')
    response.append({
        'Average Max (%)': round(average_max, 2) if average_max != "N/A" else "N/A",
        'Average Min (%)': round(average_min, 2) if average_min != "N/A" else "N/A",
        'Average Close (%)': round(average_close, 2) if average_close != "N/A" else "N/A"
    })
    return jsonify(response)

@app.route('/')
def home():
    return render_template('PercentChange.html')

@app.route('/symbols', methods=['GET'])
def get_symbols():
    timeframe = request.args.get('timeframe', 'D')  
    directory = f'D:\\CODING\\_Out\\{timeframe}\\'
    symbols = [f.split('_')[0] for f in os.listdir(directory) if f.endswith('.csv')]
    return jsonify(symbols)

@app.route('/analyze', methods=['POST'])
def analyze_data():
    symbol = request.json.get('symbol', 'ABB')  
    timeframe = request.json.get('timeframe', 'D') 
    per_chng = request.json.get('perchng', -4)  
    lf = request.json.get('lf', 7)  
    lb = request.json.get('lb', 100)  

    # Load the CSV data
    df = Loadcsv(Symbol=symbol, TimeFrame=timeframe)

    # Filter based on PerChng
    df_perchng = df[df['PerChng'] == per_chng]

    # Get high and low data
    df_lf = GetHighLow(df, df_perchng, lf, 'F')
    df_lb = GetHighLow(df, df_perchng, lb, 'B')

    # Merge results
    df_result = df_perchng.merge(df_lf, on='Serial_No', how='outer') \
                           .merge(df_lb, on='Serial_No', how='outer')
    df_result = df_perchng.merge(df_lf, on='Serial_No', how='outer').merge(df_lb, on='Serial_No', how='outer')
    average_max_percentage = df_result['Max (%)'].mean() if 'Max (%)' in df_result else "N/A"
    average_min_percentage = df_result['Min (%)'].mean() if 'Min (%)' in df_result else "N/A"
    average_close_percentage = df_result['Close (%)'].mean() if 'Close (%)' in df_result else "N/A"

   # Filter columns for the response
    columns_filter = ['Date', 'Open', 'High', 'Low', 'Close', 'Max (%)', 'Min (%)', 'Close (%)', 'From_HL (%)']
    df_result_filtered = df_result[columns_filter].dropna()  # Drop rows with NaN values if necessary

    return build_response(df_result_filtered, average_max_percentage, average_min_percentage, average_close_percentage)
    # Convert DataFrame to JSON
   # result_json = df_result_filtered.to_dict(orient='records')
    
   # return jsonify(result_json)

if __name__ == '__main__':
    app.run(debug=True)