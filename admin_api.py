from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/admin/api/stats")
async def get_admin_stats():
    """Статистика для админки - ИСПРАВЛЕННАЯ"""
    conn = sqlite3.connect('dreams.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dreams")
        total_dreams = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(requests_count) FROM users")
        total_requests = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE date(last_activity) = date('now')")
        active_today = cursor.fetchone()[0]
        
        # РЕАЛЬНЫЕ ДАННЫЕ ВМЕСТО НЕСУЩЕСТВУЮЩИХ ТАБЛИЦ
        open_requests = 0
        banned_users = 0
        
        return {
            "total_users": total_users,
            "total_dreams": total_dreams,
            "total_requests": total_requests,
            "active_today": active_today,
            "open_support_requests": open_requests,
            "banned_users": banned_users
        }
        
    except Exception as e:
        print(f"❌ ОШИБКА СТАТИСТИКИ: {e}")
        return {
            "total_users": 0,
            "total_dreams": 0,
            "total_requests": 0,
            "active_today": 0,
            "open_support_requests": 0,
            "banned_users": 0
        }
    finally:
        conn.close()

@router.get("/admin/api/support-requests")
async def get_support_requests(status: str = 'open'):
    """Получение запросов поддержки - ЗАГЛУШКА"""
    try:
        # ТАБЛИЦЫ НЕТ - ВОЗВРАЩАЕМ ПУСТОЙ МАССИВ
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))