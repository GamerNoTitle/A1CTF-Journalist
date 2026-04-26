HELP_MSG = """
========== A1CTF Journalist ==========
Usage:
!!help - 显示本帮助信息
!!rank (limit=10)/(start:end) - 显示排行榜前 N 名的队伍（默认 N=10），或显示指定排名区间的队伍
!!challenge <name|all> - 显示对应的题目当前分数以及解题情况，使用 all 来查询所有题目
!!team <name> - 查询对应队伍的当前得分和解题情况
!!about - 显示关于信息

Alias:
!!h -> !!help
!!r -> !!rank
!!c -> !!challenge
!!t -> !!team

https://github.com/GamerNoTitle/A1CTF-Journalist
======================================
"""

RANK_MAPPING = {1: "🥇", 2: "🥈", 3: "🥉"}

ABOUT_MSG = """
A1CTF Journalist 战地记者，提供前三血播报服务和各项查询功能
查看命令使用方式，请使用 !!help 获取帮助

Github: https://github.com/GamerNoTitle/A1CTF-Journalist
"""
