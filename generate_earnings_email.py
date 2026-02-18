#!/usr/bin/env python3
"""Generate HTML email from earnings research JSON"""
import json
import sys
from datetime import datetime

def generate_html_email(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        h2 {{
            color: #1e3a5f;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
        }}
        th {{
            background: #1e3a5f;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .grade-a {{ color: #2e7d32; font-weight: bold; }}
        .grade-b {{ color: #689f38; font-weight: bold; }}
        .grade-c {{ color: #f9a825; font-weight: bold; }}
        .grade-d {{ color: #ef6c00; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Daily Stocks Recommendation Report</h1>
            <p>{data.get('report_date', 'N/A')} | {data.get('generated_at', 'N/A')}</p>
        </div>
        <div class="content">
            <h2>Executive Summary</h2>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Exp Move</th>
                    <th>2x EM</th>
                    <th>Grade</th>
                    <th>Rec</th>
                </tr>
"""
    
    for stock in data.get('executive_summary_table', []):
        grade_class = f"grade-{stock.get('grade', '')[0].lower()}" if stock.get('grade') else ''
        html += f"""
                <tr>
                    <td><strong>{stock.get('ticker', '')}</strong></td>
                    <td>{stock.get('company', '')}</td>
                    <td>{stock.get('exp_move', '')}</td>
                    <td>{stock.get('2x_em', '')}</td>
                    <td class="{grade_class}">{stock.get('grade', '')}</td>
                    <td>{stock.get('rec', '')}</td>
                </tr>
"""
    
    html += """
            </table>
        </div>
    </div>
</body>
</html>
"""
    return html

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 generate_earnings_email.py <json_file>")
        sys.exit(1)
    html = generate_html_email(sys.argv[1])
    print(html)
