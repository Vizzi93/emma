#!/bin/bash
# Release Script für eMMA
# Usage: ./scripts/release.sh [major|minor|patch]

set -e

CURRENT_VERSION=$(cat VERSION)
echo "Aktuelle Version: ${CURRENT_VERSION}"

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

BUMP_TYPE=${1:-patch}

case $BUMP_TYPE in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
  *) echo "Usage: $0 [major|minor|patch]"; exit 1 ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "Neue Version: ${NEW_VERSION}"

read -p "Release v${NEW_VERSION} erstellen? (y/n) " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 0

echo "$NEW_VERSION" > VERSION
git add VERSION
git commit -m "chore: bump version to ${NEW_VERSION}"
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"

read -p "Zu GitHub pushen? (y/n) " -n 1 -r
echo
[[ $REPLY =~ ^[Yy]$ ]] && git push origin main && git push origin "v${NEW_VERSION}"

echo "Release v${NEW_VERSION} abgeschlossen!"
