import os
import zipfile
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# For PDF extraction, install PyMuPDF: pip install pymupdf
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# ---------- Extraction Functions ----------

def extract_images_from_zip(file_path, media_folder, output_folder, log):
    """
    Extract images from a zipped file (pptx or docx) by reading the media folder.
    """
    try:
        with zipfile.ZipFile(file_path, "r") as z:
            media_files = [f for f in z.namelist() if f.startswith(media_folder) and not f.endswith('/')]
            if not media_files:
                log(f"No images found in {media_folder}.")
                return
            for file in media_files:
                data = z.read(file)
                filename = os.path.basename(file)
                out_path = os.path.join(output_folder, filename)
                with open(out_path, "wb") as f_out:
                    f_out.write(data)
                log(f"Saved {filename} to {output_folder}")
    except Exception as e:
        log(f"Error processing {file_path}: {e}")

def extract_images_from_pdf(file_path, output_folder, log):
    """
    Extract images from a PDF file using PyMuPDF.
    """
    if fitz is None:
        log("PyMuPDF is not installed. Cannot extract images from PDF.")
        return

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        log(f"Error opening PDF file: {e}")
        return

    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)
        log(f"Found {len(image_list)} images on page {page_index + 1}")
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception as e:
                log(f"Error extracting image {xref}: {e}")
                continue
            image_bytes = base_image.get("image")
            image_ext = base_image.get("ext", "png")
            image_filename = f"image_page{page_index+1}_{img_index}.{image_ext}"
            out_path = os.path.join(output_folder, image_filename)
            try:
                with open(out_path, "wb") as f_out:
                    f_out.write(image_bytes)
                log(f"Saved image {image_filename}")
            except Exception as e:
                log(f"Error saving image {image_filename}: {e}")

def extract_images(file_path, log):
    """
    Determine file type and extract images accordingly.
    """
    if not os.path.exists(file_path):
        log("File does not exist.")
        return

    output_folder = "extracted_images"
    os.makedirs(output_folder, exist_ok=True)
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pptx":
        log("Extracting images from PowerPoint file...")
        extract_images_from_zip(file_path, "ppt/media/", output_folder, log)
    elif ext == ".docx":
        log("Extracting images from Word document...")
        extract_images_from_zip(file_path, "word/media/", output_folder, log)
    elif ext == ".pdf":
        log("Extracting images from PDF file...")
        extract_images_from_pdf(file_path, output_folder, log)
    else:
        log("Unsupported file type. Supported file types are: .pptx, .docx, .pdf")

# ---------- Tkinter GUI ----------

class ImageExtractorApp:
    def __init__(self, master):
        self.master = master
        master.title("File Image Extractor")

        self.selected_file = None

        # File selection frame
        self.file_frame = tk.Frame(master)
        self.file_frame.pack(pady=10)

        self.choose_button = tk.Button(self.file_frame, text="Browse File", command=self.browse_file)
        self.choose_button.pack(side=tk.LEFT, padx=5)

        self.file_label = tk.Label(self.file_frame, text="No file selected", width=50, anchor="w")
        self.file_label.pack(side=tk.LEFT, padx=5)

        # Extraction button
        self.extract_button = tk.Button(master, text="Extract Images", command=self.start_extraction)
        self.extract_button.pack(pady=5)

        # Log output (scrolled text widget)
        self.log_box = scrolledtext.ScrolledText(master, width=80, height=20, state="disabled")
        self.log_box.pack(pady=10)

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")
        print(message)

    def browse_file(self):
        filetypes = [
            ("PowerPoint files", "*.pptx"),
            ("Word Documents", "*.docx"),
            ("PDF files", "*.pdf")
        ]
        file_path = filedialog.askopenfilename(title="Select a file", filetypes=filetypes)
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.log(f"Selected file: {file_path}")

    def start_extraction(self):
        if not self.selected_file:
            messagebox.showwarning("No file", "Please select a file first!")
            return
        self.log("Starting extraction...")
        extract_images(self.selected_file, self.log)
        self.log("Extraction complete. Check the 'extracted_images' folder.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageExtractorApp(root)
    root.mainloop()
