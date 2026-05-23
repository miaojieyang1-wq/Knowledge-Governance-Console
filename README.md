# Knowledge Governance Console

独立的知识治理控制台，用于注册、审计、追溯和回流知识库质量问题。控制台使用本地 SQLite 数据库，不依赖也不嵌入任何 AI 运营分身 Agent 代码。

## 功能

- 知识单元注册中心
- 知识库健康度仪表盘
- 知识清单筛选
- 责任归属与错误追溯工作台
- Badcase 回流与审核看板
- YAML 同步转译，将生效知识导出到 `sync/`

## 启动

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows 本地也可以直接双击 `KnowledgeGovernanceConsole.exe`，或双击 `start_knowledge_console.bat`。两种方式都会读取 `config.yaml` 中的 `launch_host`、`launch_port` 和 `launch_timeout_seconds`，也支持同名 `KG_` 环境变量覆盖；如果端口被占用会自动尝试后续端口，启动记录会写入 `launcher.log` 便于排查。

默认数据库文件：

- `data/knowledge_base.db`

可在 `config.yaml` 中调整数据目录、数据库文件名和待验证告警阈值。

同名环境变量会覆盖 `config.yaml`：`KG_DATA_DIR`、`KG_DATABASE_FILE`、`KG_PENDING_VERIFY_THRESHOLD`、`KG_SYNC_DIR`、`KG_LAUNCH_HOST`、`KG_LAUNCH_PORT`、`KG_LAUNCH_TIMEOUT_SECONDS`。

## 同步转译

控制台只负责将 SQLite 中的结构化知识单元转译为 YAML 文件，不调用 ChromaDB，也不修改 Agent 代码。下游 Agent 的索引脚本可扫描 `sync/` 文件夹中的 `.yaml` 文件并自行完成向量化。

## 自检

运行快速冒烟测试：

```powershell
python selfcheck.py
```

Windows 本地也可以双击 `run_selfcheck.bat`。自检会在临时目录创建隔离数据库和同步目录，不会修改正式数据。
