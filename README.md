# A1CTF-Journalist

A1CTF 战地记者！一个监听 A1CTF 平台特定比赛的通知并发送到 QQ 群的自走步兵

## 前置条件

- 一个 QQ 号，并已接入 [Napcat](https://napcat.napneko.icu/)，Napcat 需要开启 HTTP 服务器
- 一个 [A1CTF](https://github.com/carbofish/A1CTF) 的已参赛的账号（可以是管理员，管理员不要求参赛），要能获取到 Notice 的那种

## 快速开始

### Docker

```bash
$ git clone https://github.com/GamerNoTitle/A1CTF-Journalist.git
$ cd A1CTF-Journalist
$ docker build . -t gamernotitle/a1ctf-journalist
$ docker run --name a1ctf-journalist \
	--port 8000:8000 \
  -e PLATFORM_URL=YOUR_PLATFORM_URL_HERE \
  -e PLATFORM_LISTENING_GAME_ID=YOUR_GAMEID_HERE \
  -e PLATFORM_USERNAME=YOUR_USERNAME_HERE \
  -e PLATFORM_PASSWORD=YOUR_PASSWORD_HERE \
  gamernotitle/a1ctf-journalist
```

| 变量名                     | 说明                           | 必填   | 默认值      |
| -------------------------- | ------------------------------ | ------ | ----------- |
| HOST                       | 监听的地址                     | ✕      | `127.0.0.1` |
| PORT                       | 监听的端口                     | ✕      | `8000`      |
| PLATFORM_URL               | A1CTF 平台地址                 | ✓      |             |
| PLATFORM_LISTENING_GAME_ID | A1CTF 平台中要监听的比赛的 ID  | ✓      |             |
| PLATFORM_USERNAME          | A1CTF 平台的登录账号           | 视情况 |             |
| PLATFORM_PASSWORD          | A1CTF 平台的登录账号对应的密码 | 视情况 |             |
| PLATFORM_COOKIE            | A1CTF 平台的 Cookie            | 视情况 |             |

其中，如果填写了 `PLATFORM_USERNAME` 和 `PLATFORM_PASSWORD` 的话，则会自动更新 Cookie，而无需再填入 `PLATFORM_COOKIE`；反之，如果只填写了 `PLATFORM_COOKIE`，则在 Cookie 有效期内可用，过期则需要重新更新 Cookie

### 源码启动

复制一份 `.example.env` 并命名为 `.env`，填写里面的配置

```env
HOST=127.0.0.1
PORT=8000

PLATFORM_URL=YOUR_PLATFORM_URL_HERE
PLATFORM_LISTENING_GAME_ID=1
PLATFORM_USERNAME=YOUR_USERNAME_HERE
PLATFORM_PASSWORD=YOUR_PASSWORD_HERE
PLATFORM_COOKIE=YOUR_COOKIE_HERE

TARGET_GROUPS=["114514"]
```

- `HOST`: Websocket 监听的地址
- `PORT`: Websocket 监听的端口
- `PLATFORM_URL`：A1CTF 平台的 URL，例如 `https://ctf.bili33.top`
- `PLATFORM_LISTENING_GAME_ID`：监听的比赛 id，在对应比赛的地址栏有的，例如地址为 `https://ctf.bili33.top/games/3/info`，那么 id 就是 `3`
- `PLATFORM_USERNAME`：平台登录用户名/邮箱
- `PLATFORM_PASSWORD`：平台登录密码
- `PLATFORM_COOKIE`：你的账户 Cookie，可以用 Devtool 抓，该账户必须为监听目标比赛的参赛选手或者是平台管理员（如果填写了用户名和密码这里可以不填）

配置完成后直接运行 `app.py` 即可

## 对接 Napcat

根据上方的启动方式，假定你已经知道了 `HOST` 和 `PORT`

在 Napcat 的网络配置中，新建一个 WebSocket 客户端，名称根据自己需要填写，URL 填写 `ws://HOST:PORT/ws`，token 任意，然后保存即可

## 指令

目前有如下指令

- `!!help`/`!!h` 获取帮助信息
- `!!rank`/`!!r` 获取排行榜信息
  - 后面不跟任何内容时，获取排行榜前 10 的团队及其分数
  - 后面跟单个数字，格式为 `!!rank N` 时，获取排行榜前 N 的团队及其分数
  - 后面跟特定格式，格式为 `!!rank start:end` 时，获取从第 start 名到第 end 名的团队及其分数
- `!!challenge`/`!!c` 获取题目的当前分数和解题情况
  - 后面固定跟 `all` ，例如 `!!c all` 时，获取所有题目
  - 后面跟任意字符串，如 `!!c test` 时，获取所有题目名称中含有 `test` 字样的题目，采用 `lower` 处理后包含匹配
- `!!about` 获取 A1CTF-Journalist 的关于信息

## Screenshot

![](https://cdn.bili33.top/gh/GamerNoTitle/A1CTF-Journalist/img/QQ_KaRwnpc54v.png)

## Credit

- A1CTF：https://github.com/carbofish/A1CTF
- Napcat：https://napcat.napneko.icu/
- @Phrinky: https://github.com/Ricky8955555

## Other

临时撸的，因为这边比赛快开始了，就随手弄了一个，主打一个能用就行，不喜勿喷，随便改
