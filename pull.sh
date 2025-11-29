#!/bin/bash
# pull.sh - veilig pull script met branch selectie

set -e  # stop bij fouten

echo "== Test verbinding met GitHub =="
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"
if [ $? -eq 0 ]; then
  echo "✅ Verbinding met GitHub werkt"
else
  echo "❌ Verbinding met GitHub mislukt"
  exit 1
fi

# Check of er lokale commits zijn
if [ -n "$(git log origin/main..main)" ]; then
  echo "⚠️ Er zijn lokale commits die verloren gaan bij reset!"
  echo "Wil je doorgaan? (y/n)"
  read answer
  if [ "$answer" != "y" ]; then
    exit 1
  fi
fi

echo "== Ophalen van beschikbare branches =="
git fetch origin
git reset --hard origin/main

echo "Beschikbare remote branches:"
git branch -r | grep -v 'HEAD' | sed 's/origin\///' | sort | uniq

echo
read -p "Welke branch wil je pullen? " BRANCH

if [ -z "$BRANCH" ]; then
  echo "❌ Geen branch opgegeven, stoppen..."
  exit 1
fi

# Check of de branch lokaal al bestaat
if git show-ref --verify --quiet refs/heads/$BRANCH; then
  echo "== Lokale branch '$BRANCH' bestaat al, overschakelen..."
  git checkout "$BRANCH"
else
  echo "== Lokale branch '$BRANCH' bestaat nog niet, aanmaken..."
  git checkout -b "$BRANCH" "origin/$BRANCH"
fi

echo "== Pull uitvoeren van origin/$BRANCH =="
git pull origin "$BRANCH"

echo "✅ Klaar: branch '$BRANCH' is bijgewerkt en lokaal beschikbaar."
