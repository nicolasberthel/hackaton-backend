aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 219757291726.dkr.ecr.us-west-2.amazonaws.com
docker build -t wth/g2-backend .
docker tag wth/g2-backend:latest 219757291726.dkr.ecr.us-west-2.amazonaws.com/wth/g2-backend:latest
docker push 219757291726.dkr.ecr.us-west-2.amazonaws.com/wth/g2-backend:latest