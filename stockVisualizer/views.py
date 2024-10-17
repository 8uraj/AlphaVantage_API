from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StockData
import requests
import json

APIKEY = '5EDOKWKAI40FVQGF'  # Replace with your actual Alpha Vantage API key
DATABASE_ACCESS = True  # If True, the app checks local DB for stock data before querying Alpha Vantage

# Home page view
def home(request):
    return render(request, 'home.html', {})

# API endpoint to fetch daily stock data
@csrf_exempt
def get_stock_data(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if request is an AJAX request
        ticker = request.POST.get('ticker', 'null').upper()

        # Check database for stock data if enabled
        if DATABASE_ACCESS:
            if StockData.objects.filter(symbol=ticker).exists():
                entry = StockData.objects.filter(symbol=ticker)[0]
                return HttpResponse(entry.data, content_type='application/json')

        # Prepare to fetch data from Alpha Vantage API
        output_dictionary = {}
        price_series = requests.get(
            f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&apikey={APIKEY}&outputsize=compact'
        ).json()  # Use 'compact' to fetch only the latest 100 data points

        # Error handling for API responses
        if 'Error Message' in price_series:
            return HttpResponse(json.dumps({'error': 'Stock data not found or API limit reached'}), content_type='application/json')

        # Filter for daily stock data only
        daily_data = {}
        time_series = price_series.get('Time Series (Daily)', {})
        for date, data in time_series.items():
            daily_data[date] = {
                'open': float(data['1. open']),
                'high': float(data['2. high']),
                'low': float(data['3. low']),
                'close': float(data['4. close']),
                'adjusted_close': float(data['5. adjusted close']),
                'volume': int(data['6. volume']),
                'dividend_amount': float(data['7. dividend amount']),
                'split_coefficient': float(data['8. split coefficient']),
            }

        output_dictionary['prices'] = daily_data

        # Save stock data to the database
        temp = StockData(symbol=ticker, data=json.dumps(output_dictionary))
        temp.save()

        return HttpResponse(json.dumps(output_dictionary), content_type='application/json')
    else:
        return HttpResponse("Not Ajax")
