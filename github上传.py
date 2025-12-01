import subprocess
import os

def run_command(command):
    """执行终端命令并打印输出"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)

def git_upload():
    # 获取用户输入
    repo_url = input("请输入远程仓库的 URL: ")
    commit_message = input("请输入提交信息: ")

    # 检查当前目录是否是 git 仓库
    if not os.path.exists(".git"):
        print("当前目录不是一个 Git 仓库，正在初始化...")
        run_command("git init")

    # 移除已有的远程仓库
    run_command("git remote remove origin")

    # 添加新的远程仓库
    run_command(f"git remote add origin {repo_url}")

    # 添加所有文件到暂存区
    run_command("git add .")

    # 提交文件
    run_command(f'git commit -m "{commit_message}"')

    # 推送到主分支（默认分支：main）
    run_command("git push -u origin main")  # 如果是 master 分支，可以替换为 `master`

if __name__ == "__main__":
    git_upload()
