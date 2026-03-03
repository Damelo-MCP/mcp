#!/bin/bash
set -e

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 727646507402.dkr.ecr.us-east-1.amazonaws.com

docker build -t damelo_bot .

docker tag damelo_bot:latest 727646507402.dkr.ecr.us-east-1.amazonaws.com/damelo_bot:latest

docker push 727646507402.dkr.ecr.us-east-1.amazonaws.com/damelo_bot:latest