#!/usr/bin/env python3

"""
Enhanced Codebase Indexing System - Demonstration Script

This script demonstrates the advanced capabilities of the enhanced codebase indexing system,
including sophisticated collection creation, intelligent code analysis, and comprehensive reporting.

Usage:
    python3 demo_enhanced_indexing.py [--demo-mode] [--qdrant-url URL] [--api-key KEY]

Example:
    python3 demo_enhanced_indexing.py --demo-mode --qdrant-url http://localhost:6333 --api-key your-key
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add the current directory to the path to import our indexer
sys.path.append(str(Path(__file__).parent))

try:
    from enhanced_codebase_indexer import (
        EnhancedCodebaseIndexer,
        DistanceMetric,
        QuantizationType,
        VectorParams,
        CollectionConfig
    )
except ImportError:
    print("❌ Enhanced indexer module not found. Make sure enhanced_codebase_indexer.py is in the same directory.")
    sys.exit(1)

class IndexingDemo:
    """Demonstration of enhanced codebase indexing capabilities."""

    def __init__(self, qdrant_url: str, api_key: str):
        self.indexer = EnhancedCodebaseIndexer(qdrant_url, api_key)
        self.demo_collections = []

    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f"🚀 {title}")
        print(f"{'='*60}")

    def print_step(self, step: str):
        """Print a step description."""
        print(f"\n📋 {step}")
        print("-" * 50)

    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")

    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")

    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️  {message}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")

    def demo_connection_test(self):
        """Demonstrate connection testing."""
        self.print_header("Connection and Health Check")

        self.print_step("Testing Qdrant connection...")
        try:
            collections = self.indexer.list_collections()
            self.print_success(f"Connected successfully! Found {len(collections)} existing collections.")

            if collections:
                self.print_info("Existing collections:")
                for i, collection in enumerate(collections[:5], 1):
                    print(f"  {i}. {collection.get('name', 'Unknown')}")
                if len(collections) > 5:
                    print(f"  ... and {len(collections) - 5} more")
        except Exception as e:
            self.print_error(f"Connection failed: {e}")
            return False

        return True

    def demo_collection_templates(self):
        """Demonstrate different collection templates."""
        self.print_header("Collection Template Demonstration")

        templates = [
            ("demo-small", "small_codebase", 384, False, False),
            ("demo-medium", "medium_codebase", 384, True, True),
            ("demo-large", "large_codebase", 768, True, True),
            ("demo-performance", "high_performance", 384, True, True)
        ]

        for name, template_type, vector_size, quantization, sparse in templates:
            self.print_step(f"Creating {template_type} template collection: {name}")

            try:
                # Create schema based on template type
                if template_type == "small_codebase":
                    schema = self.indexer.create_collection_schema(
                        collection_name=name,
                        vector_size=vector_size,
                        distance_metric=DistanceMetric.COSINE,
                        enable_quantization=quantization,
                        enable_sparse_vectors=sparse,
                        replication_factor=1
                    )
                elif template_type == "medium_codebase":
                    schema = self.indexer.create_collection_schema(
                        collection_name=name,
                        vector_size=vector_size,
                        distance_metric=DistanceMetric.COSINE,
                        enable_quantization=quantization,
                        quantization_type=QuantizationType.SCALAR,
                        enable_sparse_vectors=sparse,
                        replication_factor=1,
                        shard_number=2
                    )
                elif template_type == "large_codebase":
                    schema = self.indexer.create_collection_schema(
                        collection_name=name,
                        vector_size=vector_size,
                        distance_metric=DistanceMetric.COSINE,
                        enable_quantization=quantization,
                        quantization_type=QuantizationType.PRODUCT,
                        enable_sparse_vectors=sparse,
                        replication_factor=2,
                        shard_number=4
                    )
                else:  # high_performance
                    schema = self.indexer.create_collection_schema(
                        collection_name=name,
                        vector_size=vector_size,
                        distance_metric=DistanceMetric.COSINE,
                        enable_quantization=quantization,
                        quantization_type=QuantizationType.SCALAR,
                        enable_sparse_vectors=sparse,
                        replication_factor=3,
                        shard_number=6
                    )

                if self.indexer.create_collection(name, schema):
                    self.print_success(f"Created {template_type} collection")
                    self.demo_collections.append(name)

                    # Show key configuration details
                    self.print_info("Key configuration:")
                    print(f"    Vector size: {vector_size}")
                    print(f"    Distance metric: {schema['vectors']['distance']}")
                    print(f"    Quantization: {'Enabled' if quantization else 'Disabled'}")
                    print(f"    Sparse vectors: {'Enabled' if sparse else 'Disabled'}")
                    print(f"    Replication factor: {schema.get('replication_factor', 1)}")
                    if 'shard_number' in schema:
                        print(f"    Shards: {schema['shard_number']}")
                else:
                    self.print_warning(f"Failed to create {name} (may already exist)")

            except Exception as e:
                self.print_error(f"Error creating {name}: {e}")

            time.sleep(1)  # Brief pause between operations

    def demo_code_analysis(self):
        """Demonstrate advanced code analysis capabilities."""
        self.print_header("Advanced Code Analysis Demonstration")

        # Create sample code files for analysis
        sample_files = self.create_sample_code_files()

        self.print_step("Analyzing sample Python code...")

        try:
            # Analyze the sample directory
            sample_dir = Path("demo_code_samples")
            if sample_dir.exists():
                index_data = self.indexer.index_directory(sample_dir, max_files=10)

                self.print_success("Code analysis completed!")
                self.print_info("Analysis Results:")

                stats = index_data['statistics']
                print(f"    Files indexed: {index_data['total_files']}")
                print(f"    Chunks created: {index_data['total_chunks']}")
                print(f"    Languages found: {len(stats['by_language'])}")

                self.print_info("Language distribution:")
                for lang, count in stats['by_language'].items():
                    print(f"    {lang}: {count} files")

                self.print_info("Complexity distribution:")
                for level, count in stats['complexity_distribution'].items():
                    print(f"    {level}: {count} files")

                self.print_info("Code structure analysis:")
                structure = stats['function_class_counts']
                print(f"    Functions found: {structure['total_functions']}")
                print(f"    Classes found: {structure['total_classes']}")
                print(f"    Import statements: {structure['total_imports']}")

                if stats['top_keywords']:
                    self.print_info("Top keywords (first 5):")
                    for keyword, count in list(stats['top_keywords'].items())[:5]:
                        print(f"    {keyword}: {count} occurrences")
            else:
                self.print_warning("Sample code directory not found, skipping analysis demo")

        except Exception as e:
            self.print_error(f"Analysis failed: {e}")

    def create_sample_code_files(self):
        """Create sample code files for demonstration."""
        sample_dir = Path("demo_code_samples")
        sample_dir.mkdir(exist_ok=True)

        # Python sample
        python_sample = '''#!/usr/bin/env python3
"""
Sample Python module demonstrating various code patterns.
This module includes classes, functions, error handling, and imports.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import requests

class DataProcessor:
    """A sample data processing class with various methods."""

    def __init__(self, config_path: str):
        """Initialize the processor with configuration."""
        self.config_path = config_path
        self.data: Dict[str, any] = {}
        self.processed_count = 0

    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.data.update(config)
                return True
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config: {e}")
            return False

    def process_data(self, input_data: List[Dict]) -> List[Dict]:
        """Process a list of data dictionaries."""
        processed = []

        for item in input_data:
            if self.validate_item(item):
                processed_item = self.transform_item(item)
                processed.append(processed_item)
                self.processed_count += 1

        return processed

    def validate_item(self, item: Dict) -> bool:
        """Validate a single data item."""
        required_fields = ['id', 'name', 'value']

        for field in required_fields:
            if field not in item:
                print(f"Missing required field: {field}")
                return False

        if not isinstance(item['value'], (int, float)):
            print("Value must be numeric")
            return False

        return True

    def transform_item(self, item: Dict) -> Dict:
        """Transform a data item according to business rules."""
        transformed = item.copy()

        # Apply transformations
        transformed['processed'] = True
        transformed['normalized_value'] = item['value'] / 100.0

        # Add metadata
        transformed['processing_timestamp'] = time.time()

        return transformed

    async def fetch_remote_data(self, url: str) -> Optional[Dict]:
        """Fetch data from a remote API endpoint."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch data: {e}")
            return None

    def get_statistics(self) -> Dict[str, any]:
        """Get processing statistics."""
        return {
            'processed_count': self.processed_count,
            'config_loaded': bool(self.data),
            'last_update': time.time()
        }

def main():
    """Main function demonstrating the DataProcessor usage."""
    processor = DataProcessor('config.json')

    if not processor.load_config():
        print("Failed to load configuration, using defaults")

    sample_data = [
        {'id': 1, 'name': 'Item 1', 'value': 100},
        {'id': 2, 'name': 'Item 2', 'value': 250},
        {'id': 3, 'name': 'Item 3', 'value': 75}
    ]

    results = processor.process_data(sample_data)
    print(f"Processed {len(results)} items")

    stats = processor.get_statistics()
    print(f"Statistics: {stats}")

if __name__ == "__main__":
    main()
'''

        # JavaScript sample
        javascript_sample = '''/**
 * Sample JavaScript module demonstrating modern ES6+ patterns.
 * Includes classes, async/await, destructuring, and error handling.
 */

import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';

/**
 * A sample service class for managing user data.
 */
class UserService extends EventEmitter {
    constructor(dataPath = './users.json') {
        super();
        this.dataPath = dataPath;
        this.users = new Map();
        this.initialized = false;
    }

    /**
     * Initialize the service by loading user data.
     */
    async initialize() {
        try {
            const data = await fs.readFile(this.dataPath, 'utf8');
            const users = JSON.parse(data);

            for (const user of users) {
                this.users.set(user.id, user);
            }

            this.initialized = true;
            this.emit('initialized', this.users.size);

        } catch (error) {
            if (error.code === 'ENOENT') {
                console.log('User data file not found, starting with empty dataset');
                this.initialized = true;
            } else {
                console.error('Failed to initialize user service:', error);
                throw error;
            }
        }
    }

    /**
     * Create a new user with validation.
     */
    async createUser({ name, email, age }) {
        if (!this.initialized) {
            throw new Error('Service not initialized');
        }

        // Validation
        if (!name || !email) {
            throw new Error('Name and email are required');
        }

        if (age < 0 || age > 150) {
            throw new Error('Invalid age provided');
        }

        const id = this.generateId();
        const user = {
            id,
            name,
            email: email.toLowerCase(),
            age,
            createdAt: new Date().toISOString(),
            active: true
        };

        this.users.set(id, user);
        this.emit('userCreated', user);

        await this.saveData();
        return user;
    }

    /**
     * Update an existing user.
     */
    async updateUser(id, updates) {
        const user = this.users.get(id);
        if (!user) {
            throw new Error(`User with id ${id} not found`);
        }

        const updatedUser = {
            ...user,
            ...updates,
            updatedAt: new Date().toISOString()
        };

        this.users.set(id, updatedUser);
        this.emit('userUpdated', updatedUser);

        await this.saveData();
        return updatedUser;
    }

    /**
     * Find users matching criteria.
     */
    findUsers(criteria = {}) {
        const results = [];

        for (const user of this.users.values()) {
            let matches = true;

            for (const [key, value] of Object.entries(criteria)) {
                if (user[key] !== value) {
                    matches = false;
                    break;
                }
            }

            if (matches) {
                results.push(user);
            }
        }

        return results;
    }

    /**
     * Get user statistics.
     */
    getStatistics() {
        const users = Array.from(this.users.values());
        const activeUsers = users.filter(u => u.active);

        return {
            total: users.length,
            active: activeUsers.length,
            averageAge: users.reduce((sum, u) => sum + u.age, 0) / users.length,
            oldestUser: Math.max(...users.map(u => u.age)),
            youngestUser: Math.min(...users.map(u => u.age))
        };
    }

    /**
     * Generate a unique user ID.
     */
    generateId() {
        return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Save user data to file.
     */
    async saveData() {
        try {
            const users = Array.from(this.users.values());
            await fs.writeFile(this.dataPath, JSON.stringify(users, null, 2));
        } catch (error) {
            console.error('Failed to save user data:', error);
            this.emit('saveError', error);
        }
    }
}

/**
 * Utility functions for user management.
 */
export const UserUtils = {
    /**
     * Validate email format.
     */
    isValidEmail(email) {
        const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Format user display name.
     */
    formatDisplayName(user) {
        return `${user.name} (${user.email})`;
    },

    /**
     * Calculate user age from birth date.
     */
    calculateAge(birthDate) {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();

        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }

        return age;
    }
};

export default UserService;
'''

        # Write sample files
        (sample_dir / "sample_processor.py").write_text(python_sample)
        (sample_dir / "user_service.js").write_text(javascript_sample)

        # Create a simple README
        readme_content = '''# Demo Code Samples

This directory contains sample code files for demonstrating the enhanced indexing system.

## Files:
- `sample_processor.py` - Python data processing class
- `user_service.js` - JavaScript user management service

These files showcase various programming patterns that the indexer can analyze:
- Class definitions and methods
- Function signatures and complexity
- Import/export statements
- Error handling patterns
- Async/await usage
- Type annotations
- Documentation strings
'''
        (sample_dir / "README.md").write_text(readme_content)

        self.print_success(f"Created sample code files in {sample_dir}")
        return sample_dir

    def demo_collection_comparison(self):
        """Demonstrate collection comparison capabilities."""
        self.print_header("Collection Comparison")

        if len(self.demo_collections) >= 2:
            collection1 = self.demo_collections[0]
            collection2 = self.demo_collections[1]

            self.print_step(f"Comparing collections: {collection1} vs {collection2}")

            try:
                info1 = self.indexer.get_collection_info(collection1)
                info2 = self.indexer.get_collection_info(collection2)

                if info1 and info2:
                    result1 = info1.get('result', {})
                    result2 = info2.get('result', {})

                    self.print_info(f"{collection1} configuration:")
                    self.print_collection_summary(result1)

                    self.print_info(f"{collection2} configuration:")
                    self.print_collection_summary(result2)

                    # Highlight key differences
                    config1 = result1.get('config', {}).get('params', {})
                    config2 = result2.get('config', {}).get('params', {})

                    vectors1 = config1.get('vectors', {})
                    vectors2 = config2.get('vectors', {})

                    self.print_info("Key differences:")
                    if vectors1.get('size') != vectors2.get('size'):
                        print(f"    Vector size: {vectors1.get('size')} vs {vectors2.get('size')}")

                    if config1.get('replication_factor') != config2.get('replication_factor'):
                        print(f"    Replication: {config1.get('replication_factor')} vs {config2.get('replication_factor')}")

                else:
                    self.print_warning("Could not retrieve collection information for comparison")

            except Exception as e:
                self.print_error(f"Comparison failed: {e}")
        else:
            self.print_warning("Need at least 2 collections for comparison")

    def print_collection_summary(self, collection_info: Dict):
        """Print a summary of collection information."""
        config = collection_info.get('config', {}).get('params', {})
        vectors = config.get('vectors', {})

        print(f"    Vector size: {vectors.get('size', 'Unknown')}")
        print(f"    Distance metric: {vectors.get('distance', 'Unknown')}")
        print(f"    Points count: {collection_info.get('points_count', 0)}")
        print(f"    Vectors count: {collection_info.get('vectors_count', 0)}")
        print(f"    Replication factor: {config.get('replication_factor', 1)}")

        if 'quantization_config' in config:
            print("    Quantization: Enabled")
        else:
            print("    Quantization: Disabled")

    def cleanup_demo_collections(self):
        """Clean up demo collections."""
        self.print_header("Cleanup")

        self.print_step("Removing demo collections...")

        for collection_name in self.demo_collections:
            try:
                if self.indexer.delete_collection(collection_name):
                    self.print_success(f"Deleted {collection_name}")
                else:
                    self.print_warning(f"Failed to delete {collection_name}")
            except Exception as e:
                self.print_error(f"Error deleting {collection_name}: {e}")

        # Clean up sample files
        sample_dir = Path("demo_code_samples")
        if sample_dir.exists():
            try:
                import shutil
                shutil.rmtree(sample_dir)
                self.print_success("Removed sample code files")
            except Exception as e:
                self.print_warning(f"Could not remove sample files: {e}")

    def run_full_demo(self):
        """Run the complete demonstration."""
        self.print_header("Enhanced Codebase Indexing System - Demo")
        print("This demonstration showcases the advanced capabilities of the enhanced indexing system.")
        print("The demo will create sample collections, analyze code, and demonstrate various features.")

        try:
            # Step 1: Connection test
            if not self.demo_connection_test():
                return False

            # Step 2: Collection templates
            self.demo_collection_templates()

            # Step 3: Code analysis
            self.demo_code_analysis()

            # Step 4: Collection comparison
            self.demo_collection_comparison()

            # Step 5: Final summary
            self.print_header("Demo Summary")
            self.print_success("Enhanced indexing demonstration completed!")
            self.print_info("Key features demonstrated:")
            print("    ✓ Multiple collection templates (small, medium, large, high-performance)")
            print("    ✓ Advanced schema configuration with quantization and sharding")
            print("    ✓ Intelligent code analysis with structure extraction")
            print("    ✓ Comprehensive statistics and reporting")
            print("    ✓ Collection comparison and management")

            self.print_info("\nNext steps:")
            print("    • Try indexing your own codebase with ./enhanced_index_codebase.sh")
            print("    • Explore different collection templates for your use case")
            print("    • Integrate with your development workflow")
            print("    • Set up production monitoring and maintenance")

            return True

        except KeyboardInterrupt:
            self.print_warning("\nDemo interrupted by user")
            return False
        except Exception as e:
            self.print_error(f"Demo failed: {e}")
            return False
        finally:
            # Always cleanup, regardless of success/failure
            try:
                cleanup_response = input("\nDo you want to cleanup demo collections? (Y/n): ").strip().lower()
                if cleanup_response != 'n':
                    self.cleanup_demo_collections()
            except KeyboardInterrupt:
                self.print_info("\nSkipping cleanup")


def main():
    """Main demonstration entry point."""
    parser = argparse.ArgumentParser(
        description='Enhanced Codebase Indexing System - Interactive Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This demonstration showcases the advanced features of the enhanced indexing system:

• Multiple collection templates optimized for different use cases
• Intelligent code analysis with structure extraction
• Advanced vector database configurations
• Comprehensive reporting and analytics
• Collection management and comparison tools

The demo will create temporary collections for demonstration purposes.
You'll be prompted to clean them up at the end.

Prerequisites:
• Qdrant server running and accessible
• Valid API key for authentication
• Python dependencies installed (requests, pathlib2)

Examples:
    # Basic demo with default settings
    python3 demo_enhanced_indexing.py

    # Demo with custom Qdrant instance
    python3 demo_enhanced_indexing.py --qdrant-url https://my-qdrant:6333 --api-key my-key

    # Quick demo mode (no interactive prompts)
    python3 demo_enhanced_indexing.py --demo-mode
        """
    )

    parser.add_argument(
        '--qdrant-url',
        default='http://localhost:6333',
        help='Qdrant server URL (default: https://pve.local:6333)'
    )

    parser.add_argument(
        '--api-key',
        default='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.LB_x2qCirzOsvCL9WvWFadKPRUPYg73kOW3KXkxb_is',
        help='Qdrant API key for authentication'
    )

    parser.add_argument(
        '--demo-mode',
        action='store_true',
        help='Run demo without interactive prompts'
    )

    args = parser.parse_args()

    print("🚀 Enhanced Codebase Indexing System - Demo")
    print("=" * 50)

    if not args.demo_mode:
        print(f"\nConnection settings:")
        print(f"  Qdrant URL: {args.qdrant_url}")
        print(f"  API Key: {'*' * 20}...{args.api_key[-8:] if len(args.api_key) > 8 else '***'}")

        response = input("\nProceed with the demonstration? (Y/n): ").strip().lower()
        if response == 'n':
            print("Demo cancelled by user.")
            return 0

    try:
        demo = IndexingDemo(args.qdrant_url, args.api_key)
        success = demo.run_full_demo()

        if success:
            print("\n🎉 Demo completed successfully!")
            print("\nTo get started with your own codebase:")
            print("  ./enhanced_index_codebase.sh --help")
            return 0
        else:
            print("\n⚠️  Demo completed with issues.")
            return 1

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
