#!/usr/bin/env bash

while sleep 2; do curl "$(minikube service hello-kubernetes --namespace=tutorial --url)/quote"; done
