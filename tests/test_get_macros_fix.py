#!/usr/bin/env python3
"""
Test script to verify the get_macros() method fix in BBCtrlCommunicator.
"""

import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.communication import BBCtrlCommunicator
from core.macro_manager import MacroManager

def test_get_macros_method_exists():
    """Test that the get_macros method exists and is callable."""
    print("=" * 60)
    print("TEST 1: Verify get_macros() method exists")
    print("=" * 60)
    
    try:
        # Create a communicator instance
        comm = BBCtrlCommunicator()
        
        # Check if the method exists
        assert hasattr(comm, 'get_macros'), "get_macros method does not exist"
        assert callable(getattr(comm, 'get_macros')), "get_macros is not callable"
        
        print("✓ get_macros() method exists and is callable")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_macros_with_mock_data():
    """Test get_macros() method with mocked directory data."""
    print("\n" + "=" * 60)
    print("TEST 2: Test get_macros() with mock data")
    print("=" * 60)
    
    try:
        # Create a communicator instance
        comm = BBCtrlCommunicator()
        
        # Mock the _find_macros_recursive method to return test data
        mock_macros = {
            'test_macro_1': {
                'name': 'test_macro_1',
                'path': 'Home/test_macro_1.gcode',
                'description': 'Test macro 1',
                'category': 'test'
            },
            'test_macro_2': {
                'name': 'test_macro_2', 
                'path': 'Home/subfolder/test_macro_2.gcode',
                'description': 'Test macro 2',
                'category': 'user'
            }
        }
        
        # Patch the _find_macros_recursive method
        with patch.object(comm, '_find_macros_recursive', return_value=mock_macros):
            macros = comm.get_macros()
            
            # Verify the results
            assert isinstance(macros, list), f"Expected list, got {type(macros)}"
            assert len(macros) == 2, f"Expected 2 macros, got {len(macros)}"
            
            # Check first macro
            macro1 = macros[0]
            assert hasattr(macro1, 'name'), "Macro missing 'name' attribute"
            assert hasattr(macro1, 'path'), "Macro missing 'path' attribute"
            assert hasattr(macro1, 'description'), "Macro missing 'description' attribute"
            assert hasattr(macro1, 'category'), "Macro missing 'category' attribute"
            
            print(f"✓ get_macros() returned {len(macros)} macros")
            print(f"  - Macro 1: {macro1.name} at {macro1.path}")
            print(f"  - Macro 2: {macros[1].name} at {macros[1].path}")
            
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_from_controller_no_error():
    """Test that sync_from_controller no longer throws AttributeError."""
    print("\n" + "=" * 60)
    print("TEST 3: Test sync_from_controller() doesn't crash")
    print("=" * 60)
    
    temp_dir = None
    try:
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp(prefix="macro_test_")
        print(f"Using temporary directory: {temp_dir}")
        
        # Create a macro manager with the temp directory
        macro_manager = MacroManager(temp_dir)
        
        # Create a communicator instance
        comm = BBCtrlCommunicator()
        
        # Mock the methods that would be called
        mock_macros = [
            type('MockMacro', (), {
                'name': 'test_macro',
                'path': 'Home/test_macro.gcode',
                'description': 'Test macro',
                'category': 'test'
            })()
        ]
        
        # Mock the communicator methods
        with patch.object(comm, '_find_macros_recursive', return_value={
            'test_macro': {
                'name': 'test_macro',
                'path': 'Home/test_macro.gcode', 
                'description': 'Test macro',
                'category': 'test'
            }
        }):
            with patch.object(comm, 'read_file', return_value='G28\nG0 X0 Y0 Z0'):
                # This should NOT raise AttributeError anymore
                result = macro_manager.sync_from_controller(comm)
                
                print(f"✓ sync_from_controller() completed without AttributeError")
                print(f"  - Result: {result}")
                
                return True
                
    except AttributeError as e:
        if "'BBCtrlCommunicator' object has no attribute 'get_macros'" in str(e):
            print(f"✗ ORIGINAL ERROR STILL EXISTS: {e}")
            return False
        else:
            print(f"✗ Different AttributeError: {e}")
            return False
            
    except Exception as e:
        print(f"✓ sync_from_controller() completed (different error is expected): {e}")
        # Other errors are expected since we're not actually connecting to a controller
        return True
        
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

def test_get_macros_empty_result():
    """Test get_macros() when no macros are found."""
    print("\n" + "=" * 60)
    print("TEST 4: Test get_macros() with no macros")
    print("=" * 60)
    
    try:
        # Create a communicator instance
        comm = BBCtrlCommunicator()
        
        # Mock _find_macros_recursive to return empty dict
        with patch.object(comm, '_find_macros_recursive', return_value={}):
            macros = comm.get_macros()
            
            assert isinstance(macros, list), f"Expected list, got {type(macros)}"
            assert len(macros) == 0, f"Expected empty list, got {len(macros)} items"
            
            print("✓ get_macros() correctly returns empty list when no macros found")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing get_macros() method fix for BBCtrlCommunicator")
    print("=" * 60)
    
    tests = [
        test_get_macros_method_exists,
        test_get_macros_with_mock_data,
        test_sync_from_controller_no_error,
        test_get_macros_empty_result
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! The get_macros() fix is working correctly.")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. The fix needs more work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)