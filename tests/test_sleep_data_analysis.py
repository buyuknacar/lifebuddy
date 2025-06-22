#!/usr/bin/env python3
"""
Comprehensive Sleep Data Analysis Script

Analyzes all sleep-related records from Apple Health export:
- HKCategoryTypeIdentifierSleepAnalysis (sleep stages)
- AppleSleepingBreathingDisturbances (breathing disturbances during sleep)
- AppleSleepingWristTemperature (wrist temperature during sleep)

This helps understand the data structure and design appropriate sleep tables.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json


class ComprehensiveSleepAnalyzer:
    """Analyzes all Apple Health sleep-related data types."""
    
    def __init__(self, xml_path: str):
        self.xml_path = Path(xml_path)
        
        # Data storage for different sleep data types
        self.sleep_analysis_records = []
        self.breathing_disturbance_records = []
        self.wrist_temperature_records = []
        
        # Statistics tracking
        self.sleep_values = Counter()
        self.sleep_sources = Counter()
        self.breathing_sources = Counter()
        self.temperature_sources = Counter()
        
        # Date ranges for each data type
        self.date_ranges = {
            'sleep_analysis': {'earliest': None, 'latest': None},
            'breathing_disturbances': {'earliest': None, 'latest': None},
            'wrist_temperature': {'earliest': None, 'latest': None}
        }
        
        # Target data types
        self.target_types = {
            'HKCategoryTypeIdentifierSleepAnalysis': 'sleep_analysis',
            'AppleSleepingBreathingDisturbances': 'breathing_disturbances', 
            'AppleSleepingWristTemperature': 'wrist_temperature'
        }
        
    def analyze_all_sleep_data(self):
        """Analyze all sleep-related data types."""
        print(f"💤 Comprehensive Sleep Data Analysis from: {self.xml_path}")
        print("=" * 70)
        
        if not self.xml_path.exists():
            print(f"❌ File not found: {self.xml_path}")
            return
        
        # Parse XML efficiently
        context = ET.iterparse(self.xml_path, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        total_records = 0
        found_counts = {
            'sleep_analysis': 0,
            'breathing_disturbances': 0,
            'wrist_temperature': 0
        }
        
        print("🔍 Searching for sleep-related records...")
        
        for event, elem in context:
            if event == 'end' and elem.tag == 'Record':
                record_type = elem.get('type', '')
                
                if record_type in self.target_types:
                    data_category = self.target_types[record_type]
                    
                    if data_category == 'sleep_analysis':
                        sleep_data = self._parse_sleep_analysis_record(elem)
                        if sleep_data:
                            self.sleep_analysis_records.append(sleep_data)
                            found_counts['sleep_analysis'] += 1
                    
                    elif data_category == 'breathing_disturbances':
                        breathing_data = self._parse_breathing_record(elem)
                        if breathing_data:
                            self.breathing_disturbance_records.append(breathing_data)
                            found_counts['breathing_disturbances'] += 1
                    
                    elif data_category == 'wrist_temperature':
                        temp_data = self._parse_temperature_record(elem)
                        if temp_data:
                            self.wrist_temperature_records.append(temp_data)
                            found_counts['wrist_temperature'] += 1
                
                total_records += 1
                
                # Progress indicator
                if total_records % 500000 == 0:
                    print(f"   Processed {total_records:,} records...")
                    for category, count in found_counts.items():
                        if count > 0:
                            print(f"     • {category.replace('_', ' ').title()}: {count:,}")
                
                # Clear element to save memory
                elem.clear()
        
        print(f"✅ Analysis complete!")
        print(f"   Total records processed: {total_records:,}")
        print()
        
        # Analyze each data type
        self._analyze_sleep_analysis_data(found_counts['sleep_analysis'])
        self._analyze_breathing_disturbance_data(found_counts['breathing_disturbances'])
        self._analyze_wrist_temperature_data(found_counts['wrist_temperature'])
        
        # Design comprehensive sleep schema
        self._design_comprehensive_sleep_schema()
    
    def _parse_sleep_analysis_record(self, elem) -> Optional[Dict]:
        """Parse HKCategoryTypeIdentifierSleepAnalysis record."""
        try:
            record_data = {
                'type': elem.get('type'),
                'value': elem.get('value'),
                'source_name': elem.get('sourceName'),
                'source_version': elem.get('sourceVersion'),
                'device': elem.get('device', ''),
                'creation_date': elem.get('creationDate'),
                'start_date': elem.get('startDate'),
                'end_date': elem.get('endDate'),
            }
            
            # Parse metadata
            metadata = {}
            for child in elem:
                if child.tag == 'MetadataEntry':
                    key = child.get('key', '')
                    value = child.get('value', '')
                    metadata[key] = value
            
            if metadata:
                record_data['metadata'] = metadata
            
            # Track statistics
            self.sleep_values[record_data['value']] += 1
            self.sleep_sources[record_data['source_name']] += 1
            
            # Track date range
            self._update_date_range('sleep_analysis', record_data['start_date'])
            
            return record_data
            
        except Exception as e:
            print(f"Error parsing sleep analysis record: {e}")
            return None
    
    def _parse_breathing_record(self, elem) -> Optional[Dict]:
        """Parse AppleSleepingBreathingDisturbances record."""
        try:
            record_data = {
                'type': elem.get('type'),
                'value': elem.get('value'),
                'unit': elem.get('unit', ''),
                'source_name': elem.get('sourceName'),
                'source_version': elem.get('sourceVersion'),
                'device': elem.get('device', ''),
                'creation_date': elem.get('creationDate'),
                'start_date': elem.get('startDate'),
                'end_date': elem.get('endDate'),
            }
            
            # Parse metadata
            metadata = {}
            for child in elem:
                if child.tag == 'MetadataEntry':
                    key = child.get('key', '')
                    value = child.get('value', '')
                    metadata[key] = value
            
            if metadata:
                record_data['metadata'] = metadata
            
            # Track statistics
            self.breathing_sources[record_data['source_name']] += 1
            
            # Track date range
            self._update_date_range('breathing_disturbances', record_data['start_date'])
            
            return record_data
            
        except Exception as e:
            print(f"Error parsing breathing disturbance record: {e}")
            return None
    
    def _parse_temperature_record(self, elem) -> Optional[Dict]:
        """Parse AppleSleepingWristTemperature record."""
        try:
            record_data = {
                'type': elem.get('type'),
                'value': elem.get('value'),
                'unit': elem.get('unit', ''),
                'source_name': elem.get('sourceName'),
                'source_version': elem.get('sourceVersion'),
                'device': elem.get('device', ''),
                'creation_date': elem.get('creationDate'),
                'start_date': elem.get('startDate'),
                'end_date': elem.get('endDate'),
            }
            
            # Parse metadata
            metadata = {}
            for child in elem:
                if child.tag == 'MetadataEntry':
                    key = child.get('key', '')
                    value = child.get('value', '')
                    metadata[key] = value
            
            if metadata:
                record_data['metadata'] = metadata
            
            # Track statistics
            self.temperature_sources[record_data['source_name']] += 1
            
            # Track date range
            self._update_date_range('wrist_temperature', record_data['start_date'])
            
            return record_data
            
        except Exception as e:
            print(f"Error parsing wrist temperature record: {e}")
            return None
    
    def _update_date_range(self, data_type: str, date_str: str):
        """Update date range for a specific data type."""
        if not date_str:
            return
            
        date_range = self.date_ranges[data_type]
        if not date_range['earliest'] or date_str < date_range['earliest']:
            date_range['earliest'] = date_str
        if not date_range['latest'] or date_str > date_range['latest']:
            date_range['latest'] = date_str
    
    def _analyze_sleep_analysis_data(self, count: int):
        """Analyze HKCategoryTypeIdentifierSleepAnalysis data."""
        print(f"🛏️  SLEEP ANALYSIS DATA ({count:,} records)")
        print("-" * 50)
        
        if count == 0:
            print("   ❌ No sleep analysis data found")
            print()
            return
        
        date_range = self.date_ranges['sleep_analysis']
        print(f"📅 Date Range:")
        print(f"   Earliest: {date_range['earliest'][:16] if date_range['earliest'] else 'N/A'}")
        print(f"   Latest: {date_range['latest'][:16] if date_range['latest'] else 'N/A'}")
        print()
        
        print(f"💤 Sleep Values (Categories):")
        for value, count in self.sleep_values.most_common():
            print(f"   • {value:<35} {count:>8,} records")
        print()
        
        print(f"📱 Data Sources:")
        for source, count in self.sleep_sources.most_common():
            print(f"   • {source:<25} {count:>8,} records")
        print()
        
        # Show sample records
        if self.sleep_analysis_records:
            print(f"🔍 SAMPLE SLEEP ANALYSIS RECORDS:")
            for i, record in enumerate(self.sleep_analysis_records[:3]):
                print(f"   Record {i+1}:")
                print(f"     Value: {record['value']}")
                print(f"     Start: {record['start_date']}")
                print(f"     End: {record['end_date']}")
                print(f"     Duration: {self._calculate_duration(record['start_date'], record['end_date'])}")
                print(f"     Source: {record['source_name']}")
                if 'metadata' in record:
                    print(f"     Metadata: {record['metadata']}")
                print()
        
        print()
    
    def _analyze_breathing_disturbance_data(self, count: int):
        """Analyze AppleSleepingBreathingDisturbances data."""
        print(f"🫁 BREATHING DISTURBANCES DATA ({count:,} records)")
        print("-" * 50)
        
        if count == 0:
            print("   ❌ No breathing disturbance data found")
            print()
            return
        
        date_range = self.date_ranges['breathing_disturbances']
        print(f"📅 Date Range:")
        print(f"   Earliest: {date_range['earliest'][:16] if date_range['earliest'] else 'N/A'}")
        print(f"   Latest: {date_range['latest'][:16] if date_range['latest'] else 'N/A'}")
        print()
        
        print(f"📱 Data Sources:")
        for source, count in self.breathing_sources.most_common():
            print(f"   • {source:<25} {count:>8,} records")
        print()
        
        # Analyze values
        if self.breathing_disturbance_records:
            values = [float(r['value']) for r in self.breathing_disturbance_records if r['value']]
            if values:
                print(f"📊 Breathing Disturbance Statistics:")
                print(f"   • Average: {sum(values)/len(values):.2f}")
                print(f"   • Min: {min(values):.2f}")
                print(f"   • Max: {max(values):.2f}")
                print()
            
            print(f"🔍 SAMPLE BREATHING DISTURBANCE RECORDS:")
            for i, record in enumerate(self.breathing_disturbance_records[:3]):
                print(f"   Record {i+1}:")
                print(f"     Value: {record['value']} {record.get('unit', '')}")
                print(f"     Start: {record['start_date']}")
                print(f"     End: {record['end_date']}")
                print(f"     Source: {record['source_name']}")
                if 'metadata' in record:
                    print(f"     Metadata: {record['metadata']}")
                print()
        
        print()
    
    def _analyze_wrist_temperature_data(self, count: int):
        """Analyze AppleSleepingWristTemperature data."""
        print(f"🌡️  WRIST TEMPERATURE DATA ({count:,} records)")
        print("-" * 50)
        
        if count == 0:
            print("   ❌ No wrist temperature data found")
            print()
            return
        
        date_range = self.date_ranges['wrist_temperature']
        print(f"📅 Date Range:")
        print(f"   Earliest: {date_range['earliest'][:16] if date_range['earliest'] else 'N/A'}")
        print(f"   Latest: {date_range['latest'][:16] if date_range['latest'] else 'N/A'}")
        print()
        
        print(f"📱 Data Sources:")
        for source, count in self.temperature_sources.most_common():
            print(f"   • {source:<25} {count:>8,} records")
        print()
        
        # Analyze temperature values
        if self.wrist_temperature_records:
            values = [float(r['value']) for r in self.wrist_temperature_records if r['value']]
            if values:
                print(f"📊 Wrist Temperature Statistics:")
                print(f"   • Average: {sum(values)/len(values):.2f}°C")
                print(f"   • Min: {min(values):.2f}°C")
                print(f"   • Max: {max(values):.2f}°C")
                print()
            
            print(f"🔍 SAMPLE WRIST TEMPERATURE RECORDS:")
            for i, record in enumerate(self.wrist_temperature_records[:3]):
                print(f"   Record {i+1}:")
                print(f"     Value: {record['value']} {record.get('unit', '')}")
                print(f"     Start: {record['start_date']}")
                print(f"     End: {record['end_date']}")
                print(f"     Source: {record['source_name']}")
                if 'metadata' in record:
                    print(f"     Metadata: {record['metadata']}")
                print()
        
        print()
    
    def _calculate_duration(self, start_str: str, end_str: str) -> str:
        """Calculate duration between start and end times."""
        try:
            start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            duration = end - start
            
            hours = duration.total_seconds() / 3600
            return f"{hours:.1f} hours"
        except:
            return "Unknown"
    
    def _design_comprehensive_sleep_schema(self):
        """Design comprehensive sleep database schema."""
        print(f"🗄️  COMPREHENSIVE SLEEP DATABASE SCHEMA:")
        print("=" * 70)
        
        print("""
-- Sleep Analysis Table (sleep stages and timing)
CREATE TABLE sleep_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Sleep session info
    sleep_date DATE NOT NULL,                    -- Date of sleep (YYYY-MM-DD)
    sleep_stage VARCHAR(50) NOT NULL,           -- Sleep stage/category
    
    -- Timing (timezone-aware)
    start_datetime DATETIME NOT NULL,           -- Stage start time
    end_datetime DATETIME NOT NULL,             -- Stage end time
    duration_minutes INTEGER NOT NULL,          -- Duration in minutes
    
    -- Source info
    source_name VARCHAR(100),                   -- Data source
    source_version VARCHAR(50),                 -- Source version
    device_info VARCHAR(100),                   -- Device info
    
    -- Metadata and timestamps
    metadata TEXT,                              -- JSON metadata
    creation_date DATETIME,                     -- Health app creation time
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_sleep_date (sleep_date),
    INDEX idx_sleep_stage (sleep_stage),
    INDEX idx_sleep_datetime (start_datetime)
);

-- Breathing Disturbances Table
CREATE TABLE sleep_breathing_disturbances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Timing
    measurement_date DATE NOT NULL,             -- Date of measurement
    start_datetime DATETIME NOT NULL,           -- Measurement start
    end_datetime DATETIME NOT NULL,             -- Measurement end
    
    -- Breathing data
    disturbance_value REAL NOT NULL,            -- Disturbance measurement
    unit VARCHAR(20),                           -- Unit of measurement
    
    -- Source info
    source_name VARCHAR(100),
    source_version VARCHAR(50),
    device_info VARCHAR(100),
    
    -- Metadata and timestamps
    metadata TEXT,
    creation_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_breathing_date (measurement_date),
    INDEX idx_breathing_datetime (start_datetime)
);

-- Wrist Temperature Table
CREATE TABLE sleep_wrist_temperature (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Timing
    measurement_date DATE NOT NULL,             -- Date of measurement
    start_datetime DATETIME NOT NULL,           -- Measurement start
    end_datetime DATETIME NOT NULL,             -- Measurement end
    
    -- Temperature data
    temperature_celsius REAL NOT NULL,          -- Temperature in Celsius
    unit VARCHAR(20),                           -- Unit (should be degC)
    
    -- Source info
    source_name VARCHAR(100),
    source_version VARCHAR(50),
    device_info VARCHAR(100),
    
    -- Metadata and timestamps
    metadata TEXT,
    creation_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_temperature_date (measurement_date),
    INDEX idx_temperature_datetime (start_datetime)
);

-- Daily Sleep Summary Table (aggregated from all sources)
CREATE TABLE daily_sleep_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sleep_date DATE NOT NULL UNIQUE,
    
    -- Sleep timing
    bedtime DATETIME,                           -- Time went to bed
    sleep_start DATETIME,                       -- Time fell asleep
    sleep_end DATETIME,                         -- Time woke up
    wake_time DATETIME,                         -- Time got out of bed
    
    -- Sleep duration (minutes)
    time_in_bed INTEGER,                        -- Total time in bed
    time_asleep INTEGER,                        -- Total time asleep
    time_awake INTEGER,                         -- Time awake in bed
    
    -- Sleep stages (if available)
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,
    light_sleep_minutes INTEGER,
    
    -- Sleep quality metrics
    sleep_efficiency REAL,                      -- time_asleep / time_in_bed
    wake_up_count INTEGER,                      -- Number of wake-ups
    
    -- Breathing and temperature (daily averages)
    avg_breathing_disturbances REAL,           -- Average breathing disturbances
    avg_wrist_temperature REAL,                -- Average wrist temperature
    min_wrist_temperature REAL,                -- Minimum wrist temperature
    max_wrist_temperature REAL,                -- Maximum wrist temperature
    
    -- Source tracking
    primary_source VARCHAR(100),               -- Main data source
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
        """)
        
        print(f"💡 IMPLEMENTATION NOTES:")
        print("   • Three separate tables for different sleep data types")
        print("   • Daily summaries aggregate all sleep metrics")
        print("   • Timezone-aware datetime storage throughout")
        print("   • Flexible metadata fields for future extensions")
        print("   • Proper indexing for query performance")
        
        print(f"\n🔧 NEXT STEPS:")
        print("   1. Add parsing for all three sleep data types to apple_health.py")
        print("   2. Create sleep-specific tools in health_tools.py:")
        print("      • Sleep stage analysis")
        print("      • Breathing disturbance tracking")
        print("      • Temperature pattern analysis")
        print("   3. Add comprehensive sleep queries to health_data_service.py")
        print("   4. Test with actual sleep data parsing")
        print("   5. Create sleep analytics dashboard in UI")


def main():
    """Run comprehensive sleep data analysis."""
    print("💤 Apple Health Comprehensive Sleep Data Analyzer")
    print("=" * 60)
    
    # Look for Apple Health export
    possible_paths = [
        "data/raw/apple_health_export/export.xml",
        "data/raw/export.xml", 
        "export.xml"
    ]
    
    xml_path = None
    for path in possible_paths:
        if Path(path).exists():
            xml_path = path
            break
    
    if not xml_path:
        print("❌ Apple Health export not found!")
        print("\nPlace export.xml in one of these locations:")
        for path in possible_paths:
            print(f"   • {path}")
        return
    
    # Run comprehensive analysis
    analyzer = ComprehensiveSleepAnalyzer(xml_path)
    analyzer.analyze_all_sleep_data()


if __name__ == "__main__":
    main() 