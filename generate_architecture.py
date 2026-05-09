"""
Generate ARCHITECTURE.png for the Mega AI Face Detection assignment.
Uses Pillow to draw a professional system architecture diagram.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Canvas setup
WIDTH, HEIGHT = 1600, 1200
BG_COLOR = (15, 23, 42)  # #0f172a matching the app theme
BOX_BG = (30, 41, 59)    # #1e293b
BORDER_COLOR = (51, 65, 85)  # #334155
TEXT_PRIMARY = (241, 245, 249)  # #f1f5f9
TEXT_SECONDARY = (148, 163, 184)  # #94a3b8
ACCENT = (56, 189, 248)  # #38bdf8
SUCCESS = (74, 222, 128)  # #4ade80
WARNING = (251, 191, 36)  # #fbbf24
ARROW_COLOR = (148, 163, 184)

# Try to load a font, fall back to default
try:
    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    font_medium = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
except:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

def draw_rounded_rect(draw, xy, fill, outline=None, width=2, radius=12):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_arrow(draw, start, end, color=ARROW_COLOR, width=3, label=""):
    """Draw an arrow with optional label."""
    x1, y1 = start
    x2, y2 = end
    draw.line([start, end], fill=color, width=width)
    
    # Arrowhead
    if x1 == x2:  # Vertical
        if y2 > y1:
            draw.polygon([(x2, y2), (x2-8, y2-12), (x2+8, y2-12)], fill=color)
        else:
            draw.polygon([(x2, y2), (x2-8, y2+12), (x2+8, y2+12)], fill=color)
    else:  # Horizontal
        if x2 > x1:
            draw.polygon([(x2, y2), (x2-12, y2-8), (x2-12, y2+8)], fill=color)
        else:
            draw.polygon([(x2, y2), (x2+12, y2-8), (x2+12, y2+8)], fill=color)
    
    if label:
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        bbox = draw.textbbox((0, 0), label, font=font_small)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        # Draw label background
        padding = 4
        draw.rounded_rectangle(
            [mid_x - text_w//2 - padding, mid_y - text_h//2 - padding,
             mid_x + text_w//2 + padding, mid_y + text_h//2 + padding],
            radius=4, fill=BG_COLOR
        )
        draw.text((mid_x - text_w//2, mid_y - text_h//2), label, fill=ACCENT, font=font_small)

def draw_box(draw, xy, title, subtitle="", color=BORDER_COLOR, icon=""):
    """Draw a labeled box."""
    x1, y1, x2, y2 = xy
    draw_rounded_rect(draw, xy, fill=BOX_BG, outline=color, width=2)
    
    # Title
    title_y = y1 + 15
    bbox = draw.textbbox((0, 0), title, font=font_medium)
    text_w = bbox[2] - bbox[0]
    draw.text((x1 + (x2-x1)//2 - text_w//2, title_y), title, fill=TEXT_PRIMARY, font=font_medium)
    
    if subtitle:
        sub_y = title_y + 30
        bbox = draw.textbbox((0, 0), subtitle, font=font_small)
        text_w = bbox[2] - bbox[0]
        draw.text((x1 + (x2-x1)//2 - text_w//2, sub_y), subtitle, fill=TEXT_SECONDARY, font=font_small)
    
    return y2  # Return bottom for layout

# Create image
img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

# Title
title_text = "Mega AI — Real-Time Face Detection Architecture"
bbox = draw.textbbox((0, 0), title_text, font=font_large)
text_w = bbox[2] - bbox[0]
draw.text((WIDTH//2 - text_w//2, 30), title_text, fill=TEXT_PRIMARY, font=font_large)

# Subtitle
sub_text = "WebSocket Ingest | MediaPipe Detection | MJPEG Stream | PostgreSQL Persistence"
bbox = draw.textbbox((0, 0), sub_text, font=font_small)
text_w = bbox[2] - bbox[0]
draw.text((WIDTH//2 - text_w//2, 75), sub_text, fill=TEXT_SECONDARY, font=font_small)

# Layout constants
LEFT_X = 80
CENTER_X = WIDTH // 2
RIGHT_X = WIDTH - 80
BOX_WIDTH = 320
BOX_HEIGHT = 140

# ==================== BROWSER (Left) ====================
browser_y = 200
draw_box(draw, [LEFT_X, browser_y, LEFT_X + BOX_WIDTH, browser_y + BOX_HEIGHT],
         "Browser (React/Vite)", "Camera + MJPEG Display", color=ACCENT)

# ==================== FASTAPI (Center) ====================
api_y = 200
draw_box(draw, [CENTER_X - BOX_WIDTH//2, api_y, CENTER_X + BOX_WIDTH//2, api_y + BOX_HEIGHT],
         "FastAPI Backend", "Python 3.11 | AsyncIO", color=SUCCESS)

# Arrows: Browser ↔ FastAPI
# WebSocket upload
draw_arrow(draw, (LEFT_X + BOX_WIDTH, browser_y + 50), (CENTER_X - BOX_WIDTH//2, api_y + 50), 
           label="WebSocket JPEG")
# MJPEG stream back
draw_arrow(draw, (CENTER_X - BOX_WIDTH//2, api_y + 90), (LEFT_X + BOX_WIDTH, browser_y + 90), 
           label="MJPEG Stream")

# ==================== INTERNAL COMPONENTS (Inside FastAPI) ====================
# Draw a container around internal components
container_y = 380
container_x1 = CENTER_X - 380
container_x2 = CENTER_X + 380
draw_rounded_rect(draw, [container_x1, container_y, container_x2, container_y + 280], 
                  fill=(20, 30, 50), outline=BORDER_COLOR, width=1, radius=16)

draw.text((CENTER_X - 60, container_y + 10), "Internal Pipeline", fill=TEXT_SECONDARY, font=font_small)

# Component boxes
comp_width = 200
comp_height = 80
comp_y = container_y + 50

# WebSocket Handler
wh_x = container_x1 + 30
draw_box(draw, [wh_x, comp_y, wh_x + comp_width, comp_y + comp_height],
         "WebSocket Handler", "Receive frames", color=BORDER_COLOR)

# FrameProcessor
fp_x = wh_x + comp_width + 40
draw_box(draw, [fp_x, comp_y, fp_x + comp_width, comp_y + comp_height],
         "FrameProcessor", "Pillow + MediaPipe", color=WARNING)

# StreamManager
sm_x = fp_x + comp_width + 40
draw_box(draw, [sm_x, comp_y, sm_x + comp_width, comp_y + comp_height],
         "StreamManager", "In-memory buffer", color=BORDER_COLOR)

# Arrows between components
draw_arrow(draw, (wh_x + comp_width, comp_y + 40), (fp_x, comp_y + 40), label="bytes")
draw_arrow(draw, (fp_x + comp_width, comp_y + 40), (sm_x, comp_y + 40), label="annotated")

# Second row of components
comp_y2 = comp_y + comp_height + 30

# ROI Repository
repo_x = container_x1 + 30
draw_box(draw, [repo_x, comp_y2, repo_x + comp_width, comp_y2 + comp_height],
         "ROI Repository", "SQLAlchemy + asyncpg", color=BORDER_COLOR)

# MJPEG Generator
mjpeg_x = repo_x + comp_width + 40
draw_box(draw, [mjpeg_x, comp_y2, mjpeg_x + comp_width, comp_y2 + comp_height],
         "MJPEG Generator", "Multipart stream", color=BORDER_COLOR)

# ROI API
roi_x = mjpeg_x + comp_width + 40
draw_box(draw, [roi_x, comp_y2, roi_x + comp_width, comp_y2 + comp_height],
         "ROI REST API", "GET /rois", color=BORDER_COLOR)

# Arrows from StreamManager to outputs
draw_arrow(draw, (sm_x + comp_width//2, comp_y + comp_height), 
           (mjpeg_x + comp_width//2, comp_y2), label="frames")
draw_arrow(draw, (fp_x + comp_width//2, comp_y + comp_height), 
           (repo_x + comp_width//2, comp_y2), label="ROI data")

# ==================== POSTGRESQL (Right) ====================
db_y = 200
draw_box(draw, [RIGHT_X - BOX_WIDTH, db_y, RIGHT_X, db_y + BOX_HEIGHT],
         "PostgreSQL 15", "ROI Events + Stream Sessions", color=ACCENT)

# Arrow: Repository → PostgreSQL
draw_arrow(draw, (repo_x + comp_width, comp_y2 + 40), (RIGHT_X - BOX_WIDTH, db_y + 70), 
           label="Persist")

# ==================== DOCKER (Bottom) ====================
docker_y = HEIGHT - 220
draw_rounded_rect(draw, [LEFT_X, docker_y, RIGHT_X, docker_y + 160], 
                  fill=(25, 35, 55), outline=BORDER_COLOR, width=2, radius=16)

draw.text((CENTER_X - 50, docker_y + 15), "Docker Compose", fill=TEXT_SECONDARY, font=font_medium)

# Docker containers
dock_box_w = 280
dock_box_h = 80
dock_y = docker_y + 60

# Frontend container
df_x = LEFT_X + 40
draw_box(draw, [df_x, dock_y, df_x + dock_box_w, dock_y + dock_box_h],
         "Frontend Container", "Node 20 + Vite", color=SUCCESS)

# Backend container
db_x = df_x + dock_box_w + 60
draw_box(draw, [db_x, dock_y, db_x + dock_box_w, dock_y + dock_box_h],
         "Backend Container", "Python 3.11 + MediaPipe", color=SUCCESS)

# DB container
db2_x = db_x + dock_box_w + 60
draw_box(draw, [db2_x, dock_y, db2_x + dock_box_w, dock_y + dock_box_h],
         "DB Container", "PostgreSQL 15", color=SUCCESS)

# Network indicator
draw.text((CENTER_X - 80, dock_y + dock_box_h + 15), "Shared Network: megaaiassignment2_default", 
          fill=TEXT_SECONDARY, font=font_small)

# ==================== LEGEND (Bottom Left) ====================
legend_y = HEIGHT - 380
draw.text((LEFT_X, legend_y), "Legend:", fill=TEXT_PRIMARY, font=font_medium)
legend_items = [
    (ACCENT, "WebSocket / HTTP Traffic"),
    (SUCCESS, "Docker Container"),
    (WARNING, "Processing Component"),
    (TEXT_SECONDARY, "Data Flow"),
]
for i, (color, text) in enumerate(legend_items):
    y = legend_y + 35 + i * 28
    draw.rounded_rectangle([LEFT_X, y, LEFT_X + 20, y + 20], radius=4, fill=color)
    draw.text((LEFT_X + 30, y - 2), text, fill=TEXT_SECONDARY, font=font_small)

# Save
output_path = "ARCHITECTURE.png"
img.save(output_path, "PNG", quality=95)
print(f"Saved {output_path} ({WIDTH}x{HEIGHT})")
