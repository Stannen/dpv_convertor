#!/bin/bash
# push.sh - veilig push script met pull-check

set -e  # stop bij fouten

echo "== Test verbinding met GitHub =="
git ls-remote origin &>/dev/null || {
  echo "❌ Verbinding met GitHub mislukt"
  exit 1
}
echo "✅ Verbinding met GitHub werkt"

# Bepaal huidige branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "⚠️ Je hebt een pull gedaan van 'main'."
  echo "Je mag niet direct committen/pushen op main."
  read -p "Geef een naam voor de nieuwe branch: " NEW_BRANCH
  if [ -z "$NEW_BRANCH" ]; then
    echo "❌ Geen branchnaam opgegeven, stoppen..."
    exit 1
  fi
  git checkout -b "$NEW_BRANCH"
  echo "✅ Nieuwe branch '$NEW_BRANCH' aangemaakt."
  TARGET_BRANCH="$NEW_BRANCH"
else
  TARGET_BRANCH="$CURRENT_BRANCH"
fi

echo "Voer je commit-bericht in:"
read commitmsg

git add .
git commit -m "$commitmsg"

echo "== Push naar branch '$TARGET_BRANCH' =="
git push -u origin "$TARGET_BRANCH"
echo "✅ Code gepusht naar '$TARGET_BRANCH'"
