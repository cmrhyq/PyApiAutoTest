import pymysql
import threading

from common.log import Logger

logger = Logger().get_logger()

class MysqlSingleton:
    _instance = None  # 单例实例
    _lock = threading.Lock()  # 线程安全锁

    def __new__(cls, dbname, user, password, host='localhost', port=3306):
        with cls._lock:  # 确保多线程下只有一个实例
            if cls._instance is None:
                cls._instance = super(MysqlSingleton, cls).__new__(cls)
                cls._instance._initialize(dbname, user, password, host, port)
        return cls._instance

    def _initialize(self, dbname, user, password, host, port):
        """初始化数据库连接"""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None  # 持久化数据库连接

    def get_connection(self):
        """获取数据库连接，确保连接复用"""
        if self.conn is None or self.conn.closed:
            try:
                self.conn = pymysql.connect(
                    database=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
            except pymysql.DatabaseError as e:
                logger.error(f"数据库连接失败: {e}")
                self.conn = None
        return self.conn

    def execute_query(self, sql, params=None):
        """执行数据库查询"""
        conn = self.get_connection()
        if conn is None:
            raise RuntimeError("数据库连接不可用")

        with conn.cursor() as cur:
            try:
                cur.execute(sql, params)
                if cur.description:  # 只查询时返回数据
                    return cur.fetchall()
                conn.commit()  # 插入/更新操作提交
            except pymysql.DatabaseError as e:
                conn.rollback()
                logger.error(f"SQL 执行错误: {e}")
                raise

    def close_connection(self):
        """在测试结束后关闭数据库连接"""
        if self.conn is not None:
            self.conn.close()
            self.conn = None  # 清空连接实例

# 使用示例
if __name__ == "__main__":
    db = MysqlSingleton(dbname="test", user="root", password="Hyq0901.")

    # 执行查询
    result = db.execute_query("SELECT * FROM users WHERE id = %s", (1,))
    print(result)

    db.close_connection()  # 关闭数据库连接