# Overview

This is a Telegram bot that converts PDF files and images into outlined/traced PDF versions. The bot processes uploaded documents by detecting edges and contours, then regenerating them as clean vector paths in a new PDF file. Users can send PDFs or images, and the bot returns a traced version with customizable parameters like stroke width, DPI, and color inversion.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Type
This is a Python-based Telegram bot application that performs image processing and PDF manipulation.

## Core Components

### Bot Layer (bot.py)
- **Framework**: python-telegram-bot library for Telegram Bot API integration
- **Handler Pattern**: Uses CommandHandler for `/start` command and MessageHandler for document/photo uploads
- **File Processing Flow**: Downloads files → Processes them → Returns traced PDF
- **Configuration**: Environment variables via dotenv (.env file)
  - `TELEGRAM_BOT_TOKEN`: Bot authentication
  - `DOWNLOAD_DIR`: Working directory for file operations (defaults to `./work`)

### Image Processing Pipeline (tracing.py)
- **Computer Vision**: OpenCV (cv2) for edge detection and contour extraction
- **Multi-step Processing**:
  1. PDF → Images (pdf2image library converts PDF pages to PIL Images at configurable DPI)
  2. Preprocessing (bilateral filtering, adaptive thresholding, morphological operations)
  3. Edge detection (Canny algorithm)
  4. Contour extraction and simplification (Douglas-Peucker algorithm)
  5. Vector conversion (contours → SVG paths)
  6. PDF generation (CairoSVG renders SVG to PDF bytes)

**Design Rationale**: This pipeline maintains quality while converting raster images to vector format, making the output suitable for printing patterns/templates.

### PDF Operations (utils_pdf.py)
- **Library**: PyPDF2 for merging multiple PDF pages
- **In-Memory Processing**: Uses BytesIO to avoid disk I/O overhead
- **Purpose**: Combines individual page PDFs into a single multi-page document

### User-Configurable Parameters
Users can customize processing via caption text:
- `invert=true/false`: Controls whether to invert colors (default: true)
- `stroke=<number>`: Line thickness in SVG output (default: 2.0)
- `dpi=<number>`: Resolution for PDF rasterization (default: 400)

**Example**: "invert=false stroke=1.5 dpi=300"

## Processing Architecture

### Asynchronous Design
- **Async/Await Pattern**: All bot handlers use async functions to handle concurrent user requests
- **Non-blocking I/O**: File downloads and processing don't block other users

### File Handling
- **Temporary Storage**: Files downloaded to `DOWNLOAD_DIR` for processing
- **Input Support**: Accepts PDF documents and photos (JPEG/PNG via Telegram photo messages)
- **Output Naming**: Prefixes output files with "outlined_" and ensures .pdf extension

## Error Handling Strategy
The bot implements basic validation:
- Checks for valid document/photo types before processing
- Verifies PDF vs image files via MIME type and file extension
- Provides user feedback during processing ("Đang xử lý, vui lòng chờ...⏳")

**Note**: The code appears incomplete in bot.py (missing try-except completion), suggesting error handling may need enhancement.

# External Dependencies

## Telegram Integration
- **python-telegram-bot (v20.6)**: Main framework for bot functionality
- **API**: Telegram Bot API for receiving messages, downloading files, sending responses
- **Authentication**: Requires TELEGRAM_BOT_TOKEN environment variable

## Image Processing Libraries
- **OpenCV (opencv-python ≥4.8.0)**: Edge detection, contour finding, morphological operations
- **NumPy (≥1.26.0)**: Array operations for image data
- **Pillow (≥10.0.0)**: Image format conversions and PIL compatibility

## PDF Processing
- **pdf2image (≥1.17.0)**: Converts PDF pages to raster images (requires poppler-utils system dependency)
- **PyPDF2**: Merges individual PDF pages into single documents
- **ReportLab (≥4.1.0)**: Listed but not actively used in current code

## Vector Graphics
- **svgwrite (≥1.4.3)**: Creates SVG documents from contour paths
- **CairoSVG (≥2.7.1)**: Renders SVG to PDF format (requires Cairo system library)

## Configuration
- **python-dotenv (≥1.0.1)**: Loads environment variables from .env file

## System Dependencies (Not in requirements.txt)
- **poppler-utils**: Required by pdf2image for PDF rendering
- **Cairo**: Required by CairoSVG for PDF generation

**Note**: requirements.txt contains duplicates (multiple entries for same packages), which should be cleaned up during deployment.