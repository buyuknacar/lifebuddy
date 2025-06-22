#!/usr/bin/env python3
"""
Apple Health Data Exploration Script

This script analyzes the complete Apple Health export XML to discover all available
record types, including sleep data, nutrition, environmental data, and more.
Helps identify what data we could potentially parse beyond the current 9 core metrics.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set


class AppleHealthExplorer:
    """Explores Apple Health export to discover all available data types."""
    
    def __init__(self, xml_path: str):
        self.xml_path = Path(xml_path)
        self.record_types = defaultdict(int)
        self.record_samples = defaultdict(list)
        self.workout_types = Counter()
        self.source_names = Counter()
        self.units = defaultdict(set)
        self.workout_samples = []
        
    def explore_all_data(self):
        """Analyze the complete Apple Health export."""
        print(f"🔍 Exploring Apple Health export: {self.xml_path}")
        print(f"📁 File size: {self.xml_path.stat().st_size / (1024*1024):.1f} MB")
        print("=" * 80)
        
        if not self.xml_path.exists():
            print(f"❌ File not found: {self.xml_path}")
            return
        
        # Parse XML efficiently
        context = ET.iterparse(self.xml_path, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        total_records = 0
        total_workouts = 0
        
        print("📊 Parsing XML... (this may take a moment for large files)")
        
        for event, elem in context:
            if event == 'end':
                if elem.tag == 'Record':
                    self._analyze_record(elem)
                    total_records += 1
                    
                elif elem.tag == 'Workout':
                    self._analyze_workout(elem)
                    total_workouts += 1
                
                # Clear element to save memory
                elem.clear()
                
                # Progress indicator
                if (total_records + total_workouts) % 100000 == 0:
                    print(f"   Processed {total_records:,} records, {total_workouts:,} workouts...")
        
        print(f"✅ Completed! Processed {total_records:,} records and {total_workouts:,} workouts")
        print()
        
        # Generate comprehensive report
        self._print_comprehensive_report()
    
    def _analyze_record(self, elem):
        """Analyze a health record element."""
        record_type = elem.get('type', 'Unknown')
        value = elem.get('value', '')
        unit = elem.get('unit', '')
        source_name = elem.get('sourceName', '')
        start_date = elem.get('startDate', '')
        end_date = elem.get('endDate', '')
        
        # Count record types
        self.record_types[record_type] += 1
        
        # Store sample data (max 3 samples per type)
        if len(self.record_samples[record_type]) < 3:
            self.record_samples[record_type].append({
                'value': value,
                'unit': unit,
                'source': source_name,
                'start_date': start_date,
                'end_date': end_date
            })
        
        # Track units and sources
        if unit:
            self.units[record_type].add(unit)
        if source_name:
            self.source_names[source_name] += 1
    
    def _analyze_workout(self, elem):
        """Analyze a workout element."""
        workout_type = elem.get('workoutActivityType', 'Unknown')
        self.workout_types[workout_type] += 1
        
        # Store detailed workout sample for analysis
        if len(self.workout_samples) < 5:  # Store first 5 workout samples
            workout_sample = {
                'workoutActivityType': elem.get('workoutActivityType', ''),
                'startDate': elem.get('startDate', ''),
                'endDate': elem.get('endDate', ''),
                'duration': elem.get('duration', ''),
                'durationUnit': elem.get('durationUnit', ''),
                'totalEnergyBurned': elem.get('totalEnergyBurned', ''),
                'totalEnergyBurnedUnit': elem.get('totalEnergyBurnedUnit', ''),
                'totalDistance': elem.get('totalDistance', ''),
                'totalDistanceUnit': elem.get('totalDistanceUnit', ''),
                'sourceName': elem.get('sourceName', ''),
                'sourceVersion': elem.get('sourceVersion', ''),
                'creationDate': elem.get('creationDate', ''),
                'statistics': []
            }
            
            # Parse nested WorkoutStatistics
            for child in elem:
                if child.tag == 'WorkoutStatistics':
                    stat = {
                        'type': child.get('type', ''),
                        'startDate': child.get('startDate', ''),
                        'endDate': child.get('endDate', ''),
                        'average': child.get('average', ''),
                        'maximum': child.get('maximum', ''),
                        'minimum': child.get('minimum', ''),
                        'sum': child.get('sum', ''),
                        'unit': child.get('unit', '')
                    }
                    workout_sample['statistics'].append(stat)
            
            self.workout_samples.append(workout_sample)
    
    def _print_comprehensive_report(self):
        """Print a comprehensive analysis report."""
        print("📊 APPLE HEALTH DATA ANALYSIS REPORT")
        print("=" * 80)
        
        # 1. Overall Statistics
        print(f"📈 OVERVIEW:")
        print(f"   • Total Record Types: {len(self.record_types)}")
        print(f"   • Total Records: {sum(self.record_types.values()):,}")
        print(f"   • Total Workout Types: {len(self.workout_types)}")
        print(f"   • Total Workouts: {sum(self.workout_types.values()):,}")
        print(f"   • Data Sources: {len(self.source_names)}")
        print()
        
        # 2. Sleep Data Analysis
        self._analyze_sleep_data()
        
        # 3. Categorized Record Types
        self._categorize_record_types()
        
        # 4. Workout Analysis
        self._analyze_workouts()
        
        # 4.5. Detailed Workout Structure Analysis
        self._analyze_workout_structure()
        
        # 5. Data Sources
        self._analyze_sources()
        
        # 6. Currently Parsed vs Available
        self._compare_current_parsing()
    
    def _analyze_sleep_data(self):
        """Analyze sleep-related data specifically."""
        print("💤 SLEEP DATA ANALYSIS:")
        print("-" * 40)
        
        sleep_types = {k: v for k, v in self.record_types.items() 
                      if 'sleep' in k.lower() or 'bed' in k.lower()}
        
        if sleep_types:
            print(f"✅ Found {len(sleep_types)} sleep-related record types:")
            for record_type, count in sorted(sleep_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {record_type}")
                print(f"     Records: {count:,}")
                
                # Show sample data
                if record_type in self.record_samples:
                    sample = self.record_samples[record_type][0]
                    print(f"     Unit: {sample['unit'] or 'N/A'}")
                    print(f"     Sample: {sample['value']} ({sample['start_date'][:16]})")
                    print(f"     Source: {sample['source']}")
                print()
        else:
            print("❌ No sleep data found in export")
        print()
    
    def _categorize_record_types(self):
        """Categorize all record types by health domain."""
        print("🏥 RECORD TYPES BY CATEGORY:")
        print("-" * 40)
        
        categories = {
            'Sleep & Rest': ['sleep', 'bed', 'rest'],
            'Heart & Cardiovascular': ['heart', 'blood', 'pressure', 'pulse'],
            'Activity & Fitness': ['step', 'distance', 'energy', 'exercise', 'workout', 'active'],
            'Body Measurements': ['body', 'weight', 'height', 'mass', 'fat', 'lean'],
            'Nutrition': ['dietary', 'nutrition', 'vitamin', 'mineral', 'protein', 'carb', 'fat'],
            'Respiratory': ['respiratory', 'oxygen', 'breathing', 'lung'],
            'Environmental': ['audio', 'noise', 'environment', 'uv'],
            'Reproductive Health': ['menstrual', 'ovulation', 'pregnancy'],
            'Mental Health': ['mindful', 'mood', 'anxiety'],
            'Lab Results': ['cholesterol', 'glucose', 'insulin', 'hemoglobin'],
        }
        
        categorized = defaultdict(list)
        uncategorized = []
        
        for record_type, count in self.record_types.items():
            categorized_flag = False
            for category, keywords in categories.items():
                if any(keyword in record_type.lower() for keyword in keywords):
                    categorized[category].append((record_type, count))
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                uncategorized.append((record_type, count))
        
        # Print categorized results
        for category, records in categorized.items():
            if records:
                total_records = sum(count for _, count in records)
                print(f"📊 {category} ({len(records)} types, {total_records:,} records):")
                
                # Sort by count and show top items
                records.sort(key=lambda x: x[1], reverse=True)
                for record_type, count in records[:5]:  # Top 5
                    short_name = record_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
                    print(f"   • {short_name:<30} {count:>8,} records")
                
                if len(records) > 5:
                    print(f"   ... and {len(records) - 5} more types")
                print()
        
        # Show uncategorized
        if uncategorized:
            print(f"❓ UNCATEGORIZED ({len(uncategorized)} types):")
            uncategorized.sort(key=lambda x: x[1], reverse=True)
            for record_type, count in uncategorized[:10]:  # Top 10
                short_name = record_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
                print(f"   • {short_name:<30} {count:>8,} records")
            if len(uncategorized) > 10:
                print(f"   ... and {len(uncategorized) - 10} more")
            print()
    
    def _analyze_workouts(self):
        """Analyze workout types."""
        print("🏃 WORKOUT ANALYSIS:")
        print("-" * 40)
        
        if self.workout_types:
            print(f"Found {len(self.workout_types)} workout types:")
            for workout_type, count in self.workout_types.most_common(10):
                clean_name = workout_type.replace('HKWorkoutActivityType', '')
                print(f"   • {clean_name:<25} {count:>6,} workouts")
            
            if len(self.workout_types) > 10:
                print(f"   ... and {len(self.workout_types) - 10} more types")
        else:
            print("❌ No workout data found")
        print()
    
    def _analyze_workout_structure(self):
        """Analyze detailed workout structure."""
        print("🏃 WORKOUT STRUCTURE ANALYSIS:")
        print("-" * 40)
        
        if self.workout_samples:
            print(f"Found {len(self.workout_samples)} workout samples:")
            for workout_sample in self.workout_samples[:5]:  # Show first 5 samples
                print(f"🏃 Workout Type: {workout_sample['workoutActivityType']}")
                print(f"📅 Start Date: {workout_sample['startDate']}")
                print(f"📅 End Date: {workout_sample['endDate']}")
                print(f"🕒 Duration: {workout_sample['duration']} {workout_sample['durationUnit']}")
                print(f"🔥 Total Energy Burned: {workout_sample['totalEnergyBurned']} {workout_sample['totalEnergyBurnedUnit']}")
                print(f"🏃 Total Distance: {workout_sample['totalDistance']} {workout_sample['totalDistanceUnit']}")
                print(f"🏷 Source: {workout_sample['sourceName']}")
                print(f"📅 Creation Date: {workout_sample['creationDate']}")
                print("🏋️ Statistics:")
                for stat in workout_sample['statistics']:
                    print(f"   • {stat['type']} - {stat['average']} {stat['unit']}")
                print()
        else:
            print("❌ No workout data found")
        print()
    
    def _analyze_sources(self):
        """Analyze data sources."""
        print("📱 DATA SOURCES:")
        print("-" * 40)
        
        print(f"Top data sources (out of {len(self.source_names)} total):")
        for source, count in self.source_names.most_common(10):
            print(f"   • {source:<30} {count:>8,} records")
        print()
    
    def _compare_current_parsing(self):
        """Compare what we currently parse vs what's available."""
        print("🔍 CURRENT PARSING vs AVAILABLE DATA:")
        print("-" * 40)
        
        # Current target metrics from apple_health.py
        current_metrics = {
            'HKQuantityTypeIdentifierActiveEnergyBurned',
            'HKQuantityTypeIdentifierHeartRate',
            'HKQuantityTypeIdentifierBasalEnergyBurned',
            'HKQuantityTypeIdentifierDistanceWalkingRunning',
            'HKQuantityTypeIdentifierStepCount',
            'HKQuantityTypeIdentifierAppleExerciseTime',
            'HKQuantityTypeIdentifierBodyMassIndex',
            'HKQuantityTypeIdentifierBodyMass',
            'HKQuantityTypeIdentifierBodyFatPercentage'
        }
        
        print(f"✅ CURRENTLY PARSED ({len(current_metrics)} types):")
        for metric in sorted(current_metrics):
            count = self.record_types.get(metric, 0)
            short_name = metric.replace('HKQuantityTypeIdentifier', '')
            print(f"   • {short_name:<30} {count:>8,} records")
        
        print(f"\n📊 AVAILABLE BUT NOT PARSED ({len(self.record_types) - len(current_metrics)} types):")
        unparsed = {k: v for k, v in self.record_types.items() if k not in current_metrics}
        
        # Show top unparsed types by record count
        unparsed_sorted = sorted(unparsed.items(), key=lambda x: x[1], reverse=True)
        for record_type, count in unparsed_sorted[:15]:  # Top 15
            short_name = record_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
            print(f"   • {short_name:<30} {count:>8,} records")
        
        if len(unparsed_sorted) > 15:
            print(f"   ... and {len(unparsed_sorted) - 15} more types")
        
        print(f"\n💡 POTENTIAL EXPANSIONS:")
        print("   • Sleep data for sleep quality analysis")
        print("   • Nutrition data for diet tracking")
        print("   • Environmental data (noise, UV exposure)")
        print("   • Mental health data (mindfulness, mood)")
        print("   • Detailed cardiovascular metrics")


def main():
    """Run Apple Health data exploration."""
    print("🍎 Apple Health Data Explorer")
    print("=" * 50)
    
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
        print("\n📋 To use this script:")
        print("1. Export your Apple Health data:")
        print("   • Open Health app → Profile → Export All Health Data")
        print("2. Extract the ZIP file")
        print("3. Place export.xml in one of these locations:")
        for path in possible_paths:
            print(f"   • {path}")
        return
    
    # Run exploration
    explorer = AppleHealthExplorer(xml_path)
    explorer.explore_all_data()
    
    print("\n🎯 NEXT STEPS:")
    print("   • Review sleep data types for potential sleep table")
    print("   • Consider expanding parsing to include nutrition data")
    print("   • Evaluate environmental and mental health metrics")
    print("   • Update apple_health.py target_metrics if needed")


if __name__ == "__main__":
    main() 