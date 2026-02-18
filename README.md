# Mission Control - Docker Edition

Portfolio dashboard for options trading and portfolio management.

## Quick Start

```bash
# Clone repository
git clone https://github.com/rai-openclaw/mission-control.git
cd mission-control

# Build and start container
docker-compose up -d

# Access dashboard
open http://localhost:8080
```

## Migration History

| Version | Status | Notes |
|---------|--------|-------|
| v3.0 (Docker) | ✅ **Current** | Stable, full functionality |
| v2.0 (Gunicorn) | Archived | Bare metal WSGI |
| v1.0 (Flask dev) | Archived | Development server |
| GitHub Pages | ❌ **Deprecated** | 10-min cache, read-only |
| Netlify | ❌ **Deprecated** | Read-only, no edit functionality |

**Why Docker?** Previous static hosting (GitHub Pages, Netlify) failed because they don't support server-side functionality. Docker provides full edit capabilities, live price refresh, and stable deployment.

## Prerequisites

- Docker Desktop installed and running
- macOS/Linux (Windows via WSL2)

## Installation

```bash
# Clone repository
git clone https://github.com/rai-openclaw/mission-control.git
cd mission-control

# Build and start container
docker-compose up -d

# Verify container is running
docker ps

# Access dashboard
open http://localhost:8080
```

## Data Management

### Local Data Directory

Data files are stored locally in `~/mission-control/data/` (NOT in GitHub):

| File | Purpose |
|------|---------|
| `holdings.json` | Portfolio positions across accounts |
| `ideas.json` | Ideas pipeline (Kanban board) |
| `price_cache.json` | Cached stock prices |
| `corporate.json` | Team structure and org chart |
| `api_usage.json` | API usage tracking |
| `schedule.json` | Personal schedule/events |
| `analyses/*.json` | Stock analysis archive |

**Privacy Note:** Data stays on your local machine only. GitHub contains code, not your portfolio data.

### Backup

**Automatic:** Daily backups at 2 AM PT via cron

**Manual:**
```bash
cd ~/mission-control
./backup.sh
```

Backups saved to: `~/backups/mission-control-data-YYYYMMDD_HHMMSS.tar.gz`

### Recovery

If Mac Mini fails:
1. New machine: Install Docker Desktop
2. `git clone https://github.com/rai-openclaw/mission-control.git`
3. Restore data: `tar -xzf backup-file.tar.gz -C ~/mission-control/`
4. `docker-compose up -d`

## Docker Commands

```bash
# Check container status
docker ps

# View logs
docker logs mission-control

# Restart container
docker-compose restart

# Stop container
docker-compose down

# Rebuild after code changes
docker-compose build && docker-compose up -d
```

## Architecture

```
Docker Container: mission-control
├── Flask Server (port 8080)
│   ├── REST API endpoints (/api/*)
│   ├── Price fetching (Finnhub/Yahoo/CoinGecko)
│   ├── Portfolio calculations
│   └── Email sending (SMTP)
├── Templates (Jinja2)
│   └── dashboard.html
├── Static assets (CSS/JS)
├── Data Volume (persistent)
│   └── ~/mission-control/data/  ← Your data lives here
└── Auto-restart: always
```

## Features

- **Holdings Tab:** Portfolio overview with real-time prices
- **Analysis Tab:** Research archive with detailed analysis
- **Earnings Tab:** Earnings calendar and research
- **Ideas Tab:** Kanban board for project ideas
- **Corporate Tab:** Team structure visualization
- **API Usage Tab:** Cost tracking for external APIs

## Configuration

### Environment Variables

Add to `~/.zshrc`:
```bash
# Gmail (for email reports)
export GMAIL_USER="raito09726@gmail.com"
export GMAIL_APP_PASSWORD="your-app-password"

# API Keys
export FINNHUB_API_KEY="your-finnhub-key"
```

### Price Constants

Some assets (like SGOV treasury ETF) use hardcoded prices. Edit `PRICE_CONSTANTS` in `server.py` if needed:
```python
PRICE_CONSTANTS = {
    'SGOV': 100.0,  # iShares 0-3 Month Treasury Bond ETF
}
```

## Troubleshooting

### Container won't start
```bash
# Check port 8080 is free
lsof -i :8080

# View detailed logs
docker logs mission-control

# Force rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Prices showing "Error"
- Click "Refresh Prices" button in dashboard
- Check `FINNHUB_API_KEY` is set
- Verify internet connection

### Data not loading
- Check `~/mission-control/data/` exists
- Verify JSON files are valid: `python3 -m json.tool data/holdings.json`
- Restart container: `docker-compose restart`

## Development

To modify code:
1. Edit files in `~/mission-control/`
2. Rebuild: `docker-compose build && docker-compose up -d`
3. Test changes
4. Commit to GitHub: `git add -A && git commit -m "Description" && git push`

## Support

For issues or questions, check:
- Docker logs: `docker logs mission-control`
- Browser console (F12) for JavaScript errors
- `~/backups/` for data recovery

## License

Private - For personal use only.
