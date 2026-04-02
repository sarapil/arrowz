#!/bin/bash
# Script to rename ContactCall app

OLD_APP="contactcall"
NEW_APP="${1:-$(echo "Enter new app name: " && read name && echo $name)}"

if [ -z "$NEW_APP" ]; then
    echo "Error: No app name provided"
    exit 1
fi

echo "⚠️  This will rename $OLD_APP to $NEW_APP"
echo "⚠️  Make sure to backup first!"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Rename directory
if [ -d "apps/$OLD_APP" ]; then
    mv "apps/$OLD_APP" "apps/$NEW_APP"
    echo "✅ Renamed directory apps/$OLD_APP → apps/$NEW_APP"
else
    echo "❌ Directory apps/$OLD_APP not found"
    exit 1
fi

# Update apps.json
python3 << EOF
import json

with open('apps.json', 'r') as f:
    apps = json.load(f)

for app in apps:
    if app['url'].endswith('/$OLD_APP'):
        app['url'] = app['url'].replace('/$OLD_APP', '/$NEW_APP')
    if app['url'].endswith('/$OLD_APP.git'):
        app['url'] = app['url'].replace('/$OLD_APP.git', '/$NEW_APP.git')

with open('apps.json', 'w') as f:
    json.dump(apps, f, indent=2)

print("✅ Updated apps.json")
EOF

# Run Frappe commands
echo "Running Frappe setup commands..."
bench setup requirements
bench migrate
bench build

echo "✅ Rename complete!"
echo ""
echo "⚠️  Still need to update:"
echo "   - Database DocTypes (if custom)"
echo "   - Workspace configurations"
echo "   - Frontend references (check all .js/.css files)"
