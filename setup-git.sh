#!/bin/bash
# setup-git.sh — Automatisch Git + SSH configureren en repo aanmaken

# 1. Update en installeer Git
sudo apt update && sudo apt install git -y

# 2. Stel je naam en e-mail in (pas deze aan!)
git config --global user.name "Stannen"
git config --global user.email "stanknippers@hotmail.nl"

# 3. Zet standaard branch naar 'main'
git config --global init.defaultBranch main

# 4. Check of een sleutelpad is meegegeven
KEY_PATH=${1:-~/.ssh/id_ed25519}

if [ -f "$KEY_PATH" ]; then
    echo "Gebruik bestaande sleutel: $KEY_PATH"
else
    echo "Geen bestaande sleutel gevonden, genereer nieuwe..."
    ssh-keygen -t ed25519 -C "jouw@email.com" -f ~/.ssh/id_ed25519 -N ""
    KEY_PATH=~/.ssh/id_ed25519
fi

# 5. Start de SSH-agent en voeg je sleutel toe
eval "$(ssh-agent -s)"
ssh-add "$KEY_PATH"

# 6. Toon je publieke sleutel
echo "----- Voeg deze sleutel toe op GitHub (Settings → SSH and GPG keys) -----"
cat "$KEY_PATH.pub"

# 7. Test de verbinding met GitHub
echo "Test verbinding met GitHub..."
ssh -T git@github.com

# 8. Repo setup (bestaand of nieuw project)
PROJECT_DIR=${2:-$(pwd)}
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit

if [ -d ".git" ]; then
    echo "Dit is al een Git repo."
else
    echo "Initialiseer nieuwe Git repo..."
    git init
    if [ "$(ls -A)" ]; then
        echo "Bestaande bestanden gevonden, voeg toe..."
        git add .
        git commit -m "Eerste commit van bestaand project"
    else
        echo "# Nieuw project" > README.md
        git add README.md
        git commit -m "Initieel project met README"
    fi
fi

# 9. Vraag om GitHub gebruikersnaam en stel remote URL in
read -p "Voer je GitHub gebruikersnaam in: " GH_USER
REPO_NAME=$(basename "$PROJECT_DIR")
REPO_URL="git@github.com:${GH_USER}/${REPO_NAME}.git"

if git remote get-url origin > /dev/null 2>&1; then
    echo "Remote bestaat al: $(git remote get-url origin)"
else
    git remote add origin "$REPO_URL"
fi

git branch -M main
git push -u origin main
echo "✅ Repo gekoppeld en gepusht naar $REPO_URL"



