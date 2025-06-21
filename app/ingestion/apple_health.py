#!/usr/bin/env python3
"""
Apple Health XML Parser - Focused on Core Metrics with Timezone Awareness

Parses Apple Health export XML for key health metrics and creates SQLite database.
Focus on simplicity and the metrics that matter most for health insights.
Now includes automatic user timezone detection for accurate daily aggregations.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from datetime import datetime, date, timezone, timedelta
import os
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple, Optional

from app.core.logger import get_health_logger

# Initialize logger
logger = get_health_logger()

def get_user_timezone():
    """
    Detect user's timezone using system datetime.
    This is the primary method for timezone detection.
    """
    local_dt = datetime.now().astimezone()
    
    # Get timezone info
    timezone_name = str(local_dt.tzinfo)  # e.g., "America/Los_Angeles" or "UTC-07:00"
    timezone_offset = local_dt.strftime('%z')  # e.g., "-0700"
    
    logger.info(f"Detected user timezone: {timezone_name} ({timezone_offset})")
    
    return {
        'name': timezone_name,
        'offset': timezone_offset,
        'tzinfo': local_dt.tzinfo
    }

class AppleHealthParser:
    def __init__(self, xml_path: str, db_path: str = "data/lifebuddy.db"):
        self.xml_path = Path(xml_path)
        self.db_path = Path(db_path)
        
        # Detect user's timezone at initialization
        self.user_timezone = get_user_timezone()
        
        # Core metrics we care about - only the most important health indicators
        self.target_metrics = {
            'HKQuantityTypeIdentifierActiveEnergyBurned',    # Calories burned during activity
            'HKQuantityTypeIdentifierHeartRate',             # Heart rate readings
            'HKQuantityTypeIdentifierBasalEnergyBurned',     # Resting metabolic rate calories
            'HKQuantityTypeIdentifierDistanceWalkingRunning', # Distance traveled on foot
            'HKQuantityTypeIdentifierStepCount',             # Number of steps
            'HKQuantityTypeIdentifierAppleExerciseTime',     # Minutes of exercise
            'HKQuantityTypeIdentifierBodyMassIndex',         # BMI calculations
            'HKQuantityTypeIdentifierBodyMass',              # Weight measurements
            'HKQuantityTypeIdentifierBodyFatPercentage'      # Body fat percentage
        }
        
        self.parsed_records = []
        self.parsed_workouts = []
        
    def create_database(self):
        """Create SQLite database with timezone-aware schema"""
        logger.info("Creating timezone-aware SQLite database...")
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables for clean overwrite
        cursor.execute("DROP TABLE IF EXISTS user_settings")
        cursor.execute("DROP TABLE IF EXISTS health_records")
        cursor.execute("DROP TABLE IF EXISTS daily_summaries")
        cursor.execute("DROP TABLE IF EXISTS workouts")
        
        # User settings table - stores timezone and other user preferences
        cursor.execute("""
            CREATE TABLE user_settings (
                id INTEGER PRIMARY KEY,
                timezone_name TEXT NOT NULL,           -- e.g., "America/Los_Angeles"
                timezone_offset TEXT NOT NULL,         -- e.g., "-0700"
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert user timezone
        cursor.execute("""
            INSERT INTO user_settings (id, timezone_name, timezone_offset)
            VALUES (1, ?, ?)
        """, (self.user_timezone['name'], self.user_timezone['offset']))
        
        # Health records table - stores raw minute-by-minute data in user's timezone
        cursor.execute("""
            CREATE TABLE health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type VARCHAR(100) NOT NULL,     -- e.g. 'HKQuantityTypeIdentifierStepCount'
                value REAL NOT NULL,                   -- The actual measurement (steps, calories, etc.)
                unit VARCHAR(20),                      -- 'count', 'Cal', 'km', 'bpm', etc.
                start_date DATETIME NOT NULL,          -- When measurement started (user's timezone)
                end_date DATETIME,                     -- When measurement ended (user's timezone)
                creation_date DATETIME,                -- When recorded in Health app (user's timezone)
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Daily summaries table - aggregated daily metrics using user's timezone boundaries
        cursor.execute("""
            CREATE TABLE daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,             -- The date (YYYY-MM-DD) in user's timezone
                
                -- Daily totals (sum all values for the day)
                steps INTEGER,                         -- Total steps for the day
                active_energy_burned REAL,             -- Total active calories burned
                basal_energy_burned REAL,              -- Total basal calories burned
                exercise_time_minutes INTEGER,         -- Total exercise minutes
                distance_walking_km REAL,              -- Total walking/running distance
                
                -- Daily averages/ranges for continuous metrics
                avg_heart_rate REAL,                   -- Average heart rate
                min_heart_rate REAL,                   -- Lowest heart rate
                max_heart_rate REAL,                   -- Highest heart rate
                
                -- Most recent values for infrequent metrics (weight, BMI, body fat)
                body_mass_kg REAL,                     -- Most recent weight
                body_mass_index REAL,                  -- Most recent BMI
                body_fat_percentage REAL,              -- Most recent body fat %
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Workouts table - exercise sessions with detailed metrics in user's timezone
        cursor.execute("""
            CREATE TABLE workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_type VARCHAR(50),              -- 'Walking', 'Running', 'Cycling', etc.
                start_date DATETIME NOT NULL,          -- When workout started (user's timezone)
                end_date DATETIME,                     -- When workout ended (user's timezone)
                duration_minutes REAL,                 -- How long the workout lasted
                total_energy_burned REAL,              -- Calories burned during workout
                total_distance_km REAL,                -- Distance covered during workout
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance indexes - critical for fast queries on large datasets
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_records_type_date ON health_records(record_type, start_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_records_date ON health_records(start_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_summaries_date ON daily_summaries(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(start_date)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Timezone-aware database created at: {self.db_path}")
        logger.info(f"Using timezone: {self.user_timezone['name']} ({self.user_timezone['offset']})")
    
    def parse_xml(self):
        """Parse XML and extract core health metrics"""
        logger.info(f"Parsing Apple Health XML: {self.xml_path}")
        logger.info(f"File size: {self.xml_path.stat().st_size / (1024*1024):.1f} MB")
        
        # Use iterparse for memory efficiency with large XML files
        # This processes elements one at a time instead of loading entire file
        context = ET.iterparse(self.xml_path, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        record_count = 0
        workout_count = 0
        target_records = 0
        
        for event, elem in context:
            if event == 'end':
                if elem.tag == 'Record':
                    record_type = elem.get('type', '')
                    
                    # Filter: Only process our target metrics to reduce data volume
                    if record_type in self.target_metrics:
                        record_data = self._parse_health_record(elem)
                        if record_data:
                            self.parsed_records.append(record_data)
                            target_records += 1
                    
                    record_count += 1
                    
                elif elem.tag == 'Workout':
                    workout_data = self._parse_workout(elem)
                    if workout_data:
                        self.parsed_workouts.append(workout_data)
                        workout_count += 1
                
                # Memory management: Clear processed elements to prevent memory bloat
                elem.clear()
                
                # Progress indicator for large files
                if record_count % 200000 == 0:
                    print(f"📊 Processed {record_count:,} total records, {target_records:,} target metrics...")
        
        print(f"\n✅ Parsing complete!")
        print(f"📈 Total Records Processed: {record_count:,}")
        print(f"🎯 Target Health Records: {target_records:,}")
        print(f"🏃 Workouts: {workout_count:,}")
        
        return target_records, workout_count
    
    def _parse_health_record(self, elem) -> Optional[Dict]:
        """Parse individual health record from XML element with timezone awareness"""
        try:
            # Parse timestamps - convert to user's timezone instead of UTC
            start_date = self._parse_date(elem.get('startDate'))
            end_date = self._parse_date(elem.get('endDate'))
            creation_date = self._parse_date(elem.get('creationDate'))
            
            # Parse numeric value - health measurements are always numbers
            value_str = elem.get('value', '0')
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                # Skip records with invalid numeric values
                return None
            
            return {
                'record_type': elem.get('type'),
                'value': value,
                'unit': elem.get('unit'),
                'start_date': start_date,
                'end_date': end_date,
                'creation_date': creation_date
            }
        except Exception as e:
            print(f"⚠️ Error parsing record: {e}")
            return None
    
    def _parse_workout(self, elem) -> Optional[Dict]:
        """Parse workout record from XML element with timezone awareness"""
        try:
            start_date = self._parse_date(elem.get('startDate'))
            end_date = self._parse_date(elem.get('endDate'))
            
            # Parse workout duration
            duration_str = elem.get('duration', '0')
            duration_unit = elem.get('durationUnit', 'min')
            
            try:
                duration = float(duration_str)
                # Apple Health typically stores duration in minutes
                if duration_unit == 'min':
                    duration_minutes = duration
                else:
                    # Convert other units to minutes if needed
                    duration_minutes = duration  # Assume minutes for now
            except (ValueError, TypeError):
                duration_minutes = 0
            
            # Initialize workout statistics
            total_energy = 0
            total_distance = 0
            
            # Parse nested workout statistics (energy burned, distance, etc.)
            for child in elem:
                if child.tag == 'WorkoutStatistics':
                    stat_type = child.get('type', '')
                    if 'Energy' in stat_type:
                        try:
                            total_energy = float(child.get('sum', '0'))
                        except (ValueError, TypeError):
                            pass
                    elif 'Distance' in stat_type:
                        try:
                            total_distance = float(child.get('sum', '0'))
                        except (ValueError, TypeError):
                            pass
            
            # Clean up workout type name
            # Apple Health uses verbose names like 'HKWorkoutActivityTypeWalking'
            # We want clean names like 'Walking' for better readability
            raw_workout_type = elem.get('workoutActivityType', '')
            clean_workout_type = raw_workout_type.replace('HKWorkoutActivityType', '')
            
            return {
                'workout_type': clean_workout_type,
                'start_date': start_date,
                'end_date': end_date,
                'duration_minutes': duration_minutes,
                'total_energy_burned': total_energy,
                'total_distance_km': total_distance
            }
        except Exception as e:
            print(f"⚠️ Error parsing workout: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse Apple Health date string and convert to user's timezone for storage
        
        Apple Health exports dates in format: "2023-09-11 20:09:44 -0700"
        Instead of converting to UTC, we convert to user's local timezone for accurate daily boundaries
        """
        if not date_str:
            return None
        
        try:
            # Handle timezone offset parsing
            if ' -' in date_str or ' +' in date_str:
                # Split date and timezone
                date_part = date_str.rsplit(' ', 1)[0]
                tz_part = date_str.rsplit(' ', 1)[1]
                
                # Parse the datetime part
                dt = datetime.fromisoformat(date_part)
                
                # Parse timezone offset (e.g., "-0700" means UTC-7)
                if tz_part.startswith('-') or tz_part.startswith('+'):
                    sign = -1 if tz_part.startswith('-') else 1
                    hours = int(tz_part[1:3])
                    minutes = int(tz_part[3:5])
                    
                    # Create timezone object for Apple Health data
                    tz_offset = timedelta(hours=sign * hours, minutes=sign * minutes)
                    apple_tz = timezone(tz_offset)
                    
                    # Apply Apple Health timezone
                    dt_with_tz = dt.replace(tzinfo=apple_tz)
                    
                    # Convert to user's local timezone instead of UTC
                    user_local_dt = dt_with_tz.astimezone(self.user_timezone['tzinfo'])
                    
                    return user_local_dt.isoformat()
                else:
                    # No timezone info, assume it's already in user's timezone
                    return dt.isoformat()
            else:
                # No timezone info, parse as-is and assume user's timezone
                dt = datetime.fromisoformat(date_str)
                return dt.isoformat()
                
        except Exception as e:
            print(f"⚠️ Error parsing date '{date_str}': {e}")
            return date_str  # Return as-is if parsing fails
    
    def save_to_database(self):
        """Save parsed data to SQLite database"""
        print("💾 Saving data to database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert health records in batch for efficiency
        print(f"📊 Inserting {len(self.parsed_records):,} health records...")
        cursor.executemany("""
            INSERT INTO health_records 
            (record_type, value, unit, start_date, end_date, creation_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (r['record_type'], r['value'], r['unit'], 
             r['start_date'], r['end_date'], r['creation_date'])
            for r in self.parsed_records
        ])
        
        # Insert workouts in batch
        print(f"🏃 Inserting {len(self.parsed_workouts):,} workouts...")
        cursor.executemany("""
            INSERT INTO workouts 
            (workout_type, start_date, end_date, duration_minutes, total_energy_burned, total_distance_km)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (w['workout_type'], w['start_date'], w['end_date'],
             w['duration_minutes'], w['total_energy_burned'], w['total_distance_km'])
            for w in self.parsed_workouts
        ])
        
        conn.commit()
        
        # Generate daily summaries from the raw data
        self._generate_daily_summaries(cursor)
        
        conn.commit()
        conn.close()
        
        print("✅ Data saved successfully!")
    
    def _generate_daily_summaries(self, cursor):
        """
        Generate daily summaries from health records using user's timezone
        
        Since all data is now stored in user's timezone, DATE() function will work correctly
        for daily aggregations without timezone boundary issues.
        """
        print("📋 Generating timezone-aware daily summaries...")
        
        # Efficient aggregation query that handles missing data properly
        # Now works correctly because all timestamps are in user's timezone
        cursor.execute("""
            INSERT INTO daily_summaries (
                date, steps, active_energy_burned, basal_energy_burned, 
                exercise_time_minutes, distance_walking_km, 
                avg_heart_rate, min_heart_rate, max_heart_rate,
                body_mass_kg, body_mass_index, body_fat_percentage
            )
            SELECT 
                DATE(start_date) as date,
                
                -- Daily totals: Sum all measurements for the day (now timezone-correct)
                SUM(CASE WHEN record_type = 'HKQuantityTypeIdentifierStepCount' THEN value END) as steps,
                SUM(CASE WHEN record_type = 'HKQuantityTypeIdentifierActiveEnergyBurned' THEN value END) as active_energy_burned,
                SUM(CASE WHEN record_type = 'HKQuantityTypeIdentifierBasalEnergyBurned' THEN value END) as basal_energy_burned,
                SUM(CASE WHEN record_type = 'HKQuantityTypeIdentifierAppleExerciseTime' THEN value END) as exercise_time_minutes,
                SUM(CASE WHEN record_type = 'HKQuantityTypeIdentifierDistanceWalkingRunning' THEN value END) as distance_walking_km,
                
                -- Heart rate statistics: Min/Max/Average for the day
                AVG(CASE WHEN record_type = 'HKQuantityTypeIdentifierHeartRate' THEN value END) as avg_heart_rate,
                MIN(CASE WHEN record_type = 'HKQuantityTypeIdentifierHeartRate' THEN value END) as min_heart_rate,
                MAX(CASE WHEN record_type = 'HKQuantityTypeIdentifierHeartRate' THEN value END) as max_heart_rate,
                
                -- Body metrics: Use average if multiple readings on same day, NULL if no readings
                AVG(CASE WHEN record_type = 'HKQuantityTypeIdentifierBodyMass' THEN value END) as body_mass_kg,
                AVG(CASE WHEN record_type = 'HKQuantityTypeIdentifierBodyMassIndex' THEN value END) as body_mass_index,
                AVG(CASE WHEN record_type = 'HKQuantityTypeIdentifierBodyFatPercentage' THEN value END) as body_fat_percentage
                
            FROM health_records 
            WHERE DATE(start_date) IS NOT NULL
            GROUP BY DATE(start_date)
            ORDER BY date
        """)
        
        print("✅ Timezone-aware daily summaries generated!")
    
    def print_summary(self):
        """Print summary of parsed data for verification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📊 DATABASE SUMMARY")
        print("="*60)
        
        # Health records summary
        cursor.execute("SELECT COUNT(*) FROM health_records")
        health_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT record_type) FROM health_records")
        metric_types = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(DATE(start_date)), MAX(DATE(start_date)) FROM health_records")
        date_range = cursor.fetchone()
        
        print(f"📈 Health Records: {health_count:,}")
        print(f"🎯 Metric Types: {metric_types}")
        print(f"📅 Date Range: {date_range[0]} → {date_range[1]}")
        
        # Daily summaries
        cursor.execute("SELECT COUNT(*) FROM daily_summaries")
        daily_count = cursor.fetchone()[0]
        print(f"📋 Daily Summaries: {daily_count:,} days")
        
        # Workouts
        cursor.execute("SELECT COUNT(*) FROM workouts")
        workout_count = cursor.fetchone()[0]
        print(f"🏃 Workouts: {workout_count:,}")
        
        # Sample daily summary to verify data quality
        cursor.execute("""
            SELECT date, steps, active_energy_burned, avg_heart_rate 
            FROM daily_summaries 
            WHERE steps IS NOT NULL 
            ORDER BY date DESC 
            LIMIT 3
        """)
        
        print(f"\n📋 Recent Daily Summaries:")
        for row in cursor.fetchall():
            date_str, steps, energy, hr = row
            print(f"  {date_str}: {steps or 0:,} steps, {energy or 0:.0f} cal, {hr or 0:.0f} bpm")
        
        conn.close()


def main():
    """Run the Apple Health parser"""
    xml_path = "data/raw/apple_health_export/export.xml"
    
    if not os.path.exists(xml_path):
        logger.error(f"File not found: {xml_path}")
        logger.info("Please ensure your Apple Health export is in the correct location.")
        return
    
    parser = AppleHealthParser(xml_path)
    
    logger.info("Starting focused Apple Health parsing...")
    
    # Create database with optimized schema
    parser.create_database()
    
    # Parse XML and extract target metrics
    target_records, workouts = parser.parse_xml()
    
    # Save to database and generate daily summaries
    parser.save_to_database()
    
    # Print summary for verification
    parser.print_summary()
    
    print(f"\n✅ Parsing complete! Processed {target_records:,} health records and {workouts:,} workouts.")
    print("💾 Database ready for LifeBuddy application!")


if __name__ == "__main__":
    main() 