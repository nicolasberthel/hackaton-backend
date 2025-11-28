@echo off
REM Configuration file for deployment
REM Edit these values before running deploy-to-ecs.bat

REM AWS Configuration
set "AWS_REGION=us-west-2"
set "AWS_ACCOUNT_ID=219757291726"

REM ECR Configuration
set "ECR_REPO=enwth/g2-backend"
set "IMAGE_TAG=latest"

REM ECS Configuration
set "CLUSTER_NAME=hackaton-g2"
set "SERVICE_NAME=flask-pandas-task-service-0odlc93r"

