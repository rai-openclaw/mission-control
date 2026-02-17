// Holdings Module
// Self-contained module for portfolio display

const HoldingsModule = {
    loaded: false,
    data: null,
    priceData: null,
    sort: { column: null, direction: 'asc' },
    
    async load() {
        const container = document.getElementById('holdings-view');
        container.innerHTML = '<div class="loading">Loading portfolio...</div>';
        
        try {
            // Load holdings data
            const response = await fetch('data/holdings.json');
            this.data = await response.json();
            
            // Try to load live prices (will fail silently if not available)
            try {
                const priceResponse = await fetch('http://localhost:8080/api/prices');
                if (priceResponse.ok) {
                    const result = await priceResponse.json();
                    this.priceData = result.prices || result;
                }
            } catch (e) {
                console.log('Price API not available');
            }
            
            this.render();
        } catch (error) {
            container.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    },
    
    render() {
        const container = document.getElementById('holdings-view');
        const { formatCurrency, formatNumber, formatPercent } = MissionControl;
        
        // Calculate totals
        let totalValue = 0, totalCost = 0, stockCount = 0, optionCount = 0;
        const stocks = {};
        const options = [];
        
        this.data.accounts.forEach(acc => {
            if (acc.stocks_etfs) {
                acc.stocks_etfs.forEach(s => {
                    stockCount++;
                    const ticker = s.Ticker;
                    if (!stocks[ticker]) {
                        stocks[ticker] = { ticker, shares: 0, cost: 0, accounts: [] };
                    }
                    stocks[ticker].shares += s.Shares || 0;
                    stocks[ticker].cost += s['Cost Basis'] || 0;
                    stocks[ticker].accounts.push({ name: acc.name, shares: s.Shares });
                });
            }
            if (acc.options) {
                acc.options.forEach(o => {
                    optionCount++;
                    options.push({ ...o, account: acc.name });
                });
            }
        });
        
        // Build stock list with calculations
        let stockList = Object.values(stocks).map(s => {
            const costPerShare = s.shares > 0 ? s.cost / s.shares : 0;
            const price = costPerShare; // Fallback if no live price
            const value = s.shares * price;
            const pl = value - s.cost;
            const plPct = s.cost > 0 ? (pl / s.cost) * 100 : 0;
            totalValue += value;
            totalCost += s.cost;
            return { ...s, costPerShare, price, value, pl, plPct };
        });
        
        // Sort
        if (this.sort.column) {
            stockList = this.sortData(stockList, this.sort.column, this.sort.direction);
        }
        
        const totalPL = totalValue - totalCost;
        const totalPLPct = totalCost > 0 ? (totalPL / totalCost) * 100 : 0;
        
        container.innerHTML = `
            <div class="summary-cards">
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Total Value</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">${formatCurrency(totalValue)}</div>
                </div>
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Total P/L</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: ${totalPL >= 0 ? 'var(--positive)' : 'var(--negative)'}">
                        ${formatPercent(totalPLPct)}
                    </div>
                </div>
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Positions</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">${stockCount}</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">${optionCount} options</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Stock Positions</div>
                </div>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase;">
                                <th style="padding: 0.75rem; text-align: left;">Ticker</th>
                                <th style="padding: 0.75rem; text-align: right;">Shares</th>
                                <th style="padding: 0.75rem; text-align: right;">Price</th>
                                <th style="padding: 0.75rem; text-align: right;">Value</th>
                                <th style="padding: 0.75rem; text-align: right;">P/L %</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stockList.map(s => `
                                <tr style="border-top: 1px solid var(--border);">
                                    <td style="padding: 0.75rem; font-weight: 600; color: var(--accent);">${s.ticker}</td>
                                    <td style="padding: 0.75rem; text-align: right;">${formatNumber(s.shares)}</td>
                                    <td style="padding: 0.75rem; text-align: right;">${formatCurrency(s.price)}</td>
                                    <td style="padding: 0.75rem; text-align: right; font-weight: 600;">${formatCurrency(s.value)}</td>
                                    <td style="padding: 0.75rem; text-align: right; color: ${s.plPct >= 0 ? 'var(--positive)' : 'var(--negative)'}">
                                        ${formatPercent(s.plPct)}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },
    
    sortData(data, column, direction) {
        return [...data].sort((a, b) => {
            let va = a[column], vb = b[column];
            if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
            if (va < vb) return direction === 'asc' ? -1 : 1;
            if (va > vb) return direction === 'asc' ? 1 : -1;
            return 0;
        });
    }
};

// Register module
MissionControl.register('holdings', HoldingsModule);
