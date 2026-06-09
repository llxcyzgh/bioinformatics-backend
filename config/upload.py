import os

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploads")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_DATA_EXTENSIONS = {
    ".fastq", ".fq", ".fasta", ".fa", ".fna",
    ".gz", ".csv", ".tsv", ".xlsx", ".biom",
    ".zip", ".tar.gz", ".tar.bz2", ".7z",
}
ARCHIVE_EXTENSIONS = {".gz", ".zip", ".tar.gz", ".tar.bz2", ".7z"}
ALLOWED_ALL_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DATA_EXTENSIONS | {".pdf", ".txt", ".md"}
