# OutlookRegister

这个项目是用来批量注册Outlook邮箱的工具。

## 项目结构

```
OutlookRegister/
├── src/
│   ├── main.py          # 主程序入口
│   ├── register.py      # 注册功能模块
│   └── utils.py         # 工具函数
├── config/
│   └── settings.json    # 配置文件
├── data/
│   └── accounts.csv     # 账户信息文件
├── requirements.txt     # Python依赖
└── README.md           # 项目说明文件
```

## 功能说明

- 批量注册Outlook邮箱账号
- 支持自定义用户名和密码
- 支持代理IP设置
- 支持验证码识别

## 使用方法

```bash
pip install -r requirements.txt
python src/main.py
```