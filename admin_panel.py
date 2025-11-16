# admin_panel.py - РАСШИРЕННАЯ АДМИН-ПАНЕЛЬ

from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.get("/admin/api/extended-stats")
async def get_extended_admin_stats():
    """Расширенная статистика для админки"""
    conn = sqlite3.connect('dreams.db')
    cursor = conn.cursor()
    
    try:
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')")
        new_users_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) >= date('now', '-7 days')")
        new_users_week = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) >= date('now', '-30 days')")
        new_users_month = cursor.fetchone()[0]
        
        # Активность
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE date(last_activity) = date('now')")
        dau = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE date(last_activity) >= date('now', '-7 days')")
        wau = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE date(last_activity) >= date('now', '-30 days')")
        mau = cursor.fetchone()[0]
        
        # Другие метрики
        cursor.execute("SELECT SUM(requests_count) FROM users")
        total_requests = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM dreams")
        total_dreams = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_subscribed = 1")
        subscribed_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1")
        blocked_users = cursor.fetchone()[0]
        
        # Статистика по дням (для графиков)
        cursor.execute('''
            SELECT date(created_at), COUNT(*) 
            FROM users 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY date(created_at)
            ORDER BY date(created_at)
        ''')
        users_growth = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT date(timestamp), COUNT(*) 
            FROM message_logs 
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY date(timestamp)
            ORDER BY date(timestamp)
        ''')
        activity_data = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_week": new_users_week,
            "new_users_month": new_users_month,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "total_requests": total_requests,
            "total_dreams": total_dreams,
            "subscribed_users": subscribed_users,
            "blocked_users": blocked_users,
            "users_growth": users_growth,
            "activity_data": activity_data
        }
        
    except Exception as e:
        print(f"❌ ОШИБКА СТАТИСТИКИ: {e}")
        return {}
    finally:
        conn.close()

@router.get("/admin/api/search-users")
async def search_users(query: str):
    """Поиск пользователей"""
    conn = sqlite3.connect('dreams.db')
    cursor = conn.cursor()
    
    try:
        search_pattern = f"%{query}%"
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, phone, requests_count, 
                   is_subscribed, is_blocked, balance, last_activity, created_at
            FROM users 
            WHERE user_id = ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
            ORDER BY last_activity DESC
            LIMIT 50
        ''', (query, search_pattern, search_pattern, search_pattern, search_pattern))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "user_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "phone": row[4],
                "requests_count": row[5],
                "is_subscribed": bool(row[6]),
                "is_blocked": bool(row[7]),
                "balance": row[8],
                "last_activity": row[9],
                "created_at": row[10]
            })
        
        return users
        
    except Exception as e:
        print(f"❌ ОШИБКА ПОИСКА: {e}")
        return []
    finally:
        conn.close()

@router.get("/admin/api/user/{user_id}")
async def get_user_details(user_id: int):
    """Полная информация о пользователе"""
    conn = sqlite3.connect('dreams.db')
    cursor = conn.cursor()
    
    try:
        # Основная информация
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, phone, requests_count, 
                   is_subscribed, is_blocked, balance, last_activity, created_at
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user_info = cursor.fetchone()
        if not user_info:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # История снов
        cursor.execute('''
            SELECT dream_text, interpretation, created_at, is_voice
            FROM dreams WHERE user_id = ? ORDER BY created_at DESC LIMIT 10
        ''', (user_id,))
        dreams = cursor.fetchall()
        
        # Последние сообщения
        cursor.execute('''
            SELECT message_type, message_text, direction, timestamp
            FROM message_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10
        ''', (user_id,))
        messages = cursor.fetchall()
        
        # Логи ошибок
        cursor.execute('''
            SELECT error_type, error_message, timestamp
            FROM error_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5
        ''', (user_id,))
        errors = cursor.fetchall()
        
        return {
            "user_info": {
                "user_id": user_info[0],
                "username": user_info[1],
                "first_name": user_info[2],
                "last_name": user_info[3],
                "phone": user_info[4],
                "requests_count": user_info[5],
                "is_subscribed": bool(user_info[6]),
                "is_blocked": bool(user_info[7]),
                "balance": user_info[8],
                "last_activity": user_info[9],
                "created_at": user_info[10]
            },
            "dreams": [{
                "text": dream[0],
                "interpretation": dream[1],
                "created_at": dream[2],
                "is_voice": bool(dream[3])
            } for dream in dreams],
            "messages": [{
                "type": msg[0],
                "text": msg[1],
                "direction": msg[2],
                "timestamp": msg[3]
            } for msg in messages],
            "errors": [{
                "type": err[0],
                "message": err[1],
                "timestamp": err[2]
            } for err in errors]
        }
        
    except Exception as e:
        print(f"❌ ОШИБКА ПОЛУЧЕНИЯ ДАННЫХ: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()