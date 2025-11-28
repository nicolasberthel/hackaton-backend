# Python REST API

## Setup

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
uvicorn main:app --reload
```

## Docker Build & Run

```bash
docker build -t api .
docker run -p 8000:8000 api
```

## AWS ECS Deployment

1. Build and push to ECR:
```bash
aws ecr get-login-password --region [region] | docker login --username AWS --password-stdin [account-id].dkr.ecr.[region].amazonaws.com
docker build -t api .
docker tag api:latest [account-id].dkr.ecr.[region].amazonaws.com/api:latest
docker push [account-id].dkr.ecr.[region].amazonaws.com/api:latest
```

2. Create ECS task definition and service using the pushed image

## Endpoints

- GET `/status` - Returns "OK"
- GET `/loadcurve/{pod}` - Returns load curve for specified pod
- GET `/mix/{mixId}` - Returns an energy Mix 
