@echo off
setlocal enabledelayedexpansion

REM Load configuration
if not exist "deploy-config.bat" (
    echo [ERROR] deploy-config.bat not found!
    echo Please create it from the template.
    pause
    exit /b 1
)

call deploy-config.bat

echo ==========================================
echo Starting deployment to ECS...
echo ==========================================
echo.
echo Configuration:
echo   Region: %AWS_REGION%
echo   Account: %AWS_ACCOUNT_ID%
echo   Repository: %ECR_REPO%
echo   Cluster: %CLUSTER_NAME%
echo   Service: %SERVICE_NAME%
echo.

REM Check if configuration is set
if "%AWS_ACCOUNT_ID%"=="YOUR_ACCOUNT_ID" (
    echo [ERROR] Please edit deploy-config.bat with your AWS settings!
    pause
    exit /b 1
)

REM Step 1: Build Docker image
echo ==========================================
echo Step 1: Building Docker image...
echo ==========================================
docker build -t %ECR_REPO%:%IMAGE_TAG% .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed!
    pause
    exit /b 1
)
echo [OK] Docker image built successfully
echo.

REM Step 2: Test image locally
echo ==========================================
echo Step 2: Testing image locally...
echo ==========================================
echo Starting test container...
docker run -d -p 8000:80 --name encevo-test %ECR_REPO%:%IMAGE_TAG% >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container!
    pause
    exit /b 1
)

echo Waiting for container to start...
timeout /t 5 /nobreak >nul

REM Test status endpoint
curl -s http://localhost/status | findstr "OK" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Local test passed - Status endpoint responding
) else (
    echo [ERROR] Local test failed! Status endpoint not responding
    docker logs encevo-test
    docker stop encevo-test >nul 2>&1
    docker rm encevo-test >nul 2>&1
    pause
    exit /b 1
)

REM Cleanup test container
docker stop encevo-test >nul 2>&1
docker rm encevo-test >nul 2>&1
echo.

REM Step 3: Login to ECR
echo ==========================================
echo Step 3: Logging in to ECR...
echo ==========================================
set "ECR_URI=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com"

for /f "tokens=*" %%a in ('aws ecr get-login-password --region %AWS_REGION%') do set "ECR_PASSWORD=%%a"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to get ECR password
    echo Make sure AWS CLI is configured with valid credentials
    pause
    exit /b 1
)

echo %ECR_PASSWORD% | docker login --username AWS --password-stdin %ECR_URI% >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ECR login failed!
    pause
    exit /b 1
)
echo [OK] Logged in to ECR
echo.

REM Step 4: Tag and push image
echo ==========================================
echo Step 4: Pushing image to ECR...
echo ==========================================
set "FULL_IMAGE_NAME=%ECR_URI%/%ECR_REPO%:%IMAGE_TAG%"

docker tag %ECR_REPO%:%IMAGE_TAG% %FULL_IMAGE_NAME%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to tag image
    pause
    exit /b 1
)

echo Pushing to %FULL_IMAGE_NAME%...
docker push %FULL_IMAGE_NAME%
if %errorlevel% neq 0 (
    echo [ERROR] Push to ECR failed!
    pause
    exit /b 1
)
echo [OK] Image pushed to ECR
echo.

REM Step 5: Update ECS service
echo ==========================================
echo Step 5: Updating ECS service...
echo ==========================================
aws ecs update-service --cluster %CLUSTER_NAME% --service %SERVICE_NAME% --force-new-deployment --region %AWS_REGION% >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ECS service update failed!
    echo Make sure the cluster and service names are correct
    pause
    exit /b 1
)
echo [OK] ECS service update initiated
echo.

REM Step 6: Wait for deployment
echo ==========================================
echo Step 6: Waiting for deployment to complete...
echo ==========================================
echo This may take a few minutes...
echo.

aws ecs wait services-stable --cluster %CLUSTER_NAME% --services %SERVICE_NAME% --region %AWS_REGION%
if %errorlevel% equ 0 (
    echo [OK] Deployment completed successfully!
) else (
    echo [ERROR] Deployment timed out or failed
    echo Check ECS console for details
    pause
    exit /b 1
)

REM Summary
echo.
echo ==========================================
echo Deployment Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Check your ALB endpoint to verify the application
echo 2. Test the status endpoint: curl http://^<alb-dns^>/status
echo 3. View logs in CloudWatch: %LOG_GROUP%
echo.
echo To view service status:
echo   aws ecs describe-services --cluster %CLUSTER_NAME% --services %SERVICE_NAME% --region %AWS_REGION%
echo.
echo To view task logs:
echo   aws logs tail %LOG_GROUP% --follow --region %AWS_REGION%
echo.

pause
