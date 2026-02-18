#!/usr/bin/env python3
"""
Mission Control v3.0 - Portfolio Dashboard with JSON Data Layer
Uses clean JSON data sources with schema validation
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, render_template, request

# Add mission_control to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import data layer, fallback to inline if not available
try:
    from data_layer import load_holdings, load_analyses, load_earnings, load_schedule, load_ideas, load_team
    USE_DATA_LAYER = True
    print("✅ Using new JSON data layer")
except ImportError as e:
    USE_DATA_LAYER = False
    print(f"⚠️ Data layer not available ({e}), using fallback")

app = Flask(__name__)

# Configuration - Docker-aware paths
if os.path.exists('/app/data'):
    # Running in Docker container
    WORKSPACE = '/app'
    DATA_DIR = '/app/data'
    PRICE_FILE = '/app/data/price_cache.json'
else:
    # Running locally
    WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(WORKSPACE, 'portfolio', 'data')
    PRICE_FILE = os.path.join(WORKSPACE, 'portfolio', 'price_cache.json')

DATA_FILE = os.path.join(DATA_DIR, 'holdings.json')
ANALYSES_DIR = os.path.join(DATA_DIR, 'analyses')

# Fallback markdown files (for backward compatibility)
MD_DATA_FILE = os.path.join(DATA_DIR, '..', 'unified_portfolio_tracker.md')
MD_ANALYSIS_FILE = os.path.join(DATA_DIR, '..', 'portfolio_tracker.md')

# API Keys - Production should use environment variables
# For local development, fallback to demo key (rotate regularly)
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY') or 'd68o369r01qq5rjg8lcgd68o369r01qq5rjg8ld0'

# Price Constants - for assets not available via APIs
PRICE_CONSTANTS = {
    'SGOV': 100.0,  # iShares 0-3 Month Treasury Bond ETF - standard NAV
}

# ============================================================================
# DATA PARSING (Legacy - for fallback)
# ============================================================================

def parse_markdown_table(content, section_marker):
    """Extract table data from markdown section"""
    lines = content.split('\n')
    in_section = False
    headers = []
    rows = []
    
    for line in lines:
        if section_marker in line:
            in_section = True
            continue
        
        if in_section:
            if line.startswith('###') or line.startswith('---'):
                break
            
            if '|' in line and not headers:
                headers = [h.strip() for h in line.split('|') if h.strip()]
                continue
            
            if '|' in line and '---' not in line and headers:
                values = [v.strip() for v in line.split('|')]
                values = [v for v in values if v or v == '']
                while values and values[0] == '':
                    values.pop(0)
                while len(values) > len(headers) and values and values[-1] == '':
                    values.pop()
                if values and len(values) >= len(headers) - 1:
                    row = {}
                    for i, header in enumerate(headers):
                        if i < len(values):
                            row[header] = values[i]
                        else:
                            row[header] = ''
                    rows.append(row)
    
    return rows

# ============================================================================
# API ENDPOINTS
# ============================================================================

def transform_holdings_for_dashboard(data):
    """Transform JSON holdings data to dashboard format"""
    accounts = data.get('accounts', [])
    
    # Aggregate stocks across accounts
    stocks_map = {}
    options_list = []
    cash_data = {'Cash': {'total': 0, 'accounts': []}, 'SGOV': {'total': 0, 'total_shares': 0, 'accounts': [], 'price': 100.0}}
    misc_total = 0
    
    # Load prices from cache if available
    prices = {}
    try:
        if os.path.exists(PRICE_FILE):
            with open(PRICE_FILE, 'r') as f:
                price_data = json.load(f)
                # Handle nested structure: {"prices": {"stocks": {"TICKER": {"price": 123}}}}
                if isinstance(price_data, dict) and 'prices' in price_data:
                    stocks_data = price_data['prices'].get('stocks', {})
                    prices = {ticker: data.get('price', -1) for ticker, data in stocks_data.items()}
                    # Also add crypto prices
                    crypto_data = price_data['prices'].get('crypto', {})
                    for asset, data in crypto_data.items():
                        prices[asset] = data.get('price', -1)
                else:
                    prices = price_data
    except Exception as e:
        print(f"Error loading prices: {e}")
        pass
    
    for account in accounts:
        account_name = account.get('name', 'Unknown')
        
        # Process stocks
        for stock in account.get('stocks_etfs', []):
            ticker = stock.get('Ticker', '')
            shares = stock.get('Shares', 0)
            cost_basis = stock.get('Cost Basis', 0)
            
            if ticker not in stocks_map:
                stocks_map[ticker] = {
                    'ticker': ticker,
                    'total_shares': 0,
                    'total_cost_basis': 0,
                    'total_value': 0,
                    'price': prices.get(ticker, PRICE_CONSTANTS.get(ticker, -1)),  # Check cache, then constants, then error
                    'accounts': []
                }
            
            stocks_map[ticker]['total_shares'] += shares
            stocks_map[ticker]['total_cost_basis'] += cost_basis
            stocks_map[ticker]['accounts'].append({
                'account': account_name,
                'shares': shares,
                'cost_basis': cost_basis
            })
        
        # Process options - preserve sign for short positions
        for opt in account.get('options', []):
            contracts = opt.get('Contracts', 0)  # Don't use abs() - preserve sign
            premium = opt.get('Entry Premium', 0)
            # For short options (negative contracts), value is negative (obligation)
            # For long options (positive contracts), value is positive (asset)
            notional_value = contracts * premium * 100
            options_list.append({
                'ticker': opt.get('Ticker', ''),
                'type': opt.get('Type', 'PUT'),
                'strike': opt.get('Strike', 0),
                'expiration': opt.get('Expiration', ''),
                'total_contracts': contracts,  # Preserve negative for short
                'total_entry_value': notional_value,
                'current_value': notional_value,  # Simplified - should use current option price
                'accounts': [{'account': account_name, 'contracts': contracts, 'entry_premium': premium}],
                'note': f"{contracts} contracts @ ${premium}"
            })
        
        # Process cash
        for cash_item in account.get('cash', []):
            asset = cash_item.get('Asset', 'Cash')
            qty = cash_item.get('Quantity', 0)
            if asset == 'Cash':
                cash_data['Cash']['total'] += qty
                cash_data['Cash']['accounts'].append({'account': account_name, 'value': qty})
            elif asset == 'SGOV':
                cash_data['SGOV']['total'] += qty * 100  # Assuming $100/share
                cash_data['SGOV']['total_shares'] += qty
                cash_data['SGOV']['accounts'].append({'account': account_name, 'value': qty * 100})
        
    # Process misc assets (crypto, etc.) with live prices
    misc_list = []
    for account in accounts:
        account_name = account.get('name', 'Unknown')
        for misc in account.get('misc', []):
            asset = misc.get('Asset', '')
            amount = misc.get('Amount', 0)
            cost_basis = misc.get('Cost Basis', 0)
            asset_type = misc.get('Type', 'Other')
            
            # Get live price if available
            price = prices.get(asset, 0)
            current_value = amount * price if price > 0 else cost_basis
            
            misc_list.append({
                'asset': asset,
                'type': asset_type,
                'amount': amount,
                'price': price,
                'cost_basis': cost_basis,
                'current_value': current_value,
                'account': account_name
            })
    
    misc_total = sum(m['current_value'] for m in misc_list)
    
    # Calculate stock values and returns
    stocks_list = []
    for stock in stocks_map.values():
        stock['total_value'] = stock['total_shares'] * stock['price']
        cost_per_share = stock['total_cost_basis'] / stock['total_shares'] if stock['total_shares'] > 0 else 0
        stock['total_return_pct'] = ((stock['price'] - cost_per_share) / cost_per_share * 100) if cost_per_share > 0 else 0
        stocks_list.append(stock)
    
    # Calculate totals
    stocks_total = sum(s['total_value'] for s in stocks_list)
    options_total = sum(o['current_value'] for o in options_list)
    cash_total = cash_data['Cash']['total'] + cash_data['SGOV']['total']
    
    return {
        'stocks': stocks_list,
        'options': options_list,
        'cash': cash_data,
        'misc': misc_list,
        'totals': {
            'stocks_etfs': stocks_total,
            'options': options_total,
            'cash_equivalents': cash_total,
            'misc': misc_total,
            'grand_total': stocks_total + options_total + cash_total + misc_total
        },
        'last_price_refresh': data.get('last_updated', datetime.now().isoformat())
    }

@app.route('/api/portfolio')
def api_portfolio():
    """Return complete portfolio data for Holdings tab"""
    try:
        if USE_DATA_LAYER:
            data = load_holdings(use_markdown_fallback=True)
            # Transform to dashboard format
            transformed = transform_holdings_for_dashboard(data)
            return jsonify(transformed)
        else:
            # Fallback to old parsing
            return jsonify({'error': 'Data layer not available'}), 500
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

def fetch_yahoo_price(ticker):
    """Fetch mutual fund price from Yahoo Finance"""
    try:
        import urllib.request
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            result = data.get('chart', {}).get('result', [{}])[0]
            return result.get('meta', {}).get('regularMarketPrice', 0)
    except Exception as e:
        print(f"Yahoo error for {ticker}: {e}")
        return 0

def fetch_coingecko_price(asset):
    """Fetch crypto price from CoinGecko"""
    try:
        import urllib.request
        asset_map = {'ETH': 'ethereum', 'BTC': 'bitcoin', 'SOL': 'solana'}
        asset_id = asset_map.get(asset, asset.lower())
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={asset_id}&vs_currencies=usd'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get(asset_id, {}).get('usd', 0)
    except Exception as e:
        print(f"CoinGecko error for {asset}: {e}")
        return 0

@app.route('/api/refresh-prices', methods=['POST'])
def refresh_prices():
    """Refresh all prices from APIs"""
    try:
        import requests
        
        # Get all tickers and misc assets from holdings
        data = load_holdings(use_markdown_fallback=True)
        stock_tickers = set()
        misc_assets = set()
        
        for account in data.get('accounts', []):
            for stock in account.get('stocks_etfs', []):
                ticker = stock.get('Ticker', '')
                if ticker and ticker not in ['SGOV', 'Cash']:
                    stock_tickers.add(ticker)
            for misc in account.get('misc', []):
                asset = misc.get('Asset', '')
                if asset:
                    misc_assets.add(asset)
        stock_tickers.add('SGOV')
        
        prices = {'version': '2.0', 'last_updated': datetime.now().isoformat(), 'prices': {'stocks': {}, 'crypto': {}}}
        
        # Fetch stock prices (Finnhub for most, Yahoo for mutual funds)
        mutual_funds = ['VSEQX', 'VTCLX', 'VTMSX', 'VIG', 'VYM', 'VXUS']
        
        for ticker in stock_tickers:
            if not ticker:
                continue
            try:
                if ticker in mutual_funds:
                    # Use Yahoo Finance for mutual funds
                    price = fetch_yahoo_price(ticker)
                    source = 'yahoo'
                else:
                    # Use Finnhub for regular stocks
                    url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}'
                    resp = requests.get(url, timeout=5)
                    price = 0
                    if resp.status_code == 200:
                        data = resp.json()
                        price = data.get('c', 0)
                    source = 'finnhub'
                
                if price > 0:
                    prices['prices']['stocks'][ticker] = {
                        'price': price,
                        'source': source,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue
        
        # Fetch crypto prices from CoinGecko
        for asset in misc_assets:
            try:
                price = fetch_coingecko_price(asset)
                if price > 0:
                    prices['prices']['crypto'][asset] = {
                        'price': price,
                        'source': 'coingecko',
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"Error fetching {asset}: {e}")
                continue
        
        # Save to cache
        with open(PRICE_FILE, 'w') as f:
            json.dump(prices, f, indent=2)
        
        stocks_count = len(prices['prices']['stocks'])
        crypto_count = len(prices['prices']['crypto'])
        
        return jsonify({
            'success': True, 
            'prices_updated': stocks_count + crypto_count,
            'stocks': stocks_count,
            'crypto': crypto_count
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/analysis-archive')
def api_analysis_archive():
    """Return stock analysis archive for Analysis Archive tab"""
    try:
        if USE_DATA_LAYER:
            analyses = load_analyses(use_markdown_fallback=True)
            return jsonify(analyses)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/earnings-research')
def api_earnings_research():
    """Return earnings research for Earnings Research tab"""
    try:
        if USE_DATA_LAYER:
            earnings = load_earnings()
            return jsonify(earnings)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ideas')
def api_ideas():
    """Return ideas for Ideas & Notes tab"""
    try:
        if USE_DATA_LAYER:
            ideas = load_ideas()
            return jsonify(ideas)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue-idea', methods=['POST'])
def queue_idea():
    """Queue an idea for execution - sends notification to user"""
    try:
        data = request.get_json()
        idea_id = data.get('idea_id')
        idea_title = data.get('idea_title', 'Unknown Idea')
        
        if not idea_id:
            return jsonify({'success': False, 'error': 'No idea_id provided'}), 400
        
        # Load the full idea details
        ideas_data = load_ideas()
        ideas_list = ideas_data.get('ideas', []) if isinstance(ideas_data, dict) else ideas_data
        
        idea = None
        for i in ideas_list:
            if i.get('id') == idea_id:
                idea = i
                break
        
        if not idea:
            return jsonify({'success': False, 'error': 'Idea not found'}), 404
        
        # Update status to in_progress if it's approved
        if idea.get('status') == 'approved':
            idea['status'] = 'in_progress'
            # Save updated ideas
            from pathlib import Path
            import json
            ideas_file = Path(WORKSPACE) / 'portfolio' / 'data' / 'ideas.json'
            with open(ideas_file, 'w') as f:
                json.dump({'ideas': ideas_list, 'last_updated': datetime.now().isoformat()}, f, indent=2)
        
        # Add to queue file for notification
        try:
            sys.path.insert(0, WORKSPACE)
            from queue_manager import add_to_queue
            added, msg = add_to_queue(idea_id, idea_title, idea.get('context', ''))
        except Exception as queue_err:
            print(f"Queue error: {queue_err}")
            added, msg = False, str(queue_err)
        
        return jsonify({
            'success': True, 
            'message': "Idea queued successfully. You'll receive a Telegram notification within 30 minutes.",
            'idea_id': idea_id,
            'new_status': idea.get('status'),
            'queued': added
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/queue-status')
def queue_status():
    """Get current queue status (for heartbeat checks)"""
    try:
        sys.path.insert(0, WORKSPACE)
        from queue_manager import get_pending_ideas
        pending = get_pending_ideas()
        return jsonify({
            'pending_count': len(pending),
            'pending_ids': [i['id'] for i in pending]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule')
def api_schedule():
    """Return schedule for Schedule tab"""
    try:
        if USE_DATA_LAYER:
            schedule = load_schedule()
            return jsonify(schedule)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/corporate')
def api_corporate():
    """Return corporate structure for Corporate tab"""
    try:
        if USE_DATA_LAYER:
            corporate = load_team()
            return jsonify(corporate)
        else:
            # Fallback: load directly from JSON
            import json
            corporate_file = os.path.join(WORKSPACE, 'portfolio', 'data', 'corporate.json')
            if os.path.exists(corporate_file):
                with open(corporate_file, 'r') as f:
                    return jsonify(json.load(f))
            return jsonify({'team': [], 'departments': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage')
def api_usage():
    """Return API usage for API Usage tab"""
    try:
        # Read from api_usage.json
        api_file = os.path.join(DATA_DIR, 'api_usage.json')
        if os.path.exists(api_file):
            with open(api_file, 'r') as f:
                api_list = json.load(f)
                # Transform to expected format
                api_usage_data = {}
                total_cost = 0.0
                for api in api_list:
                    api_id = api.get('id', api.get('name', 'unknown'))
                    api_usage_data[api_id] = {
                        'name': api.get('name', 'Unknown'),
                        'purpose': api.get('purpose', ''),
                        'status': api.get('status', 'Active'),
                        'tier': api.get('tier', 'Free'),
                        'limit': api.get('limits', {}).get('requests_per_min') or api.get('limits', {}).get('monthly_limit') or 'N/A',
                        'calls_this_month': api.get('calls_this_month', 0),
                        'cost': api.get('cost_this_month', 0.0),
                        'dashboard_url': api.get('dashboard_url', '')
                    }
                    total_cost += api.get('cost_this_month', 0.0)
                return jsonify({'apis': api_usage_data, 'total_cost': total_cost})
        # Fallback: return empty structure
        return jsonify({'apis': {}, 'total_cost': 0.0})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/')
def dashboard():
    """Render dashboard"""
    return render_template('dashboard.html')

@app.route('/corporate-test')
def corporate_test():
    """Standalone corporate tab test"""
    return render_template('corporate_test_standalone.html')

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
