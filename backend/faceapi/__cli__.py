"""
Face Recognition System CLI 模块

此模块提供命令行接口来启动和管理人脸识别系统。
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn


def dev(args):
    """开发模式启动"""
    print("🚀 启动开发服务器...")
    os.environ.setdefault("USE_MEMORY_DB", "true")  # 默认使用内存数据库
    
    uvicorn.run(
        "faceapi.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        env_file=args.env_file,
    )


def prod():
    """生产模式启动"""
    print("🚀 启动生产服务器...")
    os.environ.setdefault("USE_MEMORY_DB", "false")  # 生产环境建议使用真实数据库
    
    uvicorn.run(
        "faceapi.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="warning",
        env_file=args.env_file,
    )


def main():
    """主命令行接口"""
    parser = argparse.ArgumentParser(description="Face Recognition System CLI")
    parser.add_argument(
        "command",
        choices=["dev", "prod", "serve"],
        help="运行命令: dev(开发模式), prod(生产模式), serve(默认开发模式)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--memory-db",
        action="store_true",
        help="强制使用内存数据库"
    )
    parser.add_argument(
        "-e",
        "--env-file",
        default=".env",
        help="指定环境配置文件路径 (默认: .env)"
    )
    
    args = parser.parse_args()
    
    # 设置环境变量
    if args.memory_db:
        os.environ["USE_MEMORY_DB"] = "true"
    
    # 加载指定的环境文件
    if args.env_file:
        if os.path.exists(args.env_file):
            from dotenv import load_dotenv
            load_dotenv(args.env_file)
            print(f"✅ 已加载环境文件: {args.env_file}")
        else:
            print(f"⚠️  环境文件不存在: {args.env_file}")
    
    if args.command == "dev" or args.command == "serve":
        dev(args)
    elif args.command == "prod":
        prod(args)


if __name__ == "__main__":
    main()