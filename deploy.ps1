# Docker快速部署脚本 (PowerShell)
# 功能：一键启动、更新代码、重新构建镜像

param(
    [string]$action = "start",
    [switch]$rebuild = $false,
    [switch]$logs = $false
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string]$message, [string]$type = "info")
    $colors = @{
        "success" = "Green"
        "error" = "Red"
        "warning" = "Yellow"
        "info" = "Cyan"
    }
    Write-Host $message -ForegroundColor $colors[$type]
}

function Show-Help {
    Write-Host @"
╔═══════════════════════════════════════════════════════════════╗
║          Proto-SAP Docker 部署脚本                            ║
╚═══════════════════════════════════════════════════════════════╝

用法：
  .\deploy.ps1 [action] [options]

行为：
  start         启动容器（默认）✅
  stop          停止容器
  restart       重启容器
  logs          查看日志
  clean         停止并删除容器与卷
  rebuild       重新构建镜像并启动

选项：
  -rebuild      重新构建后端镜像
  -logs         启动后显示日志

示例：
  .\deploy.ps1                    # 正常启动
  .\deploy.ps1 start -rebuild     # 重新构建并启动
  .\deploy.ps1 logs               # 查看日志
  .\deploy.ps1 stop               # 停止服务
  .\deploy.ps1 clean              # 清理数据

════════════════════════════════════════════════════════════════
"@
}

function Start-Services {
    param([bool]$rebuild = $false)
    
    Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "info"
    Write-Status "1️⃣  启动Docker容器..." "info"
    Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "info"
    
    if ($rebuild) {
        Write-Status "🔨 重新构建镜像..." "warning"
        docker compose up -d --build
    } else {
        docker compose up -d
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ 容器启动成功" "success"
        
        Write-Status ""
        Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "info"
        Write-Status "2️⃣  等待服务就绪（30秒）..." "info"
        Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "info"
        Start-Sleep -Seconds 30
        
        Write-Status ""
        Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "info"
        Write-Status "3️⃣  检查容器状态..." "info"
        Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "info"
        docker ps
        
        Write-Status ""
        Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "success"
        Write-Status "✅ 启动完成！" "success"
        Write-Status "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "success"
        
        Write-Status ""
        Write-Status "🌐 访问地址：" "info"
        Write-Status "   • 前端首页：http://localhost:5000" "info"
        Write-Status "   • 数据库管理：http://localhost:5000/database_management.html" "info"
        Write-Status "   • PDF导入：http://localhost:5000/pdf_import.html" "info"
        
        Write-Status ""
        Write-Status "📋 常用命令：" "info"
        Write-Status "   查看日志：.\deploy.ps1 logs" "info"
        Write-Status "   停止服务：.\deploy.ps1 stop" "info"
        Write-Status "   重启服务：.\deploy.ps1 restart" "info"
        Write-Status "   清理数据：.\deploy.ps1 clean" "info"
    } else {
        Write-Status "❌ 容器启动失败" "error"
        exit 1
    }
}

function Stop-Services {
    Write-Status "⏹️  停止容器..." "warning"
    docker compose down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ 容器已停止" "success"
    } else {
        Write-Status "❌ 停止失败" "error"
        exit 1
    }
}

function Restart-Services {
    Write-Status "🔄 重启容器..." "warning"
    docker compose restart
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ 容器已重启" "success"
        Start-Sleep -Seconds 5
        Write-Status ""
        Write-Status "🌐 服务地址：http://localhost:5000" "info"
    } else {
        Write-Status "❌ 重启失败" "error"
        exit 1
    }
}

function Show-Logs {
    Write-Status "📋 显示日志（按 Ctrl+C 退出）..." "info"
    Write-Status ""
    
    docker compose logs -f
}

function Clean-Services {
    Write-Status "⚠️  警告：将删除容器和数据卷！" "warning"
    Write-Status "此操作会删除数据库数据，谨慎执行！" "warning"
    Write-Status ""
    
    $confirm = Read-Host "确认删除？(y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Write-Status "🗑️  清理中..." "warning"
        docker compose down -v
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ 已清理" "success"
        } else {
            Write-Status "❌ 清理失败" "error"
            exit 1
        }
    } else {
        Write-Status "❌ 已取消" "warning"
    }
}

# 主程序
if ($action -eq "help" -or $action -eq "-h" -or $action -eq "--help") {
    Show-Help
} elseif ($action -eq "start") {
    Start-Services -rebuild $rebuild
    if ($logs) {
        Write-Status ""
        Write-Status "按 Ctrl+C 停止查看日志" "warning"
        Show-Logs
    }
} elseif ($action -eq "stop") {
    Stop-Services
} elseif ($action -eq "restart") {
    Restart-Services
} elseif ($action -eq "logs") {
    Show-Logs
} elseif ($action -eq "clean") {
    Clean-Services
} elseif ($action -eq "rebuild") {
    Start-Services -rebuild $true
    if ($logs) {
        Write-Status ""
        Write-Status "按 Ctrl+C 停止查看日志" "warning"
        Show-Logs
    }
} else {
    Write-Status "❌ 未知的命令: $action" "error"
    Write-Status ""
    Write-Status "使用 .\deploy.ps1 help 查看帮助" "info"
    exit 1
}
