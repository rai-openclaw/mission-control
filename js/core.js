// Mission Control - Core Module System
// Handles view switching and module initialization

const MissionControl = {
    // Registry of loaded modules
    modules: {},
    
    // Register a module
    register(name, module) {
        this.modules[name] = module;
        console.log(`Module registered: ${name}`);
    },
    
    // Switch view
    showView(viewName, event) {
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        if (event && event.target) {
            event.target.classList.add('active');
        }
        
        // Show view container
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        const viewEl = document.getElementById(`${viewName}-view`);
        if (viewEl) {
            viewEl.classList.add('active');
        }
        
        // Load module if registered
        const module = this.modules[viewName];
        if (module && typeof module.load === 'function') {
            if (!module.loaded) {
                module.load();
                module.loaded = true;
            }
        } else {
            console.warn(`Module not found: ${viewName}`);
        }
    },
    
    // Utility: Format currency
    formatCurrency(value) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    },
    
    // Utility: Format number
    formatNumber(value) {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('en-US').format(value);
    },
    
    // Utility: Format percent
    formatPercent(value) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
    },
    
    // Utility: Format date
    formatDate(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }
};

// Make globally available
window.MissionControl = MissionControl;
window.showView = (viewName, event) => MissionControl.showView(viewName, event);

// Initialize default view on page load
document.addEventListener('DOMContentLoaded', () => {
    // Load default view (holdings)
    const defaultModule = MissionControl.modules['holdings'];
    if (defaultModule) {
        defaultModule.load();
        defaultModule.loaded = true;
    }
});
