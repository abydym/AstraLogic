"""
conversation_manager.py - 会话管理模块

基于 SQLite 的会话和消息管理器，用于 AstraLogic 项目。
"""

__all__ = ["ConversationManager"]

import os
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class ConversationManager:
    """管理会话（conversations）和消息（messages）的 SQLite 存储。"""

    def __init__(self, db_path: str = "data/conversations.db"):
        """
        初始化数据库连接，自动建表。

        Args:
            db_path: 数据库文件路径，相对路径基于当前工作目录。
        """
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info("已创建数据库目录: %s", db_dir)

        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._create_tables()
            logger.info("数据库连接成功: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise

    def _create_tables(self):
        """创建 conversations 和 messages 表（如不存在）。"""
        try:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id              TEXT PRIMARY KEY,
                    title           TEXT NOT NULL,
                    openclaw_session_id TEXT NOT NULL,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active       BOOLEAN DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role            TEXT NOT NULL,
                    content         TEXT NOT NULL,
                    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
            """)
            logger.info("数据表初始化完成")
        except sqlite3.Error as e:
            logger.error("建表失败: %s", e)
            raise

    def close(self):
        """关闭数据库连接。"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("数据库连接已关闭")

    def create_conversation(self, title: str, openclaw_session_id: str) -> str:
        """
        创建新会话。

        Args:
            title: 会话标题。
            openclaw_session_id: 绑定的 OpenClaw session ID。

        Returns:
            新会话的 UUID。
        """
        conv_id = str(uuid.uuid4())
        try:
            self._conn.execute(
                "INSERT INTO conversations (id, title, openclaw_session_id) VALUES (?, ?, ?)",
                (conv_id, title, openclaw_session_id),
            )
            self._conn.commit()
            logger.info("会话已创建: id=%s, title=%s", conv_id, title)
            return conv_id
        except sqlite3.Error as e:
            logger.error("创建会话失败: %s", e)
            raise

    def list_conversations(self) -> list[dict]:
        """
        列出所有会话，按 updated_at 降序。

        Returns:
            包含 id, title, openclaw_session_id, created_at, updated_at, message_count 的字典列表。
        """
        try:
            rows = self._conn.execute("""
                SELECT
                    c.id,
                    c.title,
                    c.openclaw_session_id,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) AS message_count
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("查询会话列表失败: %s", e)
            raise

    def get_conversation(self, conversation_id: str) -> dict:
        """
        获取单个会话信息。

        Args:
            conversation_id: 会话 UUID。

        Returns:
            会话信息字典。

        Raises:
            ValueError: 会话不存在时。
        """
        try:
            row = self._conn.execute(
                "SELECT id, title, openclaw_session_id, created_at, updated_at, is_active "
                "FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"会话不存在: {conversation_id}")
            return dict(row)
        except sqlite3.Error as e:
            logger.error("获取会话失败: %s", e)
            raise

    def rename_conversation(self, conversation_id: str, new_title: str):
        """
        重命名会话。

        Args:
            conversation_id: 会话 UUID。
            new_title: 新标题。

        Raises:
            ValueError: 会话不存在时。
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            cursor = self._conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (new_title, now, conversation_id),
            )
            self._conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"会话不存在: {conversation_id}")
            logger.info("会话已重命名: id=%s -> %s", conversation_id, new_title)
        except sqlite3.Error as e:
            logger.error("重命名会话失败: %s", e)
            raise

    def delete_conversation(self, conversation_id: str):
        """
        删除会话及其所有消息。

        Args:
            conversation_id: 会话 UUID。

        Raises:
            ValueError: 会话不存在时。
        """
        try:
            self._conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            cursor = self._conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            self._conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"会话不存在: {conversation_id}")
            logger.info("会话已删除: %s", conversation_id)
        except sqlite3.Error as e:
            logger.error("删除会话失败: %s", e)
            raise

    def add_message(self, conversation_id: str, role: str, content: str):
        """
        添加消息并自动更新会话的 updated_at。

        Args:
            conversation_id: 会话 UUID。
            role: 'user' 或 'assistant'。
            content: 消息内容。
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            self._conn.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, now),
            )
            self._conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            self._conn.commit()
            logger.debug("消息已添加: conv=%s, role=%s", conversation_id, role)
        except sqlite3.Error as e:
            logger.error("添加消息失败: %s", e)
            raise

    def get_messages(self, conversation_id: str) -> list[dict]:
        """
        获取某会话的所有消息，按 timestamp 升序。

        Args:
            conversation_id: 会话 UUID。

        Returns:
            消息字典列表。
        """
        try:
            rows = self._conn.execute(
                "SELECT id, conversation_id, role, content, timestamp "
                "FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conversation_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("获取消息失败: %s", e)
            raise

    def get_latest_session_id(self) -> Optional[str]:
        """
        获取最近活跃会话的 openclaw_session_id。

        Returns:
            session ID 字符串，无会话时返回 None。
        """
        try:
            row = self._conn.execute(
                "SELECT openclaw_session_id FROM conversations "
                "WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
            return row["openclaw_session_id"] if row else None
        except sqlite3.Error as e:
            logger.error("获取最新 session ID 失败: %s", e)
            raise

    def auto_title(self, conversation_id: str, first_message: str):
        """
        用首条消息的前30个字符自动设置标题。

        Args:
            conversation_id: 会话 UUID。
            first_message: 首条消息内容。
        """
        title = first_message[:30]
        if len(first_message) > 30:
            title += "..."
        self.rename_conversation(conversation_id, title)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    test_db = "data/test_conversations.db"

    if os.path.exists(test_db):
        os.remove(test_db)

    mgr = ConversationManager(db_path=test_db)
    print("OK - database initialized")

    # 1. create conversation
    cid = mgr.create_conversation("test session", "session-001")
    print(f"OK - create conversation: {cid}")

    # 2. add messages
    mgr.add_message(cid, "user", "hello, this is a test message.")
    mgr.add_message(cid, "assistant", "hi! how can i help you?")
    print("OK - add messages")

    # 3. get messages
    messages = mgr.get_messages(cid)
    assert len(messages) == 2
    print(f"OK - get messages: {len(messages)}")

    # 4. list conversations
    convs = mgr.list_conversations()
    assert len(convs) == 1
    assert convs[0]["message_count"] == 2
    print(f"OK - list conversations: {len(convs)}, msg_count={convs[0]['message_count']}")

    # 5. get single conversation
    conv = mgr.get_conversation(cid)
    assert conv["title"] == "test session"
    print(f"OK - get conversation: {conv['title']}")

    # 6. rename
    mgr.rename_conversation(cid, "new title")
    conv = mgr.get_conversation(cid)
    assert conv["title"] == "new title"
    print(f"OK - rename: {conv['title']}")

    # 7. auto_title
    cid2 = mgr.create_conversation("temp", "session-002")
    long_msg = "a" * 50  # 50 chars, should be truncated
    mgr.auto_title(cid2, long_msg)
    conv2 = mgr.get_conversation(cid2)
    assert conv2["title"].endswith("...")
    assert len(conv2["title"]) == 33  # 30 + "..."
    print(f"OK - auto_title: '{conv2['title']}'")

    # 8. get_latest_session_id
    sid = mgr.get_latest_session_id()
    assert sid == "session-002"
    print(f"OK - latest session id: {sid}")

    # 9. delete
    mgr.delete_conversation(cid)
    convs = mgr.list_conversations()
    assert len(convs) == 1
    print(f"OK - after delete: {len(convs)} conversations")

    # 10. close and cleanup
    mgr.close()
    os.remove(test_db)
    print("\nAll tests passed!")
