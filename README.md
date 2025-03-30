# 考试刷题系统

一个基于 PyQt5 的现代化考试刷题系统，支持题库导入、答题记录、错题复习等功能。

## 功能特点

- 🔐 安全的用户认证系统
- 📚 支持多种题库格式导入（包括 Excel、CSV、TXT）
- 🎯 实时答题反馈与解析
- 📊 答题数据可视化统计
- 💾 云端同步答题记录
- 📝 智能错题集管理
- 🌈 支持自定义主题
- 🔄 定期自动更新题库

## 系统要求

- Windows 10/11 操作系统（推荐）
- Python 3.8+ 
- 4GB 及以上内存
- 1GB 可用磁盘空间
- 稳定的网络连接

## 快速开始

1. 克隆仓库
```bash
git clone https://github.com/AAASS554/shati.git
cd shati
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python main.py
```

## 项目结构

```
├── src/                # 源代码目录
│   ├── ui/            # 界面相关代码
│   ├── core/          # 核心业务逻辑
│   ├── database/      # 数据库操作
│   └── utils/         # 工具函数
├── tests/             # 测试用例
├── docs/              # 文档
├── requirements.txt   # 项目依赖
└── README.md          # 项目说明
```

## 技术栈

- Python 3.12
- PyQt5 - GUI 框架
- SQLite/MySQL - 数据存储
- requests - 网络请求
- pandas - 数据处理
- pytest - 单元测试

## 开发指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 作者

- 作者：记得晚安
- 邮箱：[你的邮箱]
- 微信：Hatebetray_

## 版权说明

© 2024 记得晚安. 保留所有权利。

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 更新日志

### v2.2.0 (2024-03-xx)

- ✨ 新增题库导入进度显示
- 🎨 优化用户界面交互
- 🐛 修复题目切换延迟问题
- 📦 重构数据库连接池

## 参与贡献

1. 提交 Issue 讨论新特性
2. 提交 Pull Request
3. 完善文档说明
4. 分享使用经验

## 致谢

感谢所有为这个项目做出贡献的开发者们！

## 获取帮助

如需帮助或报告问题，请：

- 提交 [Issue](https://github.com/AAASS554/考试刷题系统/issues)
- 通过邮箱联系：[你的邮箱]
- 添加作者微信：Hatebetray_
