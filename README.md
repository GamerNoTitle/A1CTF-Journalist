# A1CTF-Journalist

A1CTF 战地记者！一个监听 A1CTF 平台特定比赛的通知并发送到 QQ 群的自走步兵

## 前置条件

- 一个 QQ 号，并已接入 [Napcat](https://napcat.napneko.icu/)，Napcat 需要开启 HTTP 服务器
- 一个 [A1CTF](https://github.com/carbofish/A1CTF) 的已参赛的账号（可以是管理员，管理员不要求参赛），要能获取到 Notice 的那种

## 快速开始

复制一份 `.example.env` 并命名为 `.env`，填写里面的配置

```env
NAPCAT_URL=YOUR_NAPCAT_URL_HERE
NAPCAT_TOKEN=YOUR_NAPCAT_TOKEN_HERE

PLATFORM_URL=YOUR_PLATFORM_URL_HERE
PLATFORM_LISTENING_GAME_ID=1
PLATFORM_COOKIE=a1token=YOUR_COOKIE_HERE

TARGET_GROUPS=["114514"]
```

- `NAPCAT_URL`：你的 Napcat HTTP 服务器的 URL，例如 `http://localhost:3000`
- `NAPCAT_TOKEN`：上述服务器对应的 token，新建服务器的时候给的
- `PLATFORM_URL`：A1CTF 平台的 URL，例如 `https://ctf.bili33.top`
- `PLATFORM_LISTENING_GAME_ID`：监听的比赛 id，在对应比赛的地址栏有的，例如地址为 `https://ctf.bili33.top/games/3/info`，那么 id 就是 `3`
- `PLATFORM_COOKIE`：你的账户 Cookie，用 Devtool 抓，该账户必须为监听目标比赛的参赛选手或者是平台管理员

配置完成后直接运行 `app.py` 即可

## Credit

- A1CTF：https://github.com/carbofish/A1CTF
- Napcat：https://napcat.napneko.icu/

## Other

临时撸的，因为这边比赛快开始了，就随手弄了一个，主打一个能用就行，不喜勿喷，随便改
