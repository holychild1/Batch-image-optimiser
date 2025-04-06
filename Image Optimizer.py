import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import io
import threading
from datetime import datetime


class BatchImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Image Resizer")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")

        self.selected_files = []
        self.processed_images = []
        self.target_size = 250 * 1024  # 250 KB in bytes
        self.target_dimensions = (1200, 1200)
        self.output_directory = ""

        # Create frames
        self.top_frame = tk.Frame(root, bg="#f0f0f0")
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.preview_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.preview_frame.pack(fill=tk.X, padx=10, pady=10)

        self.list_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.button_frame = tk.Frame(root, bg="#f0f0f0")
        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        # Add widgets to top frame
        self.select_button = tk.Button(self.top_frame, text="Select Images", command=self.select_images,
                                       font=("Arial", 12), bg="#4CAF50", fg="white", padx=10, pady=5)
        self.select_button.pack(side=tk.LEFT, padx=5)

        self.output_button = tk.Button(self.top_frame, text="Select Output Folder",
                                       command=self.select_output_directory,
                                       font=("Arial", 12), bg="#9C27B0", fg="white", padx=10, pady=5)
        self.output_button.pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(self.top_frame, text="No images selected",
                                   font=("Arial", 12), bg="#f0f0f0")
        self.info_label.pack(side=tk.LEFT, padx=20)

        # Preview frame
        self.preview_label = tk.Label(self.preview_frame, text="Preview", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.preview_label.pack(pady=5)

        self.preview_image_label = tk.Label(self.preview_frame, bg="#e0e0e0", width=30, height=15)
        self.preview_image_label.pack(pady=5)

        # List frame with scrollbar and treeview
        self.list_label = tk.Label(self.list_frame, text="Image List", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.list_label.pack(pady=5)

        # Create button frame for file operations
        self.file_ops_frame = tk.Frame(self.list_frame, bg="#f0f0f0")
        self.file_ops_frame.pack(fill=tk.X, pady=5)

        # Add Remove Selected button
        self.remove_button = tk.Button(self.file_ops_frame, text="Remove Selected", command=self.remove_selected_files,
                                       font=("Arial", 10), bg="#F44336", fg="white", padx=5, pady=2)
        self.remove_button.pack(side=tk.LEFT, padx=5)

        # Create treeview with scrollbar
        self.tree_frame = tk.Frame(self.list_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(self.tree_frame, columns=("path", "dimensions", "size", "status"),
                                 show="headings", yscrollcommand=self.tree_scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree_scroll.config(command=self.tree.yview)

        # Configure columns
        self.tree.heading("path", text="File Name")
        self.tree.heading("dimensions", text="Dimensions")
        self.tree.heading("size", text="Original Size")
        self.tree.heading("status", text="Status")

        self.tree.column("path", width=300)
        self.tree.column("dimensions", width=150)
        self.tree.column("size", width=100)
        self.tree.column("status", width=150)

        # Add binding to show preview when selecting an item
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Bottom buttons
        self.process_button = tk.Button(self.button_frame, text="Process All Images", command=self.process_all_images,
                                        font=("Arial", 12), bg="#2196F3", fg="white", padx=10, pady=5,
                                        state=tk.DISABLED)
        self.process_button.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.button_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(side=tk.LEFT, padx=20)

        # Status label
        self.status_label = tk.Label(self.button_frame, text="Ready", font=("Arial", 10), bg="#f0f0f0")
        self.status_label.pack(side=tk.LEFT, padx=5)

    def select_images(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.webp")]
        )

        if file_paths:
            self.selected_files.extend(list(file_paths))
            self.processed_images = []

            # Clear the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add files to treeview
            self.update_file_list()

            # Enable process button if output directory is selected
            if self.output_directory:
                self.process_button.config(state=tk.NORMAL)

            # Show preview of first image
            if self.selected_files:
                self.show_preview(self.selected_files[0])

    def update_file_list(self):
        # Clear the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add files to treeview
        for file_path in self.selected_files:
            try:
                image = Image.open(file_path)
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / 1024  # KB
                dimensions = f"{image.width}x{image.height}"

                self.tree.insert("", "end", values=(file_name, dimensions, f"{file_size:.1f} KB", "Pending"))
            except Exception as e:
                # If there's an error opening the image, still show it in the list but mark as error
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / 1024  # KB
                self.tree.insert("", "end", values=(file_name, "Unknown", f"{file_size:.1f} KB", "Error loading"))

        # Update info label
        self.info_label.config(text=f"{len(self.selected_files)} images selected")

        # Update process button state
        if self.selected_files and self.output_directory:
            self.process_button.config(state=tk.NORMAL)
        else:
            self.process_button.config(state=tk.DISABLED)

    def remove_selected_files(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Information", "No files selected to remove")
            return

        # Get the filenames of selected items
        files_to_remove = []
        for item in selected_items:
            file_name = self.tree.item(item, "values")[0]
            files_to_remove.append(file_name)

        # Remove the files from selected_files list
        self.selected_files = [f for f in self.selected_files if os.path.basename(f) not in files_to_remove]

        # Update the file list
        self.update_file_list()

        # Update the preview if needed
        if self.selected_files:
            self.show_preview(self.selected_files[0])
        else:
            # Clear preview if no files left
            self.preview_image_label.config(image="")
            self.preview_image_label.photo = None

        # Update status
        self.update_status(f"Removed {len(files_to_remove)} file(s)")

    def select_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory = directory

            # Enable process button if files are selected
            if self.selected_files:
                self.process_button.config(state=tk.NORMAL)

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            file_name = self.tree.item(item, "values")[0]

            # Find the full path
            for file_path in self.selected_files:
                if os.path.basename(file_path) == file_name:
                    self.show_preview(file_path)
                    break

    def show_preview(self, file_path):
        try:
            # Open image and create thumbnail for preview
            image = Image.open(file_path)
            preview_image = image.copy()
            preview_image.thumbnail((300, 300))

            # Convert to RGB if needed for PhotoImage
            if preview_image.mode in ('RGBA', 'LA', 'P'):
                preview_image = preview_image.convert("RGB")

            # Convert to PhotoImage
            photo_image = ImageTk.PhotoImage(preview_image)

            # Keep a reference to prevent garbage collection
            self.preview_image_label.photo = photo_image

            # Display the image
            self.preview_image_label.config(image=photo_image)

        except Exception as e:
            self.preview_image_label.config(image="")
            self.update_status(f"Error previewing image: {str(e)}")

    def process_all_images(self):
        # Disable buttons during processing
        self.process_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        self.output_button.config(state=tk.DISABLED)
        self.remove_button.config(state=tk.DISABLED)

        # Reset progress bar
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.selected_files)

        # Start processing in a separate thread
        threading.Thread(target=self.process_images_thread, daemon=True).start()

    def process_images_thread(self):
        try:
            # Create output directory with timestamp if it doesn't exist
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(self.output_directory, f"resized_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)

            # Process each image
            for i, file_path in enumerate(self.selected_files):
                try:
                    file_name = os.path.basename(file_path)
                    self.update_status(f"Processing {file_name}...")

                    # Update the tree view status
                    for item in self.tree.get_children():
                        if self.tree.item(item, "values")[0] == file_name:
                            self.tree.item(item, values=(file_name, self.tree.item(item, "values")[1],
                                                         self.tree.item(item, "values")[2], "Processing..."))
                            break

                    # Open the image
                    original_image = Image.open(file_path)

                    # Convert to RGB if needed (some formats like PNG might have alpha)
                    if original_image.mode in ('RGBA', 'LA', 'P'):
                        # Create white background image
                        background = Image.new('RGB', original_image.size, (255, 255, 255))
                        if original_image.mode in ('RGBA', 'LA'):
                            # Paste using alpha channel as mask
                            background.paste(original_image, mask=original_image.split()[3])
                            original_image = background
                        else:
                            # Convert palette mode to RGB
                            original_image = original_image.convert('RGB')

                    # Process the image
                    resized_image = self.resize_image(original_image)
                    final_image = self.compress_to_target_size(resized_image)

                    # Save the processed image
                    output_path = os.path.join(output_dir, os.path.splitext(file_name)[0] + ".jpg")
                    final_image.save(output_path, "JPEG")

                    # Get new file size
                    new_size = os.path.getsize(output_path) / 1024  # KB

                    # Update the tree view
                    for item in self.tree.get_children():
                        if self.tree.item(item, "values")[0] == file_name:
                            new_status = f"Done - {new_size:.1f} KB"
                            self.tree.item(item, values=(file_name, "1200x1200",
                                                         self.tree.item(item, "values")[2], new_status))
                            break

                    # Update progress
                    self.root.after(0, lambda: self.progress.step())

                except Exception as e:
                    # Update tree view with error status
                    for item in self.tree.get_children():
                        if self.tree.item(item, "values")[0] == file_name:
                            self.tree.item(item, values=(file_name, self.tree.item(item, "values")[1],
                                                         self.tree.item(item, "values")[2], f"Error: {str(e)[:20]}"))
                            break

                    # Update progress
                    self.root.after(0, lambda: self.progress.step())

            # Processing complete
            self.root.after(0, lambda: self.update_status(f"Processing complete! Images saved to: {output_dir}"))
            self.root.after(0, lambda: messagebox.showinfo("Processing Complete",
                                                           f"All images have been processed and saved to:\n{output_dir}"))

            # Re-enable buttons
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.select_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.output_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.remove_button.config(state=tk.NORMAL))

        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Error: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))

            # Re-enable buttons
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.select_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.output_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.remove_button.config(state=tk.NORMAL))

    def update_status(self, message):
        self.status_label.config(text=message)

    def resize_image(self, image):
        """Resize image to exactly 1200x1200 while maintaining aspect ratio (crop as needed)"""
        width, height = image.size
        target_width, target_height = self.target_dimensions

        # First, resize the image so the smaller dimension is exactly 1200 pixels
        if width < height:  # Portrait orientation
            # Resize based on width to make width 1200px
            resize_factor = target_width / width
            new_height = int(height * resize_factor)
            resized = image.resize((target_width, new_height), Image.Resampling.LANCZOS)
        else:  # Landscape or square orientation
            # Resize based on height to make height 1200px
            resize_factor = target_height / height
            new_width = int(width * resize_factor)
            resized = image.resize((new_width, target_height), Image.Resampling.LANCZOS)

        # Then crop from center to make it exactly 1200x1200
        width, height = resized.size
        left = (width - target_width) // 2
        top = (height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        # Crop to exact dimensions
        cropped = resized.crop((left, top, right, bottom))

        return cropped

    def compress_to_target_size(self, image):
        """Compress image to target size using binary search for optimal quality"""
        # Start with high quality for binary search
        min_quality = 1
        max_quality = 95
        current_quality = 85  # Start with a reasonable quality

        # For very large images, try with initial quality
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="JPEG", quality=current_quality)
        current_size = img_buffer.getbuffer().nbytes

        # If already below target, try to increase quality
        if current_size <= self.target_size:
            while current_quality < max_quality:
                new_quality = current_quality + 5
                if new_quality > max_quality:
                    new_quality = max_quality

                img_buffer = io.BytesIO()
                image.save(img_buffer, format="JPEG", quality=new_quality)
                new_size = img_buffer.getbuffer().nbytes

                if new_size <= self.target_size:
                    current_quality = new_quality
                    current_size = new_size
                else:
                    break
        else:
            # Binary search to find highest quality under target size
            while min_quality <= max_quality:
                current_quality = (min_quality + max_quality) // 2

                img_buffer = io.BytesIO()
                image.save(img_buffer, format="JPEG", quality=current_quality)
                current_size = img_buffer.getbuffer().nbytes

                if current_size > self.target_size:
                    max_quality = current_quality - 1
                else:
                    min_quality = current_quality + 1

                # Early exit if we're close enough
                if max_quality - min_quality <= 1:
                    # Make sure we're under target size
                    if current_size > self.target_size:
                        current_quality -= 1
                    break

        # Final save with best quality that fits target size
        final_img = image.copy()
        img_buffer = io.BytesIO()
        final_img.save(img_buffer, format="JPEG", quality=current_quality)

        # Return the compressed image
        img_buffer.seek(0)
        return Image.open(img_buffer)


if __name__ == "__main__":
    root = tk.Tk()
    app = BatchImageResizerApp(root)
    root.mainloop()