#!/usr/bin/env python3
"""Report Generator - Creates HTML reports from analysis JSON"""
import json
import sys

def generate_html_report(analysis_file):
    with open(analysis_file, 'r') as f:
        data = json.load(f)
    
    # Simplified HTML for email
    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 12px; }}
th {{ background: #1e3a5f; color: white; padding: 12px; text-align: left; }}
td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }}
.grade-a {{ color: #2e7d32; font-weight: bold; background: #e8f5e9; padding: 3px 8px; border-radius: 4px; }}
.grade-b {{ color: #689f38; font-weight: bold; background: #f1f8e9; padding: 3px 8px; border-radius: 4px; }}
.grade-c {{ color: #f57c00; font-weight: bold; background: #fff3e0; padding: 3px 8px; border-radius: 4px; }}
.rec-trade {{ color: #2e7d32; font-weight: 600; }}
.rec-watch {{ color: #f57c00; font-weight: 600; }}
.rec-avoid {{ color: #c62828; font-weight: 600; }}
.ticker {{ font-weight: bold; color: #1e3a5f; }}
.notes {{ font-size: 11px; color: #555; line-height: 1.4; }}
.em {{ font-weight: 600; color: #2d5a87; }}
h2 {{ color: #1e3a5f; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
h3 {{ color: #2d5a87; margin-top: 25px; }}
.component {{ margin: 8px 0; padding: 10px; background: #f5f5f5; border-radius: 4px; font-size: 13px; }}
.key-insight {{ background: #fff8e1; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
.trade-setup {{ background: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50; margin: 15px 0; }}
.risk {{ background: #ffebee; padding: 15px; border-left: 4px solid #f44336; margin: 15px 0; }}
</style>
</head>
<body>
<h2>Daily Stocks Recommendation Report - {data['date']}</h2>
<table>
<thead>
<tr><th>Ticker</th><th>Exp Move</th><th>2x EM</th><th>Grade</th><th>Rec</th><th>Key Analysis</th></tr>
</thead>
<tbody>
"""
    
    for ticker, stock in data['stocks'].items():
        grade_class = f"grade-{stock['grade'][0].lower()}"
        rec_class = f"rec-{stock.get('recommendation', 'watch').lower()}"
        notes = stock['key_insight']
        
        html += f"""<tr>
<td><span class="ticker">{ticker}</span></td>
<td class="em">±{stock['expected_move']}%</td>
<td>±{stock['safety_margin_2x']}%</td>
<td><span class="{grade_class}">{stock['grade']} ({stock['total_score']})</span></td>
<td class="{rec_class}">{stock.get('recommendation', 'Watch')}</td>
<td class="notes">{notes}</td>
</tr>"""
    
    html += "</tbody></table><h2>Detailed Analysis</h2>"
    
    for ticker, stock in data['stocks'].items():
        html += f"""<h3>{ticker} - Grade {stock['grade']} ({stock['total_score']}/100)</h3>
<p><strong>Expected Move:</strong> ±{stock['expected_move']}% | <strong>2x Safety:</strong> ±{stock['safety_margin_2x']}%</p>

<h4>WHY THIS GRADE:</h4>
"""
        for component, details in stock['grade_components'].items():
            name = component.replace('_', ' ').title()
            html += f"""<div class="component">
<strong>{name}:</strong> {details['score']}/{details['max']} - {details['reason']}
</div>"""
        
        html += f"""
<div class="key-insight"><strong>Key Insight:</strong><br>{stock['key_insight']}</div>
<div class="trade-setup">
<strong>Trade Setup:</strong><br>
• Strategy: {stock['trade_setup']['strategy']}<br>
• Strikes: {stock['trade_setup']['strikes']}<br>
• Premium: {stock['trade_setup']['premium_target']}<br>
• Return: {stock['trade_setup']['annualized_return']}
</div>
<div class="risk"><strong>Risks:</strong><ul>"""
        
        for risk in stock['risk_factors']:
            html += f"<li><strong>{risk['risk']}:</strong> {risk['impact']} → {risk['probability']}</li>"
        
        html += f"""</ul></div>
<p><strong>Bottom Line:</strong> {stock['bottom_line']}</p>
<hr style="margin: 30px 0;">"""
    
    html += "</body></html>"
    return html

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 generate_report.py analysis_2026-02-18.json")
        sys.exit(1)
    print(generate_html_report(sys.argv[1]))
