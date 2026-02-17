// Analysis Module
// Self-contained research archive

const AnalysisModule = {
    loaded: false,
    data: [],
    sort: { column: 'date', direction: 'desc' },
    
    async load() {
        const container = document.getElementById('analysis-view');
        container.innerHTML = '<div class="loading">Loading research archive...</div>';
        
        try {
            // Known analysis files
            const files = ['crm.json', 'hood.json', 'ldi.json', 'rkt.json', 'sofi.json'];
            this.data = [];
            
            for (const file of files) {
                try {
                    const response = await fetch(`data/analyses/${file}`);
                    if (response.ok) {
                        const item = await response.json();
                        this.data.push(item);
                    }
                } catch (e) {
                    console.log(`Could not load ${file}`);
                }
            }
            
            // Sort by date
            this.data.sort((a, b) => new Date(b.date) - new Date(a.date));
            this.render();
            this.loaded = true;
        } catch (error) {
            container.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    },
    
    render() {
        const container = document.getElementById('analysis-view');
        const { formatCurrency, formatPercent, formatDate } = MissionControl;
        
        if (this.data.length === 0) {
            container.innerHTML = '<div class="loading">No analysis data available</div>';
            return;
        }
        
        // Calculate stats
        const avgReturn = this.data.reduce((sum, a) => sum + (a.gain_percent || 0), 0) / this.data.length;
        
        container.innerHTML = `
            <style>
                .grade-A { background: rgba(16, 185, 129, 0.2); color: #10b981; }
                .grade-B { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
                .grade-C { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
                .grade-D, .grade-F { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
                .grade-badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: 600; font-size: 0.875rem; }
                .analysis-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; cursor: pointer; }
                .analysis-card:hover { border-color: var(--accent); }
                @media (max-width: 768px) { .desktop-only { display: none; } }
                @media (min-width: 769px) { .mobile-only { display: none; } }
            </style>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Reports</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">${this.data.length}</div>
                </div>
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Avg Return</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: ${avgReturn >= 0 ? 'var(--positive)' : 'var(--negative)'}">
                        ${formatPercent(avgReturn)}
                    </div>
                </div>
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Latest</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">${this.data[0]?.grade || '-'}</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header"><div class="card-title">Research Archive</div></div>
                
                <!-- Desktop Table -->
                <div class="desktop-only" style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase;">
                                <th style="padding: 0.75rem; text-align: left;">Date</th>
                                <th style="padding: 0.75rem; text-align: left;">Ticker</th>
                                <th style="padding: 0.75rem; text-align: left;">Grade</th>
                                <th style="padding: 0.75rem; text-align: left;">Summary</th>
                                <th style="padding: 0.75rem; text-align: right;">Return</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.data.map(item => `
                                <tr style="border-top: 1px solid var(--border); cursor: pointer;" onclick="alert('${item.ticker}: ${item.summary}')">
                                    <td style="padding: 0.75rem;">${formatDate(item.date)}</td>
                                    <td style="padding: 0.75rem; font-weight: 600; color: var(--accent);">${item.ticker}</td>
                                    <td style="padding: 0.75rem;"><span class="grade-badge grade-${item.grade?.charAt(0)}">${item.grade}</span></td>
                                    <td style="padding: 0.75rem; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.summary}</td>
                                    <td style="padding: 0.75rem; text-align: right; color: ${(item.gain_percent || 0) >= 0 ? 'var(--positive)' : 'var(--negative)'}">
                                        ${formatPercent(item.gain_percent)}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <!-- Mobile Cards -->
                <div class="mobile-only">
                    ${this.data.map(item => `
                        <div class="analysis-card" onclick="alert('${item.ticker}: ${item.summary}')">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="font-weight: 600; color: var(--accent);">${item.ticker}</span>
                                <span class="grade-badge grade-${item.grade?.charAt(0)}">${item.grade}</span>
                            </div>
                            <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">${formatDate(item.date)}</div>
                            <div style="font-size: 0.875rem; margin-bottom: 0.75rem;">${item.summary}</div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: ${(item.gain_percent || 0) >= 0 ? 'var(--positive)' : 'var(--negative)'}">
                                    ${formatPercent(item.gain_percent)}
                                </span>
                                <span style="font-size: 0.75rem; color: var(--text-secondary);">${item.action?.split('—')[0] || ''}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
};

MissionControl.register('analysis', AnalysisModule);
