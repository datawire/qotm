#!/bin/bash

set -e

# Don't build on version-tag pushes.
if [ $(echo "$TRAVIS_BRANCH" | egrep -c '^v[0-9][0-9\.]*$') -gt 0 ]; then
    echo "No need to build $TRAVIS_BRANCH"
    exit 0
fi

env | grep TRAVIS | sort

export DOCKER_REGISTRY
ECHO=echo
DRYRUN=yes

if [ -n "$TRAVIS" ]; then
    ECHO=
    DRYRUN=
fi

# Syntactic sugar really...
dryrun () {
    test -n "$DRYRUN"
}

if dryrun; then
    echo "======== DRYRUN"
else
    echo "======== RUNNING"
fi

# Are we on master?
ONMASTER=

if [ \( "$TRAVIS_BRANCH" = "master" \) -a \( "$TRAVIS_PULL_REQUEST" = "false" \) ]; then
    ONMASTER=yes
fi

# Syntactic sugar really...
onmaster () {
    test -n "$ONMASTER"
}

# Do we have any non-doc changes?
echo "======== Diff summary"
git diff --stat "$TRAVIS_COMMIT_RANGE"

changes=$(git diff --name-only "$TRAVIS_COMMIT_RANGE" | wc -l | tr -d ' ')

# Default VERSION to _the current version of Ambassador._
VERSION=$(make version)

echo "========"
echo "Version ${VERSION}; change count ${changes}"
echo "========"

if [ $changes -eq 0 ]; then
    echo "No build needed"
    exit 0
fi

# Are we on master?
if onmaster; then
    # Yes. This is a Real Official Build(tm) -- make sure git is in a sane state...
    git checkout ${TRAVIS_BRANCH}

    # ...and make sure we're interacting with our official Docker repo.
    DOCKER_REGISTRY="datawire"

    set +x
    echo "+docker login..."
    $ECHO docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
    set -x
else
    # We're not on master, so we're not going to push anywhere.
    DOCKER_REGISTRY=-
fi

# OK. Actually build (and maybe push) our Docker image...
$ECHO make

if onmaster; then
    # ...and, if we're on master, tag this version...
    $ECHO git tag -a v$(VERSION) -m "v$(VERSION)"

    # ...and push the tag.
    $ECHO git push --tags https://d6e-automation:${GH_TOKEN}@github.com/datawire/ambassador.git master
else
    # If not on master, don't tag...
    echo "not on master; not tagging"
fi
