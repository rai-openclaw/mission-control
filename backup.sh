#!/bin/bash
# Mission Control Data Backup Script
# Backs up data files (not code) to ~/backups/

BACKUP_DIR="$HOME/backups"
DATA_DIR="$HOME/mission-control/data"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mission-control-data-$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Error: Data directory not found at $DATA_DIR"
    exit 1
fi

# Create backup
tar -czf "$BACKUP_FILE" -C "$HOME/mission-control" data/

# Check if backup succeeded
if [ $? -eq 0 ]; then
    echo "✅ Backup created: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    
    # Keep only last 30 backups
    cd "$BACKUP_DIR"
    ls -t mission-control-data-*.tar.gz | tail -n +31 | xargs -r rm
    echo "   Cleanup: Kept last 30 backups"
else
    echo "❌ Backup failed"
    exit 1
fi
