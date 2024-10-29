#!/bin/bash

docker build -t vehicle_registration .

docker tag vehicle_registration:latest 741448946628.dkr.ecr.us-east-1.amazonaws.com/vehicle_registration:latest

docker push 741448946628.dkr.ecr.us-east-1.amazonaws.com/vehicle_registration:latest

sam build -t Infrastructure/template.yaml

sam deploy --config-file Infrastructure/samconfig.toml --profile jeremi-profile --image-repository 741448946628.dkr.ecr.us-east-1.amazonaws.com/vehicle_registration