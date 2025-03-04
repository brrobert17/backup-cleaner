import os
import hashlib
import random
import string
import shutil
from pathlib import Path
import time
import sys

def create_random_content(size_kb):
    """Create random content of specified size in kilobytes."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size_kb * 1024))

def create_binary_file(file_path, size_mb, seed=None):
    """Create a binary file of specified size in megabytes with a progress indicator.
    If seed is provided, the random data will be deterministic based on the seed."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # If seed is provided, initialize the random generator with it
    if seed is not None:
        random.seed(seed)
    
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(file_path, 'wb') as f:
        for i in range(size_mb):
            # Generate 1MB of random data
            data = random.randbytes(chunk_size)
            f.write(data)
            
            # Update progress indicator
            percent = int((i + 1) / size_mb * 100)
            sys.stdout.write(f"\rCreating {file_path}: {percent}% complete")
            sys.stdout.flush()
    
    print()  # New line after progress indicator
    
    # Reset the random seed if we used one
    if seed is not None:
        random.seed(None)

def write_file(file_path, content):
    """Write content to a file, creating directories if needed."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def display_progress(current, total, prefix='', length=50):
    """Display a progress bar."""
    percent = int(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% ({current}/{total})')
    sys.stdout.flush()
    if current == total:
        print()

def main():
    # Base directories for testing
    base_dir = os.path.dirname(os.path.abspath(__file__))
    origin_dir = os.path.join(base_dir, "test_origin")
    target_dir = os.path.join(base_dir, "test_target")
    
    # Create directories if they don't exist
    os.makedirs(origin_dir, exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)
    
    # Clear existing test directories
    for dir_path in [origin_dir, target_dir]:
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    
    print(f"Creating test files in {origin_dir} and {target_dir}")
    
    # Count total scenarios for progress tracking
    total_scenarios = 12  # Updated count with new scenarios
    current_scenario = 0
    
    # === Scenario 1: Exact duplicates (same content) ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating exact duplicate files...")
    for i in range(3):
        content = create_random_content(1)  # 1KB of random content
        file_name = f"exact_duplicate_{i}.txt"
        
        # Create identical files in origin and target
        write_file(os.path.join(origin_dir, file_name), content)
        write_file(os.path.join(target_dir, file_name), content)
    
    # === Scenario 2: Same name but different content ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files with same name but different content...")
    for i in range(3):
        file_name = f"same_name_diff_content_{i}.txt"
        
        # Different content for origin and target
        origin_content = create_random_content(2)  # 2KB
        target_content = create_random_content(3)  # 3KB
        
        write_file(os.path.join(origin_dir, file_name), origin_content)
        write_file(os.path.join(target_dir, file_name), target_content)
    
    # === Scenario 3: Same size but different content ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files with same size but different content...")
    for i in range(3):
        file_name = f"same_size_diff_content_{i}.txt"
        size = 2  # 2KB
        
        # Different content but same size
        origin_content = create_random_content(size)
        target_content = create_random_content(size)
        
        write_file(os.path.join(origin_dir, file_name), origin_content)
        write_file(os.path.join(target_dir, file_name), target_content)
    
    # === Scenario 4: Files with " - Copy" variations ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files with Copy variations...")
    for i in range(2):
        content = create_random_content(1)
        
        # Original in origin, copy in target
        write_file(os.path.join(origin_dir, f"original_{i}.txt"), content)
        write_file(os.path.join(target_dir, f"original_{i} - Copy.txt"), content)
        
        # Copy in origin, original in target
        other_content = create_random_content(1)
        write_file(os.path.join(origin_dir, f"other_{i} - Copy.txt"), other_content)
        write_file(os.path.join(target_dir, f"other_{i}.txt"), other_content)
    
    # === Scenario 5: Files only in origin (to be moved) ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files only in origin...")
    for i in range(3):
        content = create_random_content(1)
        write_file(os.path.join(origin_dir, f"only_in_origin_{i}.txt"), content)
    
    # === Scenario 6: Nested folder structure ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating nested folder structure...")
    # Create folders and files in origin
    folders = ["folder1", "folder2", os.path.join("folder1", "subfolder")]
    for folder in folders:
        for i in range(2):
            content = create_random_content(1)
            file_name = f"nested_file_{i}.txt"
            file_path = os.path.join(origin_dir, folder, file_name)
            write_file(file_path, content)
            
            # Some files have matches in target
            if i % 2 == 0:
                target_path = os.path.join(target_dir, folder, file_name)
                write_file(target_path, content)
    
    # === Scenario 7: Files in different locations ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files in different locations...")
    for i in range(2):
        content = create_random_content(1)
        
        # File in one location in origin
        origin_path = os.path.join(origin_dir, f"different_location_{i}.txt")
        write_file(origin_path, content)
        
        # Same file in different location in target
        target_folder = os.path.join(target_dir, f"different_folder_{i}")
        target_path = os.path.join(target_folder, f"different_location_{i}.txt")
        write_file(target_path, content)
        
    # === Scenario 8: One file with multiple potential matches ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files with multiple matches...")
    # Create a file in origin with multiple potential matches in target
    multi_match_content = create_random_content(1)
    write_file(os.path.join(origin_dir, "multi_match.txt"), multi_match_content)
    
    # Create multiple copies in target with different names/locations
    write_file(os.path.join(target_dir, "multi_match.txt"), multi_match_content)  # Same name
    write_file(os.path.join(target_dir, "multi_match - Copy.txt"), multi_match_content)  # Copy variant
    write_file(os.path.join(target_dir, "different_folder", "multi_match.txt"), multi_match_content)  # Different location
    
    # Create a similar file but with different content (same size)
    other_multi_match = create_random_content(1)  # Same size, different content
    write_file(os.path.join(target_dir, "similar_multi_match.txt"), other_multi_match)
    
    # === Scenario 9: Empty folders after cleanup ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating empty folder structure for testing cleanup...")
    # Create a nested folder structure that will be empty after actions
    empty_folders = ["empty_folder", 
                     os.path.join("empty_folder", "subfolder1"), 
                     os.path.join("empty_folder", "subfolder2"),
                     os.path.join("empty_folder", "subfolder2", "subsubfolder")]
    
    for folder in empty_folders:
        folder_path = os.path.join(origin_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
    
    # Add one file to test removal after deletion
    cleanup_content = create_random_content(1)
    cleanup_file = os.path.join(origin_dir, "empty_folder", "subfolder2", "subsubfolder", "to_delete.txt")
    write_file(cleanup_file, cleanup_content)
    
    # Create identical file in target
    target_cleanup_file = os.path.join(target_dir, "empty_folder", "subfolder2", "subsubfolder", "to_delete.txt")
    write_file(target_cleanup_file, cleanup_content)
    
    # === NEW Scenario 10: Large files (>500MB) ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating large file test scenarios (this may take a while)...")
    
    # Create large files directory
    large_dir_origin = os.path.join(origin_dir, "large_files")
    large_dir_target = os.path.join(target_dir, "large_files")
    os.makedirs(large_dir_origin, exist_ok=True)
    os.makedirs(large_dir_target, exist_ok=True)
    
    # Create a small test large file for testing (10MB instead of 500MB to save time)
    # In a real test, you might want to use actual 500MB+ files
    test_size = 10  # Using 10MB for quick testing, change to 500+ for real test
    
    # Exact large file match - using same seed for identical content
    create_binary_file(os.path.join(large_dir_origin, "large_exact_match.bin"), test_size, seed=42)
    create_binary_file(os.path.join(large_dir_target, "large_exact_match.bin"), test_size, seed=42)
    
    # Same size but different content (for manual check testing)
    create_binary_file(os.path.join(large_dir_origin, "large_size_match.bin"), test_size, seed=123)
    create_binary_file(os.path.join(large_dir_target, "large_size_match.bin"), test_size, seed=456)
    
    # Different size
    create_binary_file(os.path.join(large_dir_origin, "large_diff_size.bin"), test_size, seed=789)
    create_binary_file(os.path.join(large_dir_target, "large_diff_size.bin"), test_size + 2, seed=789)
    
    # === NEW Scenario 11: Same parent folder in different locations ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files with same parent folder in different locations...")
    
    # Create origin parent folder structure
    same_parent_origin = os.path.join(origin_dir, "data", "important_folder")
    os.makedirs(same_parent_origin, exist_ok=True)
    
    # Create target with same parent folder name but in different path
    same_parent_target = os.path.join(target_dir, "backup", "important_folder")
    os.makedirs(same_parent_target, exist_ok=True)
    
    # Create matching files
    for i in range(3):
        content = create_random_content(1)
        write_file(os.path.join(same_parent_origin, f"parent_match_{i}.txt"), content)
        write_file(os.path.join(same_parent_target, f"parent_match_{i}.txt"), content)
    
    # === NEW Scenario 12: Files with unusual characters in names ===
    current_scenario += 1
    display_progress(current_scenario, total_scenarios, prefix='Test scenarios')
    print("\nCreating files with unusual characters in names...")
    
    # Create a folder for special character files
    special_chars_dir_origin = os.path.join(origin_dir, "special_chars")
    special_chars_dir_target = os.path.join(target_dir, "special_chars")
    os.makedirs(special_chars_dir_origin, exist_ok=True)
    os.makedirs(special_chars_dir_target, exist_ok=True)
    
    # Files with spaces, brackets, and special characters
    special_filenames = [
        "file with spaces.txt",
        "file_with_[brackets].txt",
        "file-with-dashes.txt",
        "file_with_$pecial_chars.txt",
        "file_with_multi-part_name-v1.0.txt",
    ]
    
    for filename in special_filenames:
        content = create_random_content(1)
        write_file(os.path.join(special_chars_dir_origin, filename), content)
        # Create some matches in target
        if random.choice([True, False]):
            write_file(os.path.join(special_chars_dir_target, filename), content)
    
    print("\nTest files created successfully!")
    print(f"Origin folder: {origin_dir}")
    print(f"Target folder: {target_dir}")
    print("\nTotal test scenarios created:", total_scenarios)
    print("Note: Large files were created at a smaller size (10MB) for testing purposes.")
    print("      For real 500MB+ testing, modify the 'test_size' variable in the script.")

if __name__ == "__main__":
    main()
