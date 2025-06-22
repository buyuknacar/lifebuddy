"""
Health Data Service for accessing SQLite health database.
Provides structured access to health metrics for LangChain agents.
Now includes timezone-aware operations.
"""
import os
import sqlite3
from datetime import datetime, timedelta, date, timezone
from typing import Dict, List, Optional, Any
import pandas as pd
import re

from app.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


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
            
            expected_tables = ['health_records', 'daily_summaries', 'workouts', 'user_settings', 'sleep_records']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                raise ValueError(f"Missing database tables: {missing_tables}")
    
    def _get_user_timezone(self) -> Dict[str, str]:
        """Get user's timezone information, prioritizing current TZ environment variable."""
        # First, check for current TZ environment variable (takes priority)
        tz_env = os.environ.get('TZ', '').strip()
        
        if tz_env and tz_env.startswith('UTC'):
            # Parse UTC offset format (UTC-8, UTC+5:30, etc.)
            match = re.match(r'UTC([+-])(\d{1,2})(?::(\d{2}))?', tz_env)
            if match:
                sign = match.group(1)
                hours = int(match.group(2))
                minutes = int(match.group(3)) if match.group(3) else 0
                
                # Convert to timezone offset
                total_minutes = hours * 60 + minutes
                if sign == '-':
                    total_minutes = -total_minutes
                
                # Format offset string
                offset_hours = total_minutes // 60
                offset_mins = abs(total_minutes % 60)
                if offset_mins > 0:
                    offset_str = f"{offset_hours:+03d}{offset_mins:02d}"
                else:
                    offset_str = f"{offset_hours:+03d}00"
                
                logger.info(f"Using current TZ environment variable: {tz_env} ({offset_str})")
                
                return {
                    'name': tz_env,
                    'offset': offset_str
                }
        
        # Fallback to database timezone (from when data was parsed)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timezone_name, timezone_offset FROM user_settings WHERE id = 1")
                result = cursor.fetchone()
                
                if result:
                    logger.info(f"Using timezone from database: {result[0]} ({result[1]})")
                    return {
                        'name': result[0],
                        'offset': result[1]
                    }
        except Exception as e:
            logger.warning(f"Error getting timezone from database: {e}")
        
        # Final fallback to system timezone
        local_dt = datetime.now().astimezone()
        timezone_name = str(local_dt.tzinfo)
        timezone_offset = local_dt.strftime('%z')
        
        logger.warning(f"Using system timezone fallback: {timezone_name} ({timezone_offset})")
        return {
            'name': timezone_name,
            'offset': timezone_offset
        }
    
    def get_user_timezone_info(self) -> Dict[str, str]:
        """Get user's timezone information for display or calculations."""
        return {
            "timezone_name": self.user_timezone['name'],
            "timezone_offset": self.user_timezone['offset'],
            "message": f"User is in timezone: {self.user_timezone['name']} ({self.user_timezone['offset']})"
        }
    
    def _get_user_current_date(self) -> date:
        """Get current date in user's timezone for accurate date range calculations."""
        try:
            # Try to parse user timezone offset (e.g., "-0800" or "+0530")
            offset_str = self.user_timezone['offset']
            
            # Parse offset string like "+0530" or "-0800"
            if len(offset_str) == 5 and offset_str[0] in ['+', '-']:
                sign = 1 if offset_str[0] == '+' else -1
                hours = int(offset_str[1:3])
                minutes = int(offset_str[3:5])
                total_minutes = sign * (hours * 60 + minutes)
                
                # Create timezone-aware datetime
                user_tz = timezone(timedelta(minutes=total_minutes))
                user_now = datetime.now(user_tz)
                return user_now.date()
            else:
                # Fallback to system date if can't parse offset
                logger.warning(f"Could not parse timezone offset: {offset_str}, using system date")
                return datetime.now().date()
                
        except Exception as e:
            logger.warning(f"Error calculating user timezone date: {e}, using system date")
            return datetime.now().date()
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SQL query and return results as list of dictionaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_steps(self, days_back: int = 7) -> Dict[str, Any]:
        """Get daily step counts for the last N days."""
        end_date = self._get_user_current_date()
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
        end_date = self._get_user_current_date()
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
        SELECT workout_type, start_date, duration_minutes, 
               total_energy_burned, total_distance_km
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
        total_distance = sum(row['total_distance_km'] or 0 for row in results)
        
        return {
            "total_workouts": total_workouts,
            "total_energy_burned": round(total_energy),
            "total_duration_minutes": round(total_duration),
            "total_distance_km": round(total_distance, 2),
            "recent_workouts": results
        }
    
    def get_weight_progress(self, days_back: int = 30) -> Dict[str, Any]:
        """Get weight tracking progress."""
        end_date = self._get_user_current_date()
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
        end_date = self._get_user_current_date()
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
    
    def get_sleep_data(self, days_back: int = 7) -> Dict[str, Any]:
        """Get sleep data for the last N days - handles both old iPhone and new Apple Watch formats."""
        end_date = self._get_user_current_date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get individual sleep records and aggregate by date and type
        query = """
        SELECT 
            DATE(start_date) as sleep_date,
            value as duration_hours,
            start_date,
            end_date,
            source_name,
            sleep_stage,
            data_type
        FROM sleep_records 
        WHERE DATE(start_date) >= ? AND DATE(start_date) <= ?
        ORDER BY start_date DESC
        """
        
        results = self._execute_query(query, (start_date, end_date))
        
        if not results:
            return {"message": "No sleep data found for the requested period"}
        
        # Aggregate by date, handling both old and new formats
        daily_sleep = {}
        for record in results:
            date = record['sleep_date']
            if date not in daily_sleep:
                daily_sleep[date] = {
                    'date': date,
                    'total_sleep_hours': 0,
                    'time_in_bed_hours': 0,
                    'sleep_stages': {'Core': 0, 'REM': 0, 'Deep': 0},
                    'data_source': 'mixed',
                    'sources': set()
                }
            
            daily_sleep[date]['sources'].add(record['source_name'])
            
            # Handle old iPhone format (total time in bed)
            if record['data_type'] == 'total_time_in_bed':
                daily_sleep[date]['time_in_bed_hours'] += record['duration_hours']
                daily_sleep[date]['data_source'] = 'iPhone'
            
            # Handle new Apple Watch format (sleep stages)
            elif record['data_type'] == 'sleep_stage':
                stage = record['sleep_stage']
                if stage in ['Core', 'REM', 'Deep']:
                    daily_sleep[date]['sleep_stages'][stage] += record['duration_hours']
                    daily_sleep[date]['data_source'] = 'Apple Watch'
        
        # Calculate total sleep for Apple Watch data and clean up
        daily_breakdown = []
        for date_data in daily_sleep.values():
            # For Apple Watch data, sum all sleep stages for total sleep time
            if date_data['data_source'] == 'Apple Watch':
                date_data['total_sleep_hours'] = sum(date_data['sleep_stages'].values())
            # For iPhone data, use time_in_bed as sleep time (older format)
            elif date_data['data_source'] == 'iPhone':
                date_data['total_sleep_hours'] = date_data['time_in_bed_hours']
            
            # Clean up and format
            date_data['sources'] = list(date_data['sources'])
            date_data['total_sleep_hours'] = round(date_data['total_sleep_hours'], 1)
            date_data['time_in_bed_hours'] = round(date_data['time_in_bed_hours'], 1)
            
            # Round sleep stages
            for stage in date_data['sleep_stages']:
                date_data['sleep_stages'][stage] = round(date_data['sleep_stages'][stage], 1)
            
            daily_breakdown.append(date_data)
        
        # Sort by date descending
        daily_breakdown.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate overall statistics
        total_hours = sum(day['total_sleep_hours'] for day in daily_breakdown)
        avg_hours = total_hours / len(daily_breakdown) if daily_breakdown else 0
        
        # Separate Apple Watch vs iPhone data counts
        watch_days = len([d for d in daily_breakdown if d['data_source'] == 'Apple Watch'])
        phone_days = len([d for d in daily_breakdown if d['data_source'] == 'iPhone'])
        
        return {
            "period": f"Last {days_back} days",
            "total_sleep_hours": round(total_hours, 1),
            "average_sleep_hours": round(avg_hours, 1),
            "days_with_data": len(daily_breakdown),
            "apple_watch_days": watch_days,
            "iphone_days": phone_days,
            "daily_breakdown": daily_breakdown,
            "raw_records_count": len(results)
        }
    
    def search_health_data(self, metric_type: str, days_back: int = 7) -> Dict[str, Any]:
        """Generic search for health data by metric type."""
        metric_map = {
            "steps": self.get_daily_steps,
            "heart_rate": self.get_heart_rate_summary,
            "workouts": lambda d: self.get_recent_workouts(limit=d),
            "weight": self.get_weight_progress,
            "activity": self.get_activity_summary,
            "sleep": self.get_sleep_data
        }
        
        if metric_type.lower() not in metric_map:
            return {
                "error": f"Unknown metric type: {metric_type}",
                "available_metrics": list(metric_map.keys())
            }
        
        return metric_map[metric_type.lower()](days_back)


# Global health data service instance
health_service = HealthDataService() 