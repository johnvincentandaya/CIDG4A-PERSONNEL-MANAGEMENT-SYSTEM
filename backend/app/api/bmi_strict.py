from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import calendar
import os
from .. import models
from ..utils import safe_resolve_upload_path


def compute_bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> float:
    try:
        if not weight_kg or not height_cm:
            return 0.0
        h_m = float(height_cm) / 100.0
        if h_m <= 0:
            return 0.0
        return float(weight_kg) / (h_m * h_m)
    except Exception:
        return 0.0


def draw_record_pdf_page(c: canvas.Canvas, rec: models.BMIRecord, db, prepared_by: str = "", noted_by: str = "", report_month: int = None, report_year: int = None) -> None:
    """Draw the BMI form using absolute positioning only (no Platypus tables).

    This implementation follows the user's exact layout specs and uses
    canvas primitives (rect, lines, drawString) so positions are deterministic.
    """

    PAGE_WIDTH = 842
    PAGE_HEIGHT = 595

    # Page margin and main border per spec
    MARGIN = 10
    MAIN_X = 10
    MAIN_Y = 10
    MAIN_W = 822
    MAIN_H = 575

    # Set drawing defaults
    c.setLineWidth(1)
    # color palette (strict, government-style)
    DARK_BORDER = colors.HexColor('#4f4f4f')
    TABLE_HEADER_BG = colors.HexColor('#e0e0e0')
    SECTION_HEADER_BG = colors.HexColor('#d0d0d0')
    ALT_ROW_BG = colors.HexColor('#f5f5f5')
    CELL_PADDING = 6
    c.setStrokeColor(DARK_BORDER)
    # Default fill for text should be black to avoid invisible/white text
    c.setFillColor(colors.black)

    # Draw main border
    c.rect(MAIN_X, MAIN_Y, MAIN_W, MAIN_H, stroke=1, fill=0)

    # Title
    title = 'INDIVIDUAL BMI MONITORING FORM'
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(PAGE_WIDTH / 2.0, 555, title)

    # PHOTO SECTION
    PHOTO_X = 20
    PHOTO_Y = 330
    PHOTO_W = 380
    PHOTO_H = 190
    c.rect(PHOTO_X, PHOTO_Y, PHOTO_W, PHOTO_H, stroke=1, fill=0)

    # Each photo box
    IMG_W = 110
    IMG_H = 160
    # compute equal gaps (4 gaps: left, between1, between2, right)
    total_photos_width = 3 * IMG_W
    gap = (PHOTO_W - total_photos_width) / 4.0
    img_positions = []
    cur_x = PHOTO_X + gap
    for _ in range(3):
        img_positions.append(cur_x)
        cur_x += IMG_W + gap

    img_y = PHOTO_Y + (PHOTO_H - IMG_H) / 2.0

    def _draw_img_box(path, x, y, w, h):
        # Draw the outer box
        c.rect(x, y, w, h, stroke=1, fill=0)
        if not path:
            return
        try:
            abs_p = safe_resolve_upload_path(path)
            if not abs_p or not os.path.exists(abs_p):
                return
            reader = ImageReader(abs_p)
            iw, ih = reader.getSize()
            scale = min(w / iw, h / ih)
            dw, dh = iw * scale, ih * scale
            dx = x + (w - dw) / 2.0
            dy = y + (h - dh) / 2.0
            c.drawImage(abs_p, dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
        except Exception:
            return

    # Draw the three photos: right, front, left
    _draw_img_box(getattr(rec, 'photo_right', None), img_positions[0], img_y, IMG_W, IMG_H)
    _draw_img_box(getattr(rec, 'photo_front', None), img_positions[1], img_y, IMG_W, IMG_H)
    _draw_img_box(getattr(rec, 'photo_left', None), img_positions[2], img_y, IMG_W, IMG_H)

    # Photo labels
    c.setFont('Helvetica', 10)
    labels = ['Right View', 'Front View', 'Left View']
    for i, lab in enumerate(labels):
        cx = img_positions[i] + IMG_W / 2.0
        # label sits just below the image box
        ly = img_y - 12
        c.drawCentredString(cx, ly, lab)

    

    # INFO TABLE (absolute rows)
    INFO_X = 440
    INFO_Y = 345
    INFO_W = 370
    INFO_H = 180
    c.rect(INFO_X, INFO_Y, INFO_W, INFO_H, stroke=1, fill=0)

    # Rows
    ROW_H = 22
    labels = ['RANK/NAME', 'UNIT', 'AGE', 'GENDER', 'HEIGHT', 'WEIGHT', 'BMI RESULT', 'CLASSIFICATION']
    # label column width and value column
    LABEL_W = 140
    VALUE_W = INFO_W - LABEL_W

    # draw vertical separator
    sep_x = INFO_X + LABEL_W
    c.line(sep_x, INFO_Y, sep_x, INFO_Y + INFO_H)

    # function to draw text and shrink to fit
    def draw_text_shrink(text, fontname, max_size, box_x, box_w, y, align='left', min_size=6):
        size = max_size
        while size >= min_size:
            width = c.stringWidth(text, fontname, size)
            if width <= box_w - 6:
                break
            size -= 0.5
        c.setFont(fontname, size)
        if align == 'left':
            c.drawString(box_x + 4, y, text)
        else:
            c.drawCentredString(box_x + box_w / 2.0, y, text)

    # Draw rows from top down
    for idx, label in enumerate(labels):
        row_top = INFO_Y + INFO_H - (idx * ROW_H)
        # horizontal line for row top
        c.line(INFO_X, row_top, INFO_X + INFO_W, row_top)
        # vertical divider already drawn
        # text baseline: place text vertically centered within row
        text_y = row_top - ROW_H + (ROW_H - 11) / 2.0 + 2
        draw_text_shrink(label, 'Helvetica-Bold', 11, INFO_X, LABEL_W, text_y, align='left')
        # values
        if label == 'RANK/NAME':
            val = f"{(rec.rank or '')} {(getattr(rec, 'display_name', rec.name) or '')}".strip()
        elif label == 'UNIT':
            val = rec.unit or ''
        elif label == 'AGE':
            val = str(rec.age or '')
        elif label == 'GENDER':
            val = rec.sex or ''
        elif label == 'HEIGHT':
            val = f"{(rec.height_cm or '')}"
        elif label == 'WEIGHT':
            val = f"{(rec.weight_kg or '')}"
        elif label == 'BMI RESULT':
            bmi_value = compute_bmi(rec.weight_kg or 0, rec.height_cm or 0)
            val = f"{bmi_value:.2f}" if bmi_value else ''
        elif label == 'CLASSIFICATION':
            bmi_value = compute_bmi(rec.weight_kg or 0, rec.height_cm or 0)
            if bmi_value <= 0:
                val = ''
            elif bmi_value < 18.5:
                val = 'Underweight'
            elif bmi_value < 25:
                val = 'Normal'
            elif bmi_value < 30:
                val = 'Overweight'
            else:
                val = 'Obese'
        else:
            val = ''
        draw_text_shrink(val, 'Helvetica', 11, INFO_X + LABEL_W, VALUE_W, text_y, align='left')

    # bottom line of info table
    c.line(INFO_X, INFO_Y, INFO_X + INFO_W, INFO_Y)

    # Profile section header (shaded) spanning photo + info areas
    profile_header_x = PHOTO_X
    profile_header_w = (INFO_X + INFO_W) - PHOTO_X
    profile_header_h = 18
    # place header just above the photo/info boxes
    profile_header_y = INFO_Y + INFO_H + 6
    c.setFillColor(SECTION_HEADER_BG)
    c.rect(profile_header_x, profile_header_y, profile_header_w, profile_header_h, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(profile_header_x + CELL_PADDING, profile_header_y + (profile_header_h - 10) / 2.0 + 2, 'Profile Information')

    # BMI CLASSIFICATION BOX (two-column: PNP Standard | WHO Standard)
    CLASS_X = 20
    CLASS_Y = 170
    CLASS_W = 380
    CLASS_H = 120
    c.rect(CLASS_X, CLASS_Y, CLASS_W, CLASS_H, stroke=1, fill=0)
    # header bar
    header_h = 18
    c.setFillColor(TABLE_HEADER_BG)
    c.rect(CLASS_X, CLASS_Y + CLASS_H - header_h, CLASS_W, header_h, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(CLASS_X + CLASS_W / 2.0, CLASS_Y + CLASS_H - header_h + (header_h - 10) / 2.0 + 2, 'BMI CLASSIFICATION')
    # split body into two columns
    inner_top = CLASS_Y + CLASS_H - header_h
    left_w = CLASS_W / 2.0
    right_w = CLASS_W - left_w
    c.line(CLASS_X + left_w, CLASS_Y, CLASS_X + left_w, inner_top)
    # sub-headers for each column
    sub_h = 16
    c.setFillColor(TABLE_HEADER_BG)
    c.rect(CLASS_X, inner_top - sub_h, left_w, sub_h, stroke=0, fill=1)
    c.rect(CLASS_X + left_w, inner_top - sub_h, right_w, sub_h, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(CLASS_X + left_w / 2.0, inner_top - sub_h + (sub_h - 9) / 2.0 + 2, 'PNP Standard')
    c.drawCentredString(CLASS_X + left_w + right_w / 2.0, inner_top - sub_h + (sub_h - 9) / 2.0 + 2, 'WHO Standard')
    # classification values (same calculation used for both columns here)
    bmi_value = compute_bmi(rec.weight_kg or 0, rec.height_cm or 0)
    if bmi_value <= 0:
        class_text = ''
    elif bmi_value < 18.5:
        class_text = 'Underweight'
    elif bmi_value < 25:
        class_text = 'Normal'
    elif bmi_value < 30:
        class_text = 'Overweight'
    else:
        class_text = 'Obese'
    c.setFont('Helvetica', 11)
    body_y = inner_top - sub_h - 20
    c.drawCentredString(CLASS_X + left_w / 2.0, body_y, class_text)
    c.drawCentredString(CLASS_X + left_w + right_w / 2.0, body_y, class_text)

    # INTERVENTION BOX (shaded header + structured rows)
    INT_X = 420
    INT_Y = 170
    INT_W = 390
    INT_H = 120
    c.rect(INT_X, INT_Y, INT_W, INT_H, stroke=1, fill=0)
    # header
    hdr_h = 18
    c.setFillColor(TABLE_HEADER_BG)
    c.rect(INT_X, INT_Y + INT_H - hdr_h, INT_W, hdr_h, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(INT_X + INT_W / 2.0, INT_Y + INT_H - hdr_h + (hdr_h - 10) / 2.0 + 2, 'Intervention Package')
    # structured rows inside intervention box
    c.setFont('Helvetica', 10)
    pkg_map = {
        'Underweight': ('A', '3 months', 'Nutritional counseling'),
        'Normal': ('B', '0 months', 'Maintain'),
        'Overweight': ('C', '3 months', 'Exercise & diet'),
        'Obese': ('D', '6 months', 'Intensive intervention'),
    }
    pkg = pkg_map.get(class_text, ('', '', ''))
    r1_y = INT_Y + INT_H - hdr_h - 26
    c.drawString(INT_X + CELL_PADDING, r1_y, f'Package: {pkg[0]}')
    c.drawString(INT_X + CELL_PADDING, r1_y - 14, f'Duration: {pkg[1]}')
    # wrap notes if necessary (simple center)
    c.drawString(INT_X + CELL_PADDING, r1_y - 28, f'Notes: {pkg[2]}')

    # SIGNATURE area (simple line)
    SIG_RIGHT_W = 250
    SIG_LEFT_W = MAIN_W - SIG_RIGHT_W
    # make sure signature left width does not exceed left column (use left column width 430)
    if SIG_LEFT_W > 430:
        SIG_LEFT_W = 430
    sig_x = MAIN_X
    sig_y = 120
    c.line(sig_x + SIG_LEFT_W, sig_y + 20, sig_x + SIG_LEFT_W + SIG_RIGHT_W - 20, sig_y + 20)
    c.setFont('Helvetica', 10)
    c.drawString(sig_x + SIG_LEFT_W + 6, sig_y + 24, 'Certified Correct Signature:')

    # BOTTOM TIMELINE - Full-width table with YEAR (spanning), MONTHS, WEIGHT rows
    TIM_X = 15
    TIM_Y = 25
    TIM_W = 800
    # increase height to accommodate YEAR row + months + weights
    TIM_H = 72
    c.setStrokeColor(DARK_BORDER)
    c.setLineWidth(1)
    # ensure text fill is black (avoid any white text)
    c.setFillColor(colors.black)
    c.rect(TIM_X, TIM_Y, TIM_W, TIM_H, stroke=1, fill=0)

    # Build months (14) with selected month at far right
    if report_year and report_month:
        ref = datetime(report_year, report_month, 1)
    else:
        ref = datetime.utcnow()
    months = []
    # oldest first, newest last (left -> right)
    for i in range(13, -1, -1):
        m = ref.month - i
        y = ref.year
        while m <= 0:
            m += 12; y -= 1
        while m > 12:
            m -= 12; y += 1
        months.append((y, m))

    ncols = len(months)
    col_w = TIM_W / float(ncols)

    # row heights
    year_h = 18
    month_h = 18
    weight_h = TIM_H - (year_h + month_h)
    top_y = TIM_Y + TIM_H
    year_y0 = top_y - year_h
    month_y0 = year_y0 - month_h

    # Title above the months table (centered). Keep fill color black for text.
    try:
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(colors.black)
        title_y = top_y + 6
        c.drawCentredString(TIM_X + TIM_W / 2.0, title_y, 'Monthly Weight Monitoring')
    except Exception:
        # fail-safe: do not interrupt drawing if title placement fails
        pass

    # shaded header rows (YEAR and MONTHS)
    c.setFillColor(TABLE_HEADER_BG)
    c.rect(TIM_X, year_y0, TIM_W, year_h, stroke=0, fill=1)
    c.setFillColor(ALT_ROW_BG)
    c.rect(TIM_X, month_y0, TIM_W, month_h, stroke=0, fill=1)
    c.setFillColor(colors.black)

    # Year grouping: merge contiguous months with same year and draw centered year
    groups = []
    start = 0
    cur_year = months[0][0]
    for i, (yy, mm) in enumerate(months):
        if yy != cur_year:
            groups.append((start, i - 1, cur_year))
            start = i
            cur_year = yy
    groups.append((start, ncols - 1, cur_year))

    c.setFont('Helvetica-Bold', 9)
    for (sidx, eidx, yy) in groups:
        gx = TIM_X + sidx * col_w
        gw = (eidx - sidx + 1) * col_w
        # draw spanning cell with border
        c.setStrokeColor(DARK_BORDER)
        c.setFillColor(TABLE_HEADER_BG)
        c.rect(gx, year_y0, gw, year_h, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(gx + gw / 2.0, year_y0 + (year_h - 9) / 2.0 + 2, str(yy))

    # draw vertical separators + outer border (grid)
    c.setStrokeColor(DARK_BORDER)
    for i in range(ncols + 1):
        x = TIM_X + i * col_w
        c.line(x, TIM_Y, x, TIM_Y + TIM_H)

    # horizontal separators between rows
    c.line(TIM_X, year_y0, TIM_X + TIM_W, year_y0)
    c.line(TIM_X, month_y0, TIM_X + TIM_W, month_y0)
    c.line(TIM_X, TIM_Y, TIM_X + TIM_W, TIM_Y)

    # load monthly weights
    weights_map = {}
    try:
        if getattr(rec, 'personnel_id', None):
            rows = db.query(models.BMIHistory).filter(models.BMIHistory.personnel_id == rec.personnel_id).all()
            for r in rows:
                weights_map[(int(r.year), int(r.month))] = getattr(r, 'weight', None)
    except Exception:
        weights_map = {}

    # write month abbreviations and weight values (centered in each cell)
    c.setFont('Helvetica-Bold', 9)
    for idx, (yy, mm) in enumerate(months):
        cx = TIM_X + idx * col_w + col_w / 2.0
        month_abbr = calendar.month_abbr[mm]
        c.setFillColor(colors.black)
        c.drawCentredString(cx, month_y0 + (month_h - 9) / 2.0 + 2, month_abbr)

    # weights row (single data row)
    c.setFont('Helvetica', 9)
    for idx, (yy, mm) in enumerate(months):
        cx = TIM_X + idx * col_w + col_w / 2.0
        wv = weights_map.get((yy, mm))
        wtext = f"{float(wv):.1f}" if (wv is not None) else ''
        c.setFillColor(colors.black)
        c.drawCentredString(cx, TIM_Y + (weight_h - 9) / 2.0 + 4, wtext)

    return
