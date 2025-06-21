"""
Health Data Service for accessing SQLite health database.
Provides structured access to health metrics for LangChain agents.
Now includes timezone-aware operations.
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd


class HealthDataService:
    """Service for accessing health data from SQLite database with timezone awareness."""
    
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "data/lifebuddy.db")
        self._verify_database()
        self.user_timezone = self._get_user_timezone()
    
    def _verify_database(self):
        """Verify database exists and has expected tables."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Health database not found: {self.db_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['health_records', 'daily_summaries', 'workouts', 'user_settings']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                raise ValueError(f"Missing database tables: {missing_tables}")
    
    def _get_user_timezone(self) -> Dict[str, str]:
        """Get user's timezone information from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timezone_name, timezone_offset FROM user_settings WHERE id = 1")
                result = cursor.fetchone()
                
                if result:
                    return {
                        'name': result[0],
                        'offset': result[1]
                    }
                else:
                    # Fallback to system timezone if not found in database
                    local_dt = datetime.now().astimezone()
                    return {
                        'name': str(local_dt.tzinfo),
                        'offset': local_dt.strftime('%z')
                    }
        except Exception as e:
            print(f"⚠️ Error getting user timezone: {e}")
            # Fallback to system timezone
            local_dt = datetime.now().astimezone()
            return {
                'name': str(local_dt.tzinfo),
                'offset': local_dt.strftime('%z')
            }
    
    def get_user_timezone_info(self) -> Dict[str, str]:
        """Get user's timezone information for display or calculations."""
        return {
            "timezone_name": self.user_timezone['name'],
            "timezone_offset": self.user_timezone['offset'],
            "message": f"User is in timezone: {self.user_timezone['name']} ({self.user_timezone['offset']})"
        }
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SQL query and return results as list of dictionaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_steps(self, days_back: int = 7) -> Dict[str, Any]:
        """Get daily step counts for the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        query = """
        SELECT date, steps
        FROM daily_summaries 
        WHERE date >= ? AND date <= ? AND steps IS NOT NULL
        ORDER BY date DESC
        """
        
        results = self._execute_query(query, (start_date, end_date))
        
        if not results:
            return {"message": "No step data found for the requested period"}
        
        total_steps = sum(row['steps'] for row in results)
        avg_steps = total_steps / len(results)
        
        return {
            "period": f"Last {days_back} days",
            "total_steps": total_steps,
            "average_steps": round(avg_steps),
            "days_with_data": len(results),
            "daily_breakdown": results
        }
    
    def get_heart_rate_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get heart rate summary for the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        query = """
        SELECT date, avg_heart_rate, min_heart_rate, max_heart_rate
        FROM daily_summaries 
        WHERE date >= ? AND date <= ? AND avg_heart_rate IS NOT NULL
        ORDER BY date DESC
        """
        
        results = self._execute_query(query, (start_date, end_date))
        
        if not results:
            return {"message": "No heart rate data found for the requested period"}
        
        avg_hr = sum(row['avg_heart_rate'] for row in results) / len(results)
        overall_min = min(row['min_heart_rate'] for row in results)
        overall_max = max(row['max_heart_rate'] for row in results)
        
        return {
            "period": f"Last {days_back} days",
            "average_heart_rate": round(avg_hr),
            "lowest_heart_rate": overall_min,
            "highest_heart_rate": overall_max,
            "days_with_data": len(results),
            "daily_breakdown": results
        }
    
    def get_recent_workouts(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent workout activities."""
        query = """
        SELECT workout_name, start_date, duration_minutes, 
               total_energy_burned, total_distance
        FROM workouts 
        ORDER BY start_date DESC 
        LIMIT ?
        """
        
        results = self._execute_query(query, (limit,))
        
        if not results:
            return {"message": "No workout data found"}
        
        total_workouts = len(results)
        total_energy = sum(row['total_energy_burned'] or 0 for row in results)
        total_duration = sum(row['duration_minutes'] or 0 for row in results)
        
        return {
            "total_workouts": total_workouts,
            "total_energy_burned": round(total_energy),
            "total_duration_minutes": round(total_duration),
            "recent_workouts": results
        }
    
    def get_weight_progress(self, days_back: int = 30) -> Dict[str, Any]:
        """Get weight tracking progress."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        query = """
        SELECT date, body_mass_kg, body_fat_percentage
        FROM daily_summaries 
        WHERE date >= ? AND date <= ? AND body_mass_kg IS NOT NULL
        ORDER BY date DESC
        """
        
        results = self._execute_query(query, (start_date, end_date))
        
        if not results:
            return {"message": "No weight data found for the requested period"}
        
        current_weight = results[0]['body_mass_kg']
        previous_weight = results[-1]['body_mass_kg']
        weight_change = current_weight - previous_weight
        
        return {
            "period": f"Last {days_back} days",
            "current_weight": round(current_weight, 1),
            "weight_change": round(weight_change, 1),
            "measurements_count": len(results),
            "recent_measurements": results[:5]  # Show last 5
        }
    
    def get_activity_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get comprehensive activity summary."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        query = """
        SELECT date, steps, active_energy_burned, 
               exercise_time_minutes, distance_walking_km
        FROM daily_summaries 
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC
        """
        
        results = self._execute_query(query, (start_date, end_date))
        
        if not results:
            return {"message": "No activity data found for the requested period"}
        
        # Calculate totals and averages
        total_steps = sum(row['steps'] or 0 for row in results)
        total_energy = sum(row['active_energy_burned'] or 0 for row in results)
        total_exercise_time = sum(row['exercise_time_minutes'] or 0 for row in results)
        total_distance = sum(row['distance_walking_km'] or 0 for row in results)
        
        days_count = len(results)
        
        return {
            "period": f"Last {days_back} days",
            "summary": {
                "total_steps": total_steps,
                "average_daily_steps": round(total_steps / days_count),
                "total_active_energy": round(total_energy),
                "total_exercise_minutes": round(total_exercise_time),
                "total_distance_km": round(total_distance, 2),
                "days_with_data": days_count
            },
            "daily_breakdown": results
        }
    
    def search_health_data(self, metric_type: str, days_back: int = 7) -> Dict[str, Any]:
        """Generic search for health data by metric type."""
        metric_map = {
            "steps": self.get_daily_steps,
            "heart_rate": self.get_heart_rate_summary,
            "workouts": lambda d: self.get_recent_workouts(limit=d),
            "weight": self.get_weight_progress,
            "activity": self.get_activity_summary
        }
        
        if metric_type.lower() not in metric_map:
            return {
                "error": f"Unknown metric type: {metric_type}",
                "available_metrics": list(metric_map.keys())
            }
        
        return metric_map[metric_type.lower()](days_back)


# Global health data service instance
health_service = HealthDataService() 