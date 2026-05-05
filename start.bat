@echo off
echo ========================================
echo AI智能体工作流服务 - 启动脚本
echo ========================================
echo.

cd /d %~dp0

echo [1/3] 清理项目...
call mvn clean
if errorlevel 1 (
    echo 清理失败！
    pause
    exit /b 1
)

echo.
echo [2/3] 编译项目...
call mvn package -DskipTests
if errorlevel 1 (
    echo 编译失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 启动服务...
echo.
echo ========================================
echo 服务即将启动，请稍候...
echo API地址: http://localhost:8080/api/ai-agent
echo 健康检查: http://localhost:8080/api/ai-agent/health
echo ========================================
echo.

java -Djava.rmi.server.useCodebaseOnly=false ^
     -Dcom.sun.management.jmxremote=false ^
     -Dspring.jmx.enabled=false ^
     -jar target/ai-agent.jar

pause
