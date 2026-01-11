import json
import os
from datetime import datetime

context = {
    "last_update": datetime.now().isoformat(),
    "infrastructure": {
        "node": "INF",
        "memory_status": "8GB (4GB Physical + 4GB Swap) - ✅ VERIFIED",
        "services": ["TimescaleDB", "JupyterLab (Port 8888)"]
    },
    "data_ingestion": {
        "status": "COLD_PATH_ACTIVE",
        "assets": ["AAPL.US (11361 rows)", "TSLA.US (3908 rows)"]
    },
    "cross_node_sync": {
        "HUB": "Synced",
        "GTW": "Synced (psycopg2/sqlalchemy verified)"
    },
    "task_history": ["#092.1", "#092.2", "#092.3"]
}

os.makedirs("docs/context", exist_ok=True)
with open("docs/context/task_092_snapshot.json", "w") as f:
    json.dump(context, f, indent=4)

print("✅ Task #092 Context Snapshot generated at docs/context/task_092_snapshot.json")
