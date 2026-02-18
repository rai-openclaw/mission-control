# Mission Control - Docker Edition

Portfolio dashboard for options trading and portfolio management.

## Setup

### Prerequisites
- Docker Desktop installed
- Git (optional, for cloning)

### Installation

```bash
# Clone repository
git clone https://github.com/rai-openclaw/mission-control.git
cd mission-control

# Build and start container
docker-compose up -d

# Access dashboard
open http://localhost:8080
```

### Data

Data files are stored locally in `~/mission-control/data/`:
- `holdings.json` - Portfolio positions
- `ideas.json` - Ideas pipeline
- `price_cache.json` - Cached stock prices
- `corporate.json` - Team structure
- `api_usage.json` - API usage tracking

**Note:** Data is NOT included in this repo for privacy. Keep your own backups.

### Commands

```bash
# Check container status
docker ps

# View logs
docker logs mission-control

# Restart
docker-compose restart

# Stop
docker-compose down
```

### Migration History

- **v1.0:** Flask on bare metal
- **v2.0:** Gunicorn WSGI
- **v3.0:** Docker containerization (current)

Previous static hosting attempts (GitHub Pages, Netlify) archived.

## Architecture

```
Docker Container: mission-control
├── Flask Server (port 8080)
│   ├── REST API endpoints
│   ├── Price fetching (Finnhub/Yahoo)
│   └── Portfolio calculations
├── Templates (Jinja2)
├── Data Volume (persistent)
│   └── ~/mission-control/data/
└── Auto-restart: always
```

## License

Private - For personal use only.
