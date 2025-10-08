from flask import Flask, render_template, jsonify
import os
from datetime import datetime, timedelta
import requests
from monitor import FPAMonitor

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')  # Get from newsapi.org

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/fpa-metrics')
def get_fpa_metrics():
    """Get FP&A monitoring metrics and insights"""
    try:
        # Initialize monitor
        monitor = FPAMonitor()
        
        # Get data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Run analysis
        results = monitor.analyze_metrics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/exchange-rates')
def get_exchange_rates():
    """Get Nordic exchange rates from European Central Bank"""
    try:
        # Fetch from ECB API
        url = 'https://api.exchangerate.host/latest'
        params = {
            'base': 'EUR',
            'symbols': 'SEK,NOK,DKK,ISK'  # Nordic currencies
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Format response
        rates = {
            'success': True,
            'base': 'EUR',
            'date': data.get('date'),
            'rates': {
                'SEK': {'name': 'Swedish Krona', 'rate': data['rates'].get('SEK', 'N/A')},
                'NOK': {'name': 'Norwegian Krone', 'rate': data['rates'].get('NOK', 'N/A')},
                'DKK': {'name': 'Danish Krone', 'rate': data['rates'].get('DKK', 'N/A')},
                'ISK': {'name': 'Icelandic Króna', 'rate': data['rates'].get('ISK', 'N/A')}
            }
        }
        
        return jsonify(rates)
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch exchange rates: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/news')
def get_news():
    """Get macroeconomic news for Nordic countries"""
    try:
        if not NEWS_API_KEY:
            # Return sample data if no API key
            return jsonify({
                'success': True,
                'articles': [
                    {
                        'title': 'Nordic Economic Outlook Remains Strong',
                        'description': 'Economic indicators show continued growth across Nordic region with stable inflation rates.',
                        'url': 'https://example.com/news1',
                        'urlToImage': 'https://via.placeholder.com/300x200?text=Nordic+Economy',
                        'publishedAt': datetime.now().isoformat(),
                        'source': {'name': 'Economic Times'}
                    },
                    {
                        'title': 'Swedish Central Bank Holds Interest Rates Steady',
                        'description': 'Riksbank maintains current monetary policy amid stable economic conditions.',
                        'url': 'https://example.com/news2',
                        'urlToImage': 'https://via.placeholder.com/300x200?text=Sweden+Finance',
                        'publishedAt': (datetime.now() - timedelta(hours=2)).isoformat(),
                        'source': {'name': 'Financial News'}
                    },
                    {
                        'title': 'Norway Oil Fund Posts Strong Returns',
                        'description': 'Government pension fund reports significant gains in latest quarter.',
                        'url': 'https://example.com/news3',
                        'urlToImage': 'https://via.placeholder.com/300x200?text=Norway+Fund',
                        'publishedAt': (datetime.now() - timedelta(hours=5)).isoformat(),
                        'source': {'name': 'Nordic Business'}
                    },
                    {
                        'title': 'Danish GDP Growth Exceeds Expectations',
                        'description': 'Latest figures show robust economic performance driven by exports and domestic consumption.',
                        'url': 'https://example.com/news4',
                        'urlToImage': 'https://via.placeholder.com/300x200?text=Denmark+GDP',
                        'publishedAt': (datetime.now() - timedelta(hours=8)).isoformat(),
                        'source': {'name': 'Market Watch'}
                    },
                    {
                        'title': 'Finland Tech Sector Sees Investment Surge',
                        'description': 'Venture capital funding in Finnish technology companies reaches new highs.',
                        'url': 'https://example.com/news5',
                        'urlToImage': 'https://via.placeholder.com/300x200?text=Finland+Tech',
                        'publishedAt': (datetime.now() - timedelta(hours=12)).isoformat(),
                        'source': {'name': 'Tech Business'}
                    }
                ],
                'note': 'Using sample data. Set NEWS_API_KEY environment variable for live news.'
            })
        
        # Fetch from NewsAPI
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': 'Nordic OR Sweden OR Norway OR Denmark OR Finland OR Iceland AND (economy OR finance OR GDP OR market)',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,
            'apiKey': NEWS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return jsonify({
            'success': True,
            'articles': data.get('articles', [])
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch news: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
