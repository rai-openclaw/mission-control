// Ideas Module
// Kanban board for ideas pipeline

const IdeasModule = {
    loaded: false,
    data: [],
    
    async load() {
        const container = document.getElementById('ideas-view');
        container.innerHTML = '<div class="loading">Loading ideas pipeline...</div>';
        
        try {
            const response = await fetch('data/ideas.json');
            const result = await response.json();
            this.data = result.ideas || [];
            this.render();
            this.loaded = true;
        } catch (error) {
            container.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    },
    
    render() {
        const container = document.getElementById('ideas-view');
        
        // Group by status
        const columns = {
            backlog: this.data.filter(i => i.status === 'backlog'),
            discussing: this.data.filter(i => i.status === 'discussing'),
            approved: this.data.filter(i => i.status === 'approved'),
            in_progress: this.data.filter(i => i.status === 'in_progress'),
            done: this.data.filter(i => i.status === 'done')
        };
        
        const categoryColors = {
            trading: '#f59e0b',
            tech: '#3b82f6',
            personal: '#10b981',
            research: '#8b5cf6'
        };
        
        const totalIdeas = this.data.length;
        const inProgress = columns.in_progress.length;
        const completed = columns.done.length;
        
        container.innerHTML = `
            <style>
                .kanban-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
                .kanban-column { background: var(--bg-secondary); border-radius: 8px; padding: 1rem; }
                .kanban-column h3 { font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem; text-transform: uppercase; }
                .idea-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 1rem; margin-bottom: 0.75rem; cursor: pointer; }
                .idea-card:hover { border-color: var(--accent); }
                .category-tag { font-size: 0.625rem; padding: 0.125rem 0.375rem; border-radius: 4px; text-transform: uppercase; }
                @media (max-width: 768px) { .kanban-container { grid-template-columns: 1fr; } }
            </style>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Total Ideas</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">${totalIdeas}</div>
                </div>
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">In Progress</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent);">${inProgress}</div>
                </div>
                <div class="card" style="text-align: center;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Done</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--positive);">${completed}</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header"><div class="card-title">Ideas Pipeline</div></div>
                
                <div class="kanban-container">
                    <div class="kanban-column">
                        <h3>Backlog (${columns.backlog.length})</h3>
                        ${columns.backlog.map(idea => this.renderIdeaCard(idea, categoryColors)).join('')}
                    </div>
                    <div class="kanban-column">
                        <h3>Discussing (${columns.discussing.length})</h3>
                        ${columns.discussing.map(idea => this.renderIdeaCard(idea, categoryColors)).join('')}
                    </div>
                    <div class="kanban-column">
                        <h3>Approved (${columns.approved.length})</h3>
                        ${columns.approved.map(idea => this.renderIdeaCard(idea, categoryColors)).join('')}
                    </div>
                    <div class="kanban-column">
                        <h3>In Progress (${columns.in_progress.length})</h3>
                        ${columns.in_progress.map(idea => this.renderIdeaCard(idea, categoryColors)).join('')}
                    </div>
                    <div class="kanban-column">
                        <h3>Done (${columns.done.length})</h3>
                        ${columns.done.map(idea => this.renderIdeaCard(idea, categoryColors)).join('')}
                    </div>
                </div>
            </div>
        `;
    },
    
    renderIdeaCard(idea, colors) {
        const color = colors[idea.category] || '#64748b';
        return `
            <div class="idea-card" onclick="alert('${idea.title}\\n\\n${idea.analysis || 'No analysis yet'}')">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <strong style="font-size: 0.9rem;">${idea.title}</strong>
                    <span class="category-tag" style="background: ${color}20; color: ${color};">${idea.category}</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">
                    ${idea.effort} • ${idea.priority} priority
                </div>
            </div>
        `;
    }
};

MissionControl.register('ideas', IdeasModule);
