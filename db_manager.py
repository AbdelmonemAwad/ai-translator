import os
import atexit
import duckdb
import threading

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    _connections = {}
    _db_file = None
    
    @classmethod
    def get_instance(cls, db_file=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_file)
            elif db_file and cls._db_file != db_file:
                # إذا تم تغيير ملف قاعدة البيانات، قم بإغلاق الاتصالات القديمة وإنشاء مدير جديد
                cls._instance.close_all()
                cls._instance = cls(db_file)
            return cls._instance
    
    def __init__(self, db_file):
        self._db_file = db_file
        # تسجيل دالة لإغلاق جميع الاتصالات عند إنهاء البرنامج
        atexit.register(self.close_all)
    
    def get_connection(self, thread_id=None):
        """الحصول على اتصال لسلسلة محددة أو إنشاء اتصال جديد"""
        if thread_id is None:
            thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id not in self._connections or self._connections[thread_id] is None:
                try:
                    conn = duckdb.connect(self._db_file, read_only=False)
                    self._connections[thread_id] = conn
                except Exception as e:
                    print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
                    raise
            
            return self._connections[thread_id]
    
    def close_connection(self, thread_id=None):
        """إغلاق اتصال لسلسلة محددة"""
        if thread_id is None:
            thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id in self._connections and self._connections[thread_id] is not None:
                try:
                    self._connections[thread_id].close()
                    self._connections[thread_id] = None
                except Exception as e:
                    print(f"خطأ في إغلاق اتصال قاعدة البيانات: {e}")
    
    def close_all(self):
        """إغلاق جميع اتصالات قاعدة البيانات"""
        with self._lock:
            for thread_id, conn in list(self._connections.items()):
                if conn is not None:
                    try:
                        conn.close()
                    except Exception as e:
                        print(f"خطأ في إغلاق اتصال قاعدة البيانات: {e}")
            self._connections.clear()

# دالة مساعدة للحصول على اتصال قاعدة البيانات
def get_db_connection(db_file=None):
    if db_file is None:
        # استخدام المسار الافتراضي إذا لم يتم تحديد ملف
        db_file = os.environ.get("DATABASE_FILE", "library.db")
    
    return DatabaseManager.get_instance(db_file).get_connection()

# دالة مساعدة لإغلاق اتصال قاعدة البيانات
def close_db_connection():
    DatabaseManager.get_instance().close_connection()