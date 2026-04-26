HELP_MSG = """
🛰️ A1CTF Journalist
指令菜单 & 使用指南 

⌨️ [基础指令]
!!help | !!h
   > 显示本帮助信息
!!rank [参数] | !!r
   > !!rank 8 (前 8 名)
   > !!rank 1:5 (1-5 名)
   > !!rank (默认前 10 名)
!!challenge <题目名称|all> | !!c
   > 查询题目分数及解题详情
   > !!challenge all 查询所有题目状态
   > !!challenge 旮旯 game (查询含有「旮旯 game」字样的题目状态)
!!team <队名> | !!t
   > 查询特定队伍的得分与进度
   > !!team Volcano (查询队伍「Volcano」的状态)

⚠️ 数据具有五分钟缓存，请勿频繁查询

💡 [关于系统]
!!about
   > 显示机器人版本及开发信息

🔗 [开源地址]
https://github.com/GamerNoTitle/A1CTF-Journalist
"""

RANK_MAPPING = {1: "🥇", 2: "🥈", 3: "🥉"}

ABOUT_MSG = """
🤖 A1CTF Journalist 战地记者

📡 本工具提供：
• 🚩 赛题一/二/三血及通知的实时播报
• 📊 实时积分榜数据查询
• 🔍 队伍/题目详细状态检索

✨ 让比赛动态触手可及
🔗 Github: https://github.com/GamerNoTitle/A1CTF-Journalist
"""
