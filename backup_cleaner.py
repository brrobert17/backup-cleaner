import os
import sys
import xxhash
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
import shutil
from pathlib import Path
import collections
import threading
import queue
import time
import itertools
import datetime
from multiprocessing import Pool, cpu_count

class BackupCleaner(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Backup Cleaner")
        self.geometry("1200x800")
        
        # Set theme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Variables
        self.origin_folder_var = tk.StringVar()
        self.target_folder_var = tk.StringVar()
        self.search_different_locations_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        
        # CPU usage control variable
        self.cpu_usage_var = tk.IntVar(value=75)  # Default to 75% of available cores
        
        self.create_widgets()
        
        # Store file data
        self.file_data = []
        
        # For background processing
        self.processing_queue = queue.Queue()
        self.stop_background_thread = False

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Folder selection frame
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=10)
        
        # Origin folder selection
        ttk.Label(folder_frame, text="Origin Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        origin_entry = ttk.Entry(folder_frame, textvariable=self.origin_folder_var, width=50)
        origin_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Button(folder_frame, text="Browse...", command=self.select_origin_folder).grid(row=0, column=2, padx=5, pady=5)
        
        # Target folder selection
        ttk.Label(folder_frame, text="Target Folder:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        target_entry = ttk.Entry(folder_frame, textvariable=self.target_folder_var, width=50)
        target_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Button(folder_frame, text="Browse...", command=self.select_target_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # Search option
        search_option = ttk.Checkbutton(
            folder_frame, 
            text="Search for matches in different locations", 
            variable=self.search_different_locations_var
        )
        search_option.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # CPU usage slider
        cpu_label = ttk.Label(folder_frame, text="CPU Usage (%): ")
        cpu_label.grid(row=3, column=0, padx=(20, 5), pady=5, sticky=tk.W)
        
        cpu_slider = ttk.Scale(
            folder_frame,
            from_=25,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.cpu_usage_var,
            length=150
        )
        cpu_slider.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # CPU percentage label
        self.cpu_percent_label = ttk.Label(folder_frame, text="75%")
        self.cpu_percent_label.grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Update CPU percentage label when slider value changes
        cpu_slider.bind("<Motion>", self.update_cpu_label)
        
        # Progress bar
        progress_frame = ttk.Frame(folder_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        # Progress label
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(fill=tk.X, expand=True, pady=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(folder_frame)
        button_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Compare Folders", command=self.compare_folders).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Execute Actions", command=self.execute_actions).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to Log", command=self.export_to_log).pack(side=tk.LEFT, padx=5)
        
        # Results TreeView with scrollbar
        self.result_tree_frame = ttk.Frame(main_frame)
        self.result_tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create scrollbars
        tree_scroll_y = ttk.Scrollbar(self.result_tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x = ttk.Scrollbar(self.result_tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create Treeview
        self.result_tree = ttk.Treeview(
            self.result_tree_frame,
            columns=("selected", "origin_path", "target_path", "size", "match_type", "action"),
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        # Configure scrollbars
        tree_scroll_y.config(command=self.result_tree.yview)
        tree_scroll_x.config(command=self.result_tree.xview)
        
        # Configure column headings
        self.result_tree.heading("selected", text="Select")
        self.result_tree.heading("origin_path", text="Origin Path")
        self.result_tree.heading("target_path", text="Target Path")
        self.result_tree.heading("size", text="Size")
        self.result_tree.heading("match_type", text="Match Type")
        self.result_tree.heading("action", text="Proposed Action")
        
        # Configure column widths
        self.result_tree.column("selected", width=50, stretch=False)
        self.result_tree.column("origin_path", width=350, stretch=True)
        self.result_tree.column("target_path", width=350, stretch=True)
        self.result_tree.column("size", width=100, stretch=False)
        self.result_tree.column("match_type", width=100, stretch=False)
        self.result_tree.column("action", width=150, stretch=False)
        
        self.result_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind click event for checkboxes
        self.result_tree.bind("<ButtonRelease-1>", self.on_tree_click)
        
        # Status bar
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure tags for color highlighting
        self.result_tree.tag_configure("green", foreground="green")
        self.result_tree.tag_configure("blue", foreground="blue")

    def select_origin_folder(self):
        folder = filedialog.askdirectory(title="Select Origin Folder")
        if folder:
            self.origin_folder_var.set(folder)

    def select_target_folder(self):
        folder = filedialog.askdirectory(title="Select Target Folder")
        if folder:
            self.target_folder_var.set(folder)

    def count_files_in_directory(self, directory):
        """Count files in a directory without loading all files in memory."""
        file_count = 0
        batch_size = 1000  # Process in batches to prevent memory issues
        
        try:
            for root, _, files in os.walk(directory):
                file_count += len(files)
                
                # Update UI periodically during counting
                if file_count % batch_size == 0:
                    self.progress_label.config(text=f"Counting files: {file_count}...")
                    self.update_idletasks()
                    
            return file_count
        except Exception as e:
            print(f"Error counting files: {e}")
            return 0

    def compare_folders(self):
        origin_folder = self.origin_folder_var.get()
        target_folder = self.target_folder_var.get()
        
        # Reset UI and data
        self.reset_ui()
        
        # Input validation
        if not origin_folder or not os.path.isdir(origin_folder):
            messagebox.showerror("Error", "Please select a valid origin folder")
            return
        
        if not target_folder or not os.path.isdir(target_folder):
            messagebox.showerror("Error", "Please select a valid target folder")
            return
        
        # Initialize progress info
        self.status_var.set("Counting files...")
        self.progress_var.set(0)
        self.progress_label.config(text="Preparing...")
        self.update_idletasks()
        
        try:
            # Count files for progress tracking
            self.status_var.set("Counting files...")
            origin_files = self.count_files_in_directory(origin_folder)
            
            if origin_files == 0:
                messagebox.showinfo("Info", "No files found in the origin folder.")
                self.status_var.set("Ready")
                return
            
            self.status_var.set(f"Processing {origin_files} files...")
            
            # Get list of files in both directories
            origin_file_list = []
            for root, _, files in os.walk(origin_folder):
                for file in files:
                    origin_file_list.append(os.path.join(root, file))
            
            # Process files in batches using multiprocessing
            batch_size = max(1, len(origin_file_list) // (self.get_worker_count() * 2))  # Adjust batch size based on CPU count
            batches = [origin_file_list[i:i+batch_size] for i in range(0, len(origin_file_list), batch_size)]
            
            # Create a pool of workers
            processed_files = 0
            
            # Parameters for multiprocessing
            process_params = {
                'origin_folder': origin_folder,
                'target_folder': target_folder,
                'search_different_locations': self.search_different_locations_var.get()
            }
            
            with Pool(processes=self.get_worker_count()) as pool:
                # Process batches in parallel
                results_iter = pool.imap(
                    self._process_file_batch, 
                    [(batch, process_params) for batch in batches]
                )
                
                # Process results as they come in
                all_results = []
                for batch_results in results_iter:
                    all_results.extend(batch_results)
                    processed_files += len(batch_results)
                    progress = (processed_files / origin_files) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"Processing files: {int(progress)}%")
                    self.update_idletasks()
            
            # Add all results to the UI
            for result in all_results:
                self.add_file_to_results(
                    result['origin_path'],
                    result['target_path'],
                    result['size'],
                    result['match_type'],
                    result['action'],
                    result['selected'],
                    result['color']
                )
            
            # Update status
            self.status_var.set(f"Processed {origin_files} files. Check results and select actions.")
            self.progress_label.config(text="Comparison complete")
            
        except Exception as e:
            self.status_var.set("Error during comparison")
            messagebox.showerror("Error", f"An error occurred during comparison: {str(e)}")

    @staticmethod
    def _process_file_batch(args):
        """Static method for parallel processing of file batches"""
        batch, params = args
        origin_folder = params['origin_folder']
        target_folder = params['target_folder']
        search_different_locations = params['search_different_locations']
        
        results = []
        
        for origin_file_path in batch:
            # Extract relative path
            rel_path = os.path.relpath(origin_file_path, origin_folder)
            file_size = os.path.getsize(origin_file_path)
            filename = os.path.basename(origin_file_path)
            
            # Find potential matching files
            potential_matches = []
            
            # Original path in target folder
            target_path = os.path.join(target_folder, rel_path)
            potential_matches.append(target_path)
            
            # Check for " - Copy" variations
            if " - Copy" in filename:
                # Try without " - Copy"
                base_filename = filename.replace(" - Copy", "")
                base_rel_path = os.path.join(os.path.dirname(rel_path), base_filename)
                potential_matches.append(os.path.join(target_folder, base_rel_path))
            else:
                # Try with " - Copy"
                copy_filename = os.path.splitext(filename)[0] + " - Copy" + os.path.splitext(filename)[1]
                copy_rel_path = os.path.join(os.path.dirname(rel_path), copy_filename)
                potential_matches.append(os.path.join(target_folder, copy_rel_path))
            
            # If searching in different locations is enabled
            if search_different_locations:
                # Get the parent folder name of the original file
                parent_folder_name = os.path.basename(os.path.dirname(rel_path))
                
                # Search only in folders with the same parent folder name
                for search_root, search_dirs, search_files in os.walk(target_folder):
                    # Check if this directory has the same name as the parent folder
                    if os.path.basename(search_root) == parent_folder_name:
                        for file in search_files:
                            if file == filename or (file == filename.replace(" - Copy", "")) or (file == os.path.splitext(filename)[0] + " - Copy" + os.path.splitext(filename)[1]):
                                potential_matches.append(os.path.join(search_root, file))
            
            # Check for matches
            matches = []
            
            for potential_match in potential_matches:
                if os.path.exists(potential_match):
                    # Get basic file info
                    target_size = os.path.getsize(potential_match)
                    
                    # Check if exact duplicate (same content)
                    if BackupCleaner._calculate_checksum(origin_file_path) == BackupCleaner._calculate_checksum(potential_match):
                        matches.append({
                            "target_path": potential_match,
                            "match_type": "Exact match",
                            "proposed_action": "Delete",
                            "selected": True,
                            "color": "green"
                        })
                    # Check if same name, different content
                    elif os.path.basename(origin_file_path) == os.path.basename(potential_match):
                        matches.append({
                            "target_path": potential_match,
                            "match_type": "Name match",
                            "proposed_action": "Copy as _v2",
                            "selected": True,
                            "color": "orange"
                        })
                    # Check if same size, different content
                    elif file_size == target_size:
                        matches.append({
                            "target_path": potential_match,
                            "match_type": "Size match",
                            "proposed_action": "Copy as _v2",
                            "selected": True,
                            "color": "blue"
                        })
            
            # Create result entry
            result = {}
            
            # If we found matches
            if matches:
                # Handle multiple matches
                if len(matches) > 1:
                    # Sort matches by priority: Exact match > Size match > Name match
                    sorted_matches = sorted(
                        matches,
                        key=lambda x: (
                            0 if x["match_type"] == "Exact match" else 
                            1 if x["match_type"] == "Size match" else 
                            2
                        )
                    )
                    
                    # Add the best match to results
                    best_match = sorted_matches[0]
                    result = {
                        'origin_path': origin_file_path,
                        'target_path': best_match["target_path"],
                        'size': file_size,
                        'match_type': f"{best_match['match_type']} (multiple matches: {len(matches)})",
                        'action': best_match["proposed_action"],
                        'selected': best_match["selected"],
                        'color': best_match["color"]
                    }
                    
                    # Add other matches with different proposed action
                    for i, match in enumerate(sorted_matches[1:]):
                        results.append({
                            'origin_path': origin_file_path,
                            'target_path': match["target_path"],
                            'size': file_size,
                            'match_type': f"Alternative match #{i+1}",
                            'action': "Skip",  # We skip alternative matches by default
                            'selected': False,
                            'color': None
                        })
                else:
                    # Single match
                    match = matches[0]
                    result = {
                        'origin_path': origin_file_path,
                        'target_path': match["target_path"],
                        'size': file_size,
                        'match_type': match["match_type"],
                        'action': match["proposed_action"],
                        'selected': match["selected"],
                        'color': match["color"]
                    }
            else:
                # No matches found
                result = {
                    'origin_path': origin_file_path,
                    'target_path': None,
                    'size': file_size,
                    'match_type': "No match",
                    'action': "Move",
                    'selected': False,
                    'color': None
                }
            
            results.append(result)
        
        return results
    
    @staticmethod
    def _calculate_checksum(file_path):
        """Calculate xxHash (xxh64) checksum for a file with optimizations for large files."""
        file_size = os.path.getsize(file_path)
        hasher = xxhash.xxh64()
        
        with open(file_path, "rb") as f:
            if file_size > 100 * 1024 * 1024:  # For files larger than 100MB
                # Hash the first 1MB
                hasher.update(f.read(1024 * 1024))
                
                # Move to the middle and hash 1MB
                f.seek(file_size // 2, 0)
                hasher.update(f.read(1024 * 1024))
                
                # Move to the end and hash the last 1MB
                f.seek(-1024 * 1024, 2)
                hasher.update(f.read(1024 * 1024))
            else:
                # For smaller files, read in 1MB chunks
                for byte_block in iter(lambda: f.read(1024 * 1024), b""):
                    hasher.update(byte_block)
                    
        return hasher.hexdigest()

    def calculate_checksum(self, file_path):
        """Instance method that calls the static method for compatibility"""
        return self._calculate_checksum(file_path)

    def add_file_to_results(self, origin_path, target_path, size, match_type, action, selected=False, color=None):
        """Add a file comparison result to the treeview."""
        # Store file data
        file_id = len(self.file_data)
        self.file_data.append({
            "id": file_id,
            "origin_path": origin_path,
            "target_path": target_path,
            "size": size,
            "match_type": match_type,
            "action": action,
            "selected": selected
        })
        
        # Format the size
        size_formatted = self.format_size(size)
        
        # Add to treeview
        item = self.result_tree.insert(
            "", tk.END,
            values=(
                "✓" if selected else "□", 
                origin_path, 
                target_path if target_path else "", 
                size_formatted, 
                match_type, 
                action
            )
        )
        
        # Set tag for color
        if color:
            self.result_tree.item(item, tags=(color,))

    def format_size(self, size_bytes):
        """Format file size in a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def on_tree_click(self, event):
        """Handle clicks on the treeview."""
        region = self.result_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.result_tree.identify_column(event.x)
            if column == "#1":  # Selected column
                item = self.result_tree.identify_row(event.y)
                if item:
                    item_index = self.result_tree.index(item)
                    if item_index < len(self.file_data):
                        # Toggle selection
                        self.file_data[item_index]["selected"] = not self.file_data[item_index]["selected"]
                        self.update_tree_item(item_index)

    def update_tree_item(self, index):
        """Update a single item in the treeview."""
        if index < len(self.file_data):
            file_data = self.file_data[index]
            item = self.result_tree.get_children()[index]
            
            self.result_tree.item(
                item, 
                values=(
                    "✓" if file_data["selected"] else "□", 
                    file_data["origin_path"], 
                    file_data["target_path"] if file_data["target_path"] else "", 
                    self.format_size(file_data["size"]), 
                    file_data["match_type"], 
                    file_data["action"]
                )
            )

    def select_all(self):
        """Select all items in the treeview."""
        for i in range(len(self.file_data)):
            self.file_data[i]["selected"] = True
            self.update_tree_item(i)

    def deselect_all(self):
        """Deselect all items in the treeview."""
        for i in range(len(self.file_data)):
            self.file_data[i]["selected"] = False
            self.update_tree_item(i)

    def execute_actions(self):
        """Execute the proposed actions for selected files."""
        if not self.file_data:
            messagebox.showinfo("Info", "No files to process.")
            return
        
        # Count actions to perform
        move_count = 0
        delete_count = 0
        copy_count = 0
        
        selected_files = []
        for file_data in self.file_data:
            if file_data["selected"]:
                selected_files.append(file_data)
                if file_data["action"] == "Move":
                    move_count += 1
                elif file_data["action"] == "Delete":
                    delete_count += 1
                elif file_data["action"] == "Copy as _v2" or file_data["action"] == "Manual check needed":
                    copy_count += 1
        
        if move_count == 0 and delete_count == 0 and copy_count == 0:
            messagebox.showinfo("Info", "No actions selected.")
            return
        
        # Confirm action
        message = f"About to perform the following actions:\n"
        if move_count > 0:
            message += f"- Move {move_count} files\n"
        if delete_count > 0:
            message += f"- Delete {delete_count} files\n"
        if copy_count > 0:
            message += f"- Copy {copy_count} files with _v2 suffix\n"
        message += "\nDo you want to continue?"
        
        # Check for files that need manual verification
        manual_check_needed = False
        for file_data in self.file_data:
            if file_data["selected"] and file_data["action"] == "Manual check needed":
                manual_check_needed = True
                break
        
        if manual_check_needed:
            message += "\n\nWARNING: Some selected files are large (>500MB) and require manual verification."
        
        if not messagebox.askyesno("Confirm Actions", message):
            return
        
        # Execute actions
        error_count = 0
        success_count = 0
        origin_folder = self.origin_folder_var.get()
        target_folder = self.target_folder_var.get()
        
        total_files = len(selected_files)
        processed_files = 0
        
        # Reset progress bar
        self.progress_var.set(0)
        self.progress_label.config(text="Executing actions: 0%")
        self.status_var.set("Executing actions...")
        self.update_idletasks()
        
        # Keep track of processed origin files to handle multiple matches
        processed_origin_files = set()
        
        for file_data in selected_files:
            if file_data["origin_path"] not in processed_origin_files:
                try:
                    if file_data["action"] == "Move":
                        # Create target directory structure if needed
                        rel_path = os.path.relpath(file_data["origin_path"], origin_folder)
                        target_path = os.path.join(target_folder, rel_path)
                        target_dir = os.path.dirname(target_path)
                        
                        # Create target directory if it doesn't exist
                        os.makedirs(target_dir, exist_ok=True)
                        
                        # Move the file
                        shutil.move(file_data["origin_path"], target_path)
                        processed_origin_files.add(file_data["origin_path"])
                        success_count += 1
                    
                    elif file_data["action"] == "Delete":
                        # Delete the file
                        os.remove(file_data["origin_path"])
                        processed_origin_files.add(file_data["origin_path"])
                        success_count += 1
                    
                    elif file_data["action"] == "Copy as _v2" or file_data["action"] == "Manual check needed":
                        # Create target directory structure if needed
                        rel_path = os.path.relpath(file_data["origin_path"], origin_folder)
                        file_name, file_ext = os.path.splitext(os.path.basename(rel_path))
                        new_file_name = f"{file_name}_v2{file_ext}"
                        new_rel_path = os.path.join(os.path.dirname(rel_path), new_file_name)
                        target_path = os.path.join(target_folder, new_rel_path)
                        target_dir = os.path.dirname(target_path)
                        
                        # Create target directory if it doesn't exist
                        os.makedirs(target_dir, exist_ok=True)
                        
                        # Copy the file with _v2 suffix
                        shutil.copy2(file_data["origin_path"], target_path)
                        
                        # Delete the original file after copying
                        os.remove(file_data["origin_path"])
                        
                        processed_origin_files.add(file_data["origin_path"])
                        success_count += 1
                
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {file_data['origin_path']}: {e}")
                
                # Update progress
                processed_files += 1
                progress_percentage = (processed_files / total_files) * 100
                self.progress_var.set(progress_percentage)
                self.progress_label.config(text=f"Executing actions: {int(progress_percentage)}%")
                self.update_idletasks()
        
        # Clean up empty directories in origin folder
        self.cleanup_empty_directories(origin_folder)
        
        # Update status and show message
        self.status_var.set(f"Actions completed. Success: {success_count}, Errors: {error_count}")
        self.progress_label.config(text="Actions completed")
        messagebox.showinfo("Actions Completed", f"Actions completed.\nSuccess: {success_count}\nErrors: {error_count}")
        
        # Refresh the file list
        self.compare_folders()

    def cleanup_empty_directories(self, directory):
        """Recursively remove empty directories."""
        if not os.path.exists(directory):
            return
        
        # Track removed directories for status updates
        dirs_removed = 0
        
        # Keep removing empty directories until no more are found
        while True:
            empty_dirs_found = False
            
            # Walk bottom-up to find empty directories
            for root, dirs, files in os.walk(directory, topdown=False):
                # Skip the base directory itself
                if root == directory:
                    continue
                    
                if not files and not dirs:  # If directory is empty
                    try:
                        # Double-check it's still empty before removing
                        if os.path.exists(root) and not os.listdir(root):
                            os.rmdir(root)
                            dirs_removed += 1
                            empty_dirs_found = True
                            
                            # Update UI periodically
                            if dirs_removed % 10 == 0:
                                self.progress_label.config(text=f"Removed {dirs_removed} empty directories...")
                                self.update_idletasks()
                    except Exception as e:
                        print(f"Error removing directory {root}: {e}")
            
            # If no empty directories were found in this pass, we're done
            if not empty_dirs_found:
                break
        
        self.progress_label.config(text=f"Removed {dirs_removed} empty directories")
        self.update_idletasks()

    def export_to_log(self):
        """Export all comparison details to a log.txt file for analysis."""
        if not self.file_data:
            messagebox.showinfo("Export to Log", "No comparison data to export. Please run 'Compare Folders' first.")
            return
        
        # Get the log file path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"backup_cleaner_log_{timestamp}.txt")
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write("Backup Cleaner - Comparison Log\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Origin Folder: {self.origin_folder_var.get()}\n")
                f.write(f"Target Folder: {self.target_folder_var.get()}\n")
                f.write(f"Search in different locations: {self.search_different_locations_var.get()}\n")
                f.write(f"Total files analyzed: {len(self.file_data)}\n")
                f.write("=" * 80 + "\n\n")
                
                # Write test summary statistics
                match_types = collections.Counter(item['match_type'] for item in self.file_data)
                proposed_actions = collections.Counter(item['action'] for item in self.file_data)
                
                f.write("SUMMARY STATISTICS\n")
                f.write("-" * 80 + "\n")
                
                f.write("Match Types:\n")
                for match_type, count in match_types.items():
                    f.write(f"  {match_type}: {count}\n")
                
                f.write("\nProposed Actions:\n")
                for action, count in proposed_actions.items():
                    f.write(f"  {action}: {count}\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
                
                # Write detailed file information
                f.write("DETAILED FILE INFORMATION\n")
                f.write("-" * 80 + "\n")
                
                for i, item in enumerate(self.file_data, 1):
                    f.write(f"File #{i}:\n")
                    f.write(f"  Origin Path: {item['origin_path']}\n")
                    f.write(f"  Target Path: {item['target_path'] if item['target_path'] else 'None'}\n")
                    f.write(f"  Size: {self.format_size(item['size'])}\n")
                    f.write(f"  Match Type: {item['match_type']}\n")
                    f.write(f"  Proposed Action: {item['action']}\n")
                    f.write(f"  Selected: {item['selected']}\n")
                    f.write("\n")
                
                # Write test validation for each scenario
                f.write("TEST SCENARIO VALIDATION\n")
                f.write("-" * 80 + "\n")
                
                # Exact duplicates
                exact_matches = [item for item in self.file_data if item['match_type'] == 'Exact match']
                f.write(f"Scenario 1 - Exact duplicates: {len(exact_matches)} files\n")
                
                # Same name, different content
                name_matches = [item for item in self.file_data if item['match_type'] == 'Name match']
                f.write(f"Scenario 2 - Same name, different content: {len(name_matches)} files\n")
                
                # Same size, different content
                size_matches = [item for item in self.file_data if item['match_type'] == 'Size match']
                f.write(f"Scenario 3 - Same size, different content: {len(size_matches)} files\n")
                
                # Copy variations
                copy_variants = [item for item in self.file_data if " - Copy" in (item['origin_path'] or "") or " - Copy" in (item['target_path'] or "")]
                f.write(f"Scenario 4 - Copy variations: {len(copy_variants)} files\n")
                
                # Files only in origin
                files_only_in_origin = [item for item in self.file_data if item['match_type'] == 'No match']
                f.write(f"Scenario 5 - Files only in origin: {len(files_only_in_origin)} files\n")
                
                # Nested folder structure
                nested_folder_files = [item for item in self.file_data if "/folder" in item['origin_path'].replace("\\", "/")]
                f.write(f"Scenario 6 - Nested folder structure: {len(nested_folder_files)} files\n")
                
                # Files in different locations
                diff_location_files = [item for item in self.file_data if item['target_path'] and os.path.dirname(item['origin_path']) != os.path.dirname(item['target_path'])]
                f.write(f"Scenario 7 - Files in different locations: {len(diff_location_files)} files\n")
                
                # Files with multiple matches
                multi_match_files = [item for item in self.file_data if 'multiple matches' in (item['match_type'] or "")]
                f.write(f"Scenario 8 - Files with multiple matches: {len(multi_match_files)} files\n")
                
                # Large files
                large_files = [item for item in self.file_data if "large file" in (item['match_type'] or "").lower()]
                f.write(f"Scenario 10 - Large files: {len(large_files)} files\n")
                
                # Files with same parent folder in different locations
                same_parent_diff_loc = [item for item in self.file_data if 
                                      item['target_path'] and 
                                      os.path.basename(os.path.dirname(item['origin_path'])) == os.path.basename(os.path.dirname(item['target_path'])) and
                                      os.path.dirname(item['origin_path']) != os.path.dirname(item['target_path'])]
                f.write(f"Scenario 11 - Same parent folder in different locations: {len(same_parent_diff_loc)} files\n")
                
                # Files with special characters
                special_char_files = [item for item in self.file_data if "special_chars" in item['origin_path']]
                f.write(f"Scenario 12 - Files with special characters: {len(special_char_files)} files\n")
                
            # Show success message
            messagebox.showinfo("Export to Log", f"Comparison details successfully exported to:\n{log_file}")
            
            # Try to open the log file
            try:
                os.startfile(log_file)
            except Exception:
                # If opening fails, just inform the user about the file location
                pass
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export comparison details: {str(e)}")

    def reset_ui(self):
        self.file_data = []
        self.result_tree.delete(*self.result_tree.get_children())

    def update_cpu_label(self, event=None):
        """Update the CPU percentage label when the slider value changes"""
        self.cpu_percent_label.config(text=f"{self.cpu_usage_var.get()}%")

    def get_worker_count(self):
        """Calculate the number of worker processes based on CPU usage setting"""
        available_cpus = cpu_count()
        user_percentage = self.cpu_usage_var.get() / 100
        
        # At least 1 worker, at most the available CPU count
        worker_count = max(1, min(available_cpus, int(available_cpus * user_percentage)))
        
        # Always leave at least 1 core free if there are 4 or more cores
        if available_cpus >= 4 and worker_count >= available_cpus:
            worker_count = available_cpus - 1
            
        return worker_count

if __name__ == "__main__":
    app = BackupCleaner()
    app.mainloop()
