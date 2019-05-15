#!/usr/bin/env python
# coding: utf-8

import re
import os
import sys
import smtplib
import datetime
import linecache
import subprocess
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


home = os.path.expanduser('~')
if not os.path.exists('%s/.weekly/' % home):
        os.makedirs('%s/.weekly/' % home, mode=0o777)


'''
创建仓库记录文件
'''
git_repos = "%s/.weekly/.git_repos" % home
if not os.path.exists(git_repos):
    os.mknod(git_repos, mode=0o777)

'''
创建仓库作者
'''
git_author = "%s/.weekly/.git_author" % home
if not os.path.exists(git_repos):
    os.mknod(git_repos, mode=0o777)

'''
创建发送邮件文件
'''
send_email = "%s/.weekly/.send_email" % home
if not os.path.exists(send_email):
    os.mknod(send_email, mode=0o777)


'''
创建定时任务文件脚本
'''
cron_job = "%s/.weekly/cron_job.sh" % home
if not os.path.exists(cron_job):
    os.mknod(cron_job, mode=0o777)
    # 脚本内容
    sh = '# !/bin/sh\nsource /etc/profile\nsource ~/.bashrc\n\n/..../wt start'
    with open(cron_job, 'w', encoding='UTF-8') as cron:
        cron.write(sh + '\n')



'''
创建定时任务文件
'''
weekly_cron = "%s/.weekly/.weekly_cron" % home
if not os.path.exists(weekly_cron):
    os.mknod(weekly_cron, mode=0o777)
    # 脚本内容
    sh = 'SHELL=/bin/bash\nPATH=/sbin:/bin:/usr/sbin:/usr/bin\n\n30  20  *  *  6  ~/.weekly/cron_job.sh'
    with open(weekly_cron, 'w', encoding='UTF-8') as cron:
        cron.write(sh + '\n')



'''
邮箱验证
'''
email_re=r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'


def add():
    args = sys.argv[1:]
    if len(args) == 0:
        pass
    else:
        cmd = args[0]
        if 'add' == cmd:
            num_args = len(args)
            if num_args > 1:
                sub_cmd = args[1]
                if '-p' == sub_cmd:
                    # 执行添加 repo 路径
                    for i in range(2, len(args)):
                        path = args[i]
                        if is_git_repo(path):
                            record_git_repo(path)
                elif '-e' == sub_cmd:
                    # 添加邮箱
                    email = args[2]
                    if email and re.match(email_re, email):
                        add_email_arg(email)
                elif '-k' == sub_cmd:
                    # 添加邮箱授权码
                    code = args[2]
                    if code:
                        add_email_arg(code)
                    pass
            else:
                print('should follow -p or -t or -k')
        elif 'start' == cmd:
            # 执行收集任务
            start()
        elif '-l' == cmd:
            # 打印当前记录的 repos
            print_repos()
        elif '--help' == cmd:
            # 打印帮助文档
            print_help()


def print_help():
    help = '''
    -p: add a git repo
    -e: a mailbox
    -k: add a verification code
    '''
    print(help)



def print_repos():
    with open(git_repos, 'r', encoding='UTF-8') as repos:
        for repo in repos.readlines():
            print(repo)



def start():
    parse_git_repo()



def parse_git_repo():
    '''
    解析仓库记录文件，并记录最近一周的任务到文件
    '''
    git_user_name = linecache.getline(git_author, 1).replace("\n","")
    git_user_email = linecache.getline(git_author, 2).replace("\n","")

    weekly_task = create_weekly_task()
    with open(git_repos, 'r', encoding='UTF-8') as repos:
        for repo in repos.readlines():
            repo = repo.replace("\n","")
            if is_git_repo(repo):
                record_git_log_weekly(repo, git_user_name, git_user_email, weekly_task)
                pass
    # 发送邮件到邮箱
    send_email_to_tencent(weekly_task)



def record_git_repo(path):
    '''
    添加当前目录到 .git_repos.txt
    '''
    contains = False
    with open(git_repos, 'r', encoding='UTF-8') as txt:
        for line in txt.readlines():
            if path in line:   
                contains = True
                break

    if not contains:
        with open(git_repos, 'a', encoding='UTF-8') as txt:
            txt.write(path + '\n')



def record_git_log_weekly(path, git_user_name, git_user_email, weekly_task):
    '''
    path: 当前仓库目录
    weekly_task: 周报文件
    读取当前仓库的一周内的 log
    '''
    try:
        cmd = 'cd {0} && git log --all --no-merges --author="{1}\\|{2}" --pretty=format:"【task】%'.format(path, git_user_name, git_user_email) + 's 【date】%' + 'ad" --since=1.weeks --date=short'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8')
        with open(weekly_task, 'w', encoding='UTF-8') as logs:
            logs.write(out + '\n')
    except:
        pass



def get_git_author():
    '''
    获取当前仓库的本地提交作者
    只获取 --global user.name & user.email
    '''
    user_name = ''
    user_email = ''
    try:
        cmd_user_name = 'git config --global user.name'
        cmd_user_email = 'git config --global user.email'
        user_name = subprocess.check_output(cmd_user_name, shell=True).decode('utf-8')
        user_email = subprocess.check_output(cmd_user_email, shell=True).decode('utf-8')
    except:
        pass
        
    if user_name and user_email:
        with open(git_author, 'w', encoding='UTF-8') as author:
            author.write(user_name + user_email)
    else:
        print('git --global user.name or user.email 未设置， 请检查')

'''
解析时读取 git config --global user.name & git config --global user.email
'''
get_git_author()


def is_git_repo(path):
    '''
    判断当前目录是否是一个 git 仓库
    '''
    try:
        cmd = 'cd %s && git rev-parse --is-inside-work-tree' % path,
        out = subprocess.check_output(cmd, shell=True).decode('utf-8').replace("\n","")
        if out == 'true':
            return True
        else:
            return False
    except:
        print('[%s] is not a git repo' % path)
        return False




def create_weekly_task():
    '''
    创建本周周报文件 2019_5_11-2019_5_18.task
    '''
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    start_date = today.strftime('%Y_%m_%d')
    end_date = seven_days_ago.strftime('%Y_%m_%d')
    weekly = '%s/.weekly/weekly/' % home
    weekly_task = weekly + '%s-%s.task' % (start_date, end_date)
    if not os.path.exists(weekly):
        os.makedirs(weekly, mode=0o777)
    if not os.path.exists(weekly_task):
        os.mknod(weekly_task)
    return weekly_task



def add_email_arg(email_arg):
    '''
    添加邮箱和授权码
    '''
    if email_arg:
        with open(send_email, 'r', encoding='UTF-8') as email_args:
            contains = False
            for line in email_args.readlines():
                if email_arg == line.replace("\n",""):
                    contains = True
                    break

        if not contains:            
            with open(send_email, 'a', encoding='UTF-8') as email_args:
                email_args.write(email_arg + '\n')



def send_email_to_tencent(weekly_task):
    '''
    发送邮件到腾讯邮箱
    '''
    try:
        # 用户信息
        from_addr = ''
        password = ''
        to_addr = ''
        # 腾讯服务器地址
        smtp_server = 'smtp.exmail.qq.com'

        # 加载邮箱和授权码
        with open(send_email, 'r', encoding='UTF-8') as email_args:
            for line in email_args.readlines():
                line = line.replace("\n","")
                if line and re.match(email_re, line):
                    from_addr = line
                    to_addr = line
                elif line:
                    password = line
        
        if not from_addr or not password or not to_addr:
            print('Please use "wt add -e/-k [xxx]" to add a mailbox and a verification code.')
            return EnvironmentError
        
        text = ''
        # 加载文件内容
        if weekly_task:
            with open(weekly_task, 'r', encoding='UTF-8') as weekly_txt:
                text = weekly_txt.read()
        else:
            print('Please use "wt add -p [path]" to add a git repo.')
            return EnvironmentError

        # 内容初始化，定义内容格式（普通文本，html）
        msg = MIMEText(text, 'plain', 'utf-8')

        # 发件人收件人信息格式化 ，可防空
        lam_format_addr = lambda name, addr: formataddr((Header(name, 'utf-8').encode(), addr))
        # 传入昵称和邮件地址
        msg['From'] = lam_format_addr('weekly_robot', from_addr)
        msg['To'] = lam_format_addr('myself', to_addr)

        # 邮件标题
        msg['Subject'] = Header('周报', 'utf-8').encode()

        # 服务端配置，账密登陆
        server = smtplib.SMTP(smtp_server, 25)

        # 登陆服务器
        server.login(from_addr, password)

        # 发送邮件及退出
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
        pass
    except :
        pass
        
    
