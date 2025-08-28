#!/bin/bash
# Script to complete the rebase when terminal access is restored

echo "Checking git status..."
git status

echo "Attempting to continue rebase..."
if git rebase --continue; then
    echo "✅ Rebase completed successfully!"
else
    echo "⚠️  Rebase continuation failed. Trying alternative approach..."
    
    # Check if we're still in rebase state
    if [ -d ".git/rebase-merge" ]; then
        echo "Still in rebase state. Aborting and restarting..."
        git rebase --abort
    fi
    
    echo "Restarting rebase from main..."
    git rebase main
fi

echo "Final status:"
git status
git log --oneline -n 5