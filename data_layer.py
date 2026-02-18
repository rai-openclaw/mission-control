"""
Mission Control Data Layer Module

Provides structured data loading with validation for Mission Control dashboard.
Supports JSON data sources with fallback to markdown files.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

# Try to import jsonschema for validation
try:
    from jsonschema import validate, ValidationError as JSONSchemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Base paths - Docker-friendly
WORKSPACE_ROOT = Path("/Users/raitsai/.openclaw/workspace")
PORTFOLIO_DIR = WORKSPACE_ROOT / "portfolio"

# Check if running in Docker (data mounted at /app/data)
if Path("/app/data").exists():
    DATA_DIR = Path("/app/data")
    SCHEMAS_DIR = Path("/app/data/schemas")
    ANALYSES_DIR = Path("/app/data/analyses")
else:
    DATA_DIR = PORTFOLIO_DIR / "data"
    SCHEMAS_DIR = PORTFOLIO_DIR / "schemas"
    ANALYSES_DIR = DATA_DIR / "analyses"

# Ensure directories exist
def _ensure_dirs():
    """Ensure all required directories exist."""
    for dir_path in [DATA_DIR, SCHEMAS_DIR, ANALYSES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# SCHEMAS
# ============================================================================

HOLDING_SCHEMA = {
    "type": "object",
    "properties": {
        "accounts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "broker": {"type": "string"},
                    "holdings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"},
                                "cost_basis": {"type": "number"},
                                "notes": {"type": "string"}
                            },
                            "required": ["ticker", "shares"]
                        }
                    },
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "type": {"type": "string", "enum": ["CALL", "PUT"]},
                                "strike": {"type": "number"},
                                "expiration": {"type": "string"},
                                "contracts": {"type": "number"},
                                "premium": {"type": "number"}
                            },
                            "required": ["ticker", "type", "strike", "expiration", "contracts"]
                        }
                    },
                    "cash": {"type": "number"},
                    "cash_equivalents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"},
                                "value": {"type": "number"}
                            }
                        }
                    }
                },
                "required": ["name", "type", "broker"]
            }
        }
    },
    "required": ["accounts"]
}

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "date": {"type": "string"},
        "grade": {"type": "string"},
        "summary": {"type": "string"},
        "content": {"type": "string"},
        "price_target": {"type": "number"},
        "scenarios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "probability": {"type": "number"},
                    "target": {"type": "string"},
                    "return": {"type": "string"}
                }
            }
        }
    },
    "required": ["ticker", "date", "grade", "summary"]
}

EARNINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "date": {"type": "string"},
        "eps_estimate": {"type": "number"},
        "revenue_estimate": {"type": "number"},
        "time": {"type": "string", "enum": ["bmo", "amc", "--"]},
        "importance": {"type": "string", "enum": ["high", "medium", "low"]},
        "notes": {"type": "string"}
    },
    "required": ["ticker", "date"]
}

SCHEDULE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "title": {"type": "string"},
                    "type": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "notes": {"type": "string"}
                },
                "required": ["date", "title"]
            }
        }
    },
    "required": ["events"]
}

IDEA_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "status": {"type": "string", "enum": ["watching", "researching", "ready", "executed", "rejected"]},
                    "thesis": {"type": "string"},
                    "entry_price": {"type": "number"},
                    "target_price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "position_size": {"type": "string"},
                    "conviction": {"type": "string", "enum": ["high", "medium", "low"]},
                    "added_date": {"type": "string"},
                    "notes": {"type": "string"}
                },
                "required": ["ticker", "status", "thesis"]
            }
        }
    },
    "required": ["ideas"]
}

CORPORATE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "date": {"type": "string"},
                    "type": {"type": "string", "enum": ["merger", "acquisition", "spinoff", "restructuring", "dividend", "split", "other"]},
                    "description": {"type": "string"},
                    "impact": {"type": "string", "enum": ["high", "medium", "low"]},
                    "notes": {"type": "string"}
                },
                "required": ["ticker", "date", "type", "description"]
            }
        }
    },
    "required": ["events"]
}

# Schema registry
SCHEMAS = {
    "holdings": HOLDING_SCHEMA,
    "analyses": ANALYSIS_SCHEMA,
    "earnings": EARNINGS_SCHEMA,
    "schedule": SCHEDULE_SCHEMA,
    "ideas": IDEA_SCHEMA,
    "corporate": CORPORATE_SCHEMA
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _validate_data(data: Any, schema_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate data against a schema.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not HAS_JSONSCHEMA:
        return True, None  # Skip validation if jsonschema not available
    
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return True, None  # No schema found, skip validation
    
    try:
        validate(instance=data, schema=schema)
        return True, None
    except JSONSchemaValidationError as e:
        return False, f"Validation error: {e.message} at {list(e.path)}"
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"


def _load_json_file(filepath: Path) -> tuple[Optional[Any], Optional[str]]:
    """
    Load and parse a JSON file.
    
    Returns:
        Tuple of (data, error_message)
    """
    try:
        if not filepath.exists():
            return None, f"File not found: {filepath}"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            return None, f"File is empty: {filepath}"
        
        data = json.loads(content)
        return data, None
        
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {filepath}: {str(e)}"
    except PermissionError:
        return None, f"Permission denied reading {filepath}"
    except Exception as e:
        return None, f"Error loading {filepath}: {str(e)}"


def _parse_markdown_holdings(md_content: str) -> dict:
    """
    Parse holdings data from unified_portfolio_tracker.md format.
    Fallback when JSON not available.
    """
    accounts = []
    current_account = None
    
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Match account header
        if line.startswith('## Account:'):
            if current_account:
                accounts.append(current_account)
            account_name = line.replace('## Account:', '').strip()
            current_account = {
                'name': account_name,
                'type': '',
                'broker': '',
                'holdings': [],
                'options': [],
                'cash': 0.0,
                'cash_equivalents': []
            }
            
            # Look for account type and broker in next lines
            for j in range(i+1, min(i+5, len(lines))):
                type_match = re.search(r'\*\*Type:\*\*\s*(.+)', lines[j])
                broker_match = re.search(r'\*\*Broker:\*\*\s*(.+)', lines[j])
                if type_match:
                    current_account['type'] = type_match.group(1).strip()
                if broker_match:
                    current_account['broker'] = broker_match.group(1).strip()
        
        # Match stock holdings table rows
        if current_account and line.startswith('|') and not line.startswith('| Ticker') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                ticker = parts[1]
                if ticker and ticker not in ['', 'Ticker'] and not ticker.startswith('**'):
                    try:
                        shares = float(parts[2].replace(',', '')) if parts[2] else 0
                        cost_basis = float(parts[3].replace(',', '').replace('$', '')) if parts[3] else 0
                        notes = parts[4] if len(parts) > 4 else ''
                        current_account['holdings'].append({
                            'ticker': ticker,
                            'shares': shares,
                            'cost_basis': cost_basis,
                            'notes': notes
                        })
                    except ValueError:
                        pass
        
        # Match cash
        cash_match = re.search(r'\|\s*Cash\s*\|\s*\$?([\d,\.]+)', line)
        if cash_match and current_account:
            try:
                current_account['cash'] = float(cash_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        # Match options
        if current_account and 'Options Positions' in line:
            # Parse options in next lines
            for j in range(i+2, len(lines)):
                opt_line = lines[j].strip()
                if not opt_line.startswith('|') or opt_line.startswith('|---'):
                    if opt_line.startswith('##') or opt_line.startswith('###'):
                        break
                    continue
                parts = [p.strip() for p in opt_line.split('|')]
                if len(parts) >= 6 and parts[1] not in ['', 'Ticker', '—']:
                    try:
                        option_type = parts[2].upper() if parts[2] else 'CALL'
                        strike = float(parts[3].replace('$', '').replace(',', '')) if parts[3] else 0
                        expiration = parts[4]
                        contracts = int(parts[5]) if parts[5] else 0
                        premium = float(parts[6].replace('$', '').replace(',', '')) if len(parts) > 6 and parts[6] else 0
                        current_account['options'].append({
                            'ticker': parts[1],
                            'type': option_type,
                            'strike': strike,
                            'expiration': expiration,
                            'contracts': contracts,
                            'premium': premium
                        })
                    except ValueError:
                        pass
        
        i += 1
    
    if current_account:
        accounts.append(current_account)
    
    return {'accounts': accounts}


def _parse_markdown_analyses(md_content: str) -> list:
    """
    Parse analyses from analysis_history.md.
    Fallback when JSON not available.
    """
    analyses = []
    
    # Split by ticker sections (## TICKER pattern)
    sections = re.split(r'\n##\s+([A-Z]+)', md_content)
    
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            ticker = sections[i]
            content = sections[i + 1] if i + 1 < len(sections) else ''
            
            analysis = {
                'ticker': ticker,
                'date': '',
                'grade': '',
                'summary': '',
                'content': content.strip()
            }
            
            # Extract date
            date_match = re.search(r'\*\*Analyzed:\*\*\s*(.+)', content)
            if date_match:
                analysis['date'] = date_match.group(1).strip()
            
            # Extract grade
            grade_match = re.search(r'\*\*Grade:\*\*\s*([A-D][+-]?)', content)
            if grade_match:
                analysis['grade'] = grade_match.group(1)
            
            # Extract summary
            summary_match = re.search(r'\*\*Verdict\*\*|\*\*Recommendation\*\*|### Recommendation', content)
            if summary_match:
                start = summary_match.start()
                end = content.find('\n##', start) if content.find('\n##', start) > 0 else len(content)
                analysis['summary'] = content[start:end].strip()[:200] + '...'
            
            analyses.append(analysis)
    
    return analyses


# ============================================================================
# MAIN DATA LOADING FUNCTIONS
# ============================================================================

def load_holdings(use_markdown_fallback: bool = True) -> dict:
    """
    Load portfolio holdings data.
    
    Returns:
        Dict with 'accounts' key containing list of account holdings,
        or empty structure with error info.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "holdings.json"
    md_path = PORTFOLIO_DIR / "unified_portfolio_tracker.md"
    
    # Try JSON first
    data, error = _load_json_file(json_path)
    
    if data is not None:
        is_valid, validation_error = _validate_data(data, "holdings")
        if is_valid:
            return data
        else:
            return {
                "accounts": [],
                "_error": f"Validation failed: {validation_error}",
                "_source": str(json_path)
            }
    
    # Fallback to markdown
    if use_markdown_fallback and md_path.exists():
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            data = _parse_markdown_holdings(md_content)
            return {
                **data,
                "_warning": "Parsed from markdown (JSON not found)",
                "_source": str(md_path)
            }
        except Exception as e:
            return {
                "accounts": [],
                "_error": f"Failed to parse markdown fallback: {str(e)}",
                "_original_error": error
            }
    
    return {
        "accounts": [],
        "_error": error or "No data source available"
    }


def load_analyses(use_markdown_fallback: bool = True) -> list:
    """
    Load stock analyses data.
    
    Returns:
        List of analysis objects, possibly with metadata.
    """
    _ensure_dirs()
    
    analyses = []
    errors = []
    
    # Try individual JSON files in analyses/ directory
    if ANALYSES_DIR.exists():
        for json_file in sorted(ANALYSES_DIR.glob("*.json")):
            data, error = _load_json_file(json_file)
            if data is not None:
                is_valid, validation_error = _validate_data(data, "analyses")
                if is_valid:
                    analyses.append({
                        **data,
                        "_source": str(json_file.name)
                    })
                else:
                    errors.append(f"{json_file.name}: {validation_error}")
            else:
                errors.append(f"{json_file.name}: {error}")
    
    if analyses:
        return analyses
    
    # Fallback to markdown
    if use_markdown_fallback:
        md_path = PORTFOLIO_DIR / "analysis_history.md"
        if md_path.exists():
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                analyses = _parse_markdown_analyses(md_content)
                if analyses:
                    return {
                        "_analyses": analyses,
                        "_warning": "Parsed from markdown (JSON not found)",
                        "_source": str(md_path)
                    }
            except Exception as e:
                errors.append(f"Markdown fallback failed: {str(e)}")
    
    if errors:
        return [{"_error": "; ".join(errors), "_count": 0}]
    
    return []


def load_arnings() -> list:
    """
    Load earnings calendar data.
    
    Returns:
        List of earnings events.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "earnings.json"
    data, error = _load_json_file(json_path)
    
    if data is not None:
        # Handle both list and dict with 'earnings' key
        earnings = data if isinstance(data, list) else data.get('earnings', [])
        
        for item in earnings:
            is_valid, validation_error = _validate_data(item, "earnings")
            if not is_valid:
                item['_validation_error'] = validation_error
        
        return earnings
    
    # Return empty list with error info
    return [{"_error": error or "No earnings data available", "_count": 0}]


def load_schedule() -> dict:
    """
    Load schedule/events data.
    
    Returns:
        Dict with 'events' key containing list of scheduled events.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "schedule.json"
    data, error = _load_json_file(json_path)
    
    if data is not None:
        is_valid, validation_error = _validate_data(data, "schedule")
        if is_valid:
            return data
        else:
            return {
                "events": [],
                "_error": f"Validation failed: {validation_error}"
            }
    
    return {
        "events": [],
        "_error": error or "No schedule data available"
    }


def load_ideas() -> dict:
    """
    Load trade ideas data.
    
    Returns:
        Dict with 'ideas' key containing list of trade ideas.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "ideas.json"
    data, error = _load_json_file(json_path)
    
    if data is not None:
        is_valid, validation_error = _validate_data(data, "ideas")
        if is_valid:
            return data
        else:
            return {
                "ideas": [],
                "_error": f"Validation failed: {validation_error}"
            }
    
    return {
        "ideas": [],
        "_error": error or "No ideas data available"
    }


def load_corporate() -> dict:
    """
    Load corporate events data.
    
    Returns:
        Dict with 'events' key containing list of corporate events.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "corporate.json"
    data, error = _load_json_file(json_path)
    
    if data is not None:
        is_valid, validation_error = _validate_data(data, "corporate")
        if is_valid:
            return data
        else:
            return {
                "events": [],
                "_error": f"Validation failed: {validation_error}"
            }
    
    return {
        "events": [],
        "_error": error or "No corporate events data available"
    }


def load_api_usage() -> list:
    """
    Load API usage and configuration data.
    
    Returns:
        List of API configuration objects with usage details.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "api_usage.json"
    data, error = _load_json_file(json_path)
    
    if data is not None:
        # Load schema for validation if available
        schema_path = SCHEMAS_DIR / "api_usage.schema.json"
        if HAS_JSONSCHEMA and schema_path.exists():
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                validate(instance=data, schema=schema)
            except Exception as e:
                # Don't fail on validation error, just add warning
                if isinstance(data, list):
                    for item in data:
                        item['_validation_warning'] = f"Schema validation: {str(e)}"
        
        return data
    
    # Return empty list with error info
    return [{"_error": error or "No API usage data available", "_count": 0}]


def load_team() -> dict:
    """
    Load corporate team structure data.
    
    Returns:
        Dict with 'departments', 'team', and hierarchy data.
    """
    _ensure_dirs()
    
    json_path = DATA_DIR / "corporate.json"
    data, error = _load_json_file(json_path)
    
    if data is not None:
        # Build hierarchy
        hierarchy = {}
        for member in data.get('team', []):
            reports_to = member.get('reports_to')
            if reports_to:
                if reports_to not in hierarchy:
                    hierarchy[reports_to] = []
                hierarchy[reports_to].append(member['id'])
        
        data['hierarchy'] = hierarchy
        return data
    
    return {
        "departments": [],
        "team": [],
        "hierarchy": {},
        "_error": error or "No team data available"
    }


# ============================================================================
# HELPER FUNCTIONS FOR DATA ACCESS
# ============================================================================

def get_all_tickers() -> list[str]:
    """
    Get all unique tickers from holdings and analyses.
    
    Returns:
        Sorted list of unique ticker symbols.
    """
    tickers = set()
    
    holdings = load_holdings()
    for account in holdings.get('accounts', []):
        for holding in account.get('holdings', []):
            tickers.add(holding.get('ticker', ''))
    
    analyses = load_analyses()
    if isinstance(analyses, list):
        for analysis in analyses:
            if isinstance(analysis, dict):
                tickers.add(analysis.get('ticker', ''))
    elif isinstance(analyses, dict) and '_analyses' in analyses:
        for analysis in analyses['_analyses']:
            tickers.add(analysis.get('ticker', ''))
    
    return sorted([t for t in tickers if t])


def get_position_summary() -> dict:
    """
    Get summary of all positions across accounts.
    
    Returns:
        Dict with position summary statistics.
    """
    holdings = load_holdings()
    
    total_value = 0.0
    total_cost = 0.0
    position_count = 0
    account_count = 0
    
    for account in holdings.get('accounts', []):
        account_count += 1
        for holding in account.get('holdings', []):
            position_count += 1
            total_cost += holding.get('cost_basis', 0)
            # Note: Would need current prices for accurate value
    
    total_cash = 0.0
    for acc in holdings.get('accounts', []):
        cash = acc.get('cash', 0)
        if isinstance(cash, (int, float)):
            total_cash += cash
    
    return {
        "accounts": account_count,
        "positions": position_count,
        "total_cost_basis": round(total_cost, 2),
        "total_cash": round(total_cash, 2)
    }


def get_upcoming_earnings(days: int = 30) -> list:
    """
    Get earnings events within the next N days.
    
    Args:
        days: Number of days to look ahead
        
    Returns:
        Filtered list of earnings events.
    """
    earnings = load_earnings()
    
    if not earnings or (isinstance(earnings, list) and '_error' in earnings[0]):
        return earnings
    
    today = datetime.now()
    filtered = []
    
    for event in earnings:
        if not isinstance(event, dict):
            continue
        try:
            event_date = datetime.strptime(event.get('date', ''), '%Y-%m-%d')
            delta = (event_date - today).days
            if 0 <= delta <= days:
                event['_days_until'] = delta
                filtered.append(event)
        except (ValueError, TypeError):
            continue
    
    return sorted(filtered, key=lambda x: x.get('date', ''))


# Aliases for backwards compatibility or typos
load_earnings = load_arnings


# ============================================================================
# MODULE TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Mission Control Data Layer - Test Suite")
    print("=" * 60)
    
    print("\n1. Testing load_holdings()...")
    holdings = load_holdings()
    print(f"   Accounts: {len(holdings.get('accounts', []))}")
    if '_error' in holdings:
        print(f"   Error: {holdings['_error']}")
    if '_warning' in holdings:
        print(f"   Warning: {holdings['_warning']}")
    
    print("\n2. Testing load_analyses()...")
    analyses = load_analyses()
    if isinstance(analyses, list):
        print(f"   Analyses: {len(analyses)}")
        for a in analyses[:3]:
            if isinstance(a, dict):
                print(f"   - {a.get('ticker', 'N/A')}: {a.get('grade', 'N/A')}")
    elif isinstance(analyses, dict) and '_analyses' in analyses:
        print(f"   Analyses: {len(analyses['_analyses'])}")
    if analyses and isinstance(analyses, list) and '_error' in analyses[0]:
        print(f"   Error: {analyses[0]['_error']}")
    
    print("\n3. Testing load_earnings()...")
    earnings = load_earnings()
    print(f"   Earnings events: {len(earnings) if isinstance(earnings, list) else 'N/A'}")
    if earnings and isinstance(earnings, list) and '_error' in earnings[0]:
        print(f"   Error: {earnings[0]['_error']}")
    
    print("\n4. Testing load_schedule()...")
    schedule = load_schedule()
    print(f"   Events: {len(schedule.get('events', []))}")
    if '_error' in schedule:
        print(f"   Error: {schedule['_error']}")
    
    print("\n5. Testing load_ideas()...")
    ideas = load_ideas()
    print(f"   Ideas: {len(ideas.get('ideas', []))}")
    if '_error' in ideas:
        print(f"   Error: {ideas['_error']}")
    
    print("\n6. Testing load_corporate()...")
    corporate = load_corporate()
    print(f"   Events: {len(corporate.get('events', []))}")
    if '_error' in corporate:
        print(f"   Error: {corporate['_error']}")
    
    print("\n7. Testing load_api_usage()...")
    api_usage = load_api_usage()
    print(f"   APIs: {len(api_usage) if isinstance(api_usage, list) else 'N/A'}")
    if api_usage and isinstance(api_usage, list) and '_error' in api_usage[0]:
        print(f"   Error: {api_usage[0]['_error']}")
    else:
        for api in api_usage[:3]:
            if isinstance(api, dict):
                print(f"   - {api.get('name', 'N/A')}: {api.get('tier', 'N/A')}")
    
    print("\n8. Testing get_all_tickers()...")
    tickers = get_all_tickers()
    print(f"   Total tickers: {len(tickers)}")
    print(f"   Sample: {', '.join(tickers[:10])}")
    
    print("\n9. Testing get_position_summary()...")
    summary = get_position_summary()
    print(f"   Summary: {summary}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
