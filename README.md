# weekly_tool

+ ## 使用

`仅支持 python3.6+ `

```
wt add -p : 添加 git 仓库路径
wt add -e : 添加发送与收件邮箱（同一个邮箱/目前只支持腾讯企业邮箱）
wt add -k : 添加腾讯企业邮箱授权码
wt start    : 开始任务
```

+ ## 启动定时任务
`weekly_tool` 会在用户主目录下生成定时任务文件 `.weekly_cron`，此文件指向同目录下的 `cron_job.sh`，需要修改此文件中的命令行  `/.../wt`，指向本地 wt 安装的目录


```shell
执行定时任务
sudo crontab -u [用户名] [.weekly_cron 绝对路径]
sudo crontab /etc/init.d/cron restart
```
