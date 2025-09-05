import cv2
import numpy as np
import time

PALETTE_COLS = [
    ((0, 0, 255), "Red"),
    ((0, 255, 0), "Green"),
    ((255, 0, 0), "Blue"),
    ((0, 255, 255), "Yellow"),
    ((255, 0, 255), "Magenta"),
    ((255, 255, 255), "Eraser"),
    ("CLEAR", "Clear")
]
PALETTE_BOX_W  = 110
HEADER_HEIGHT = 80
HOVER_SELECT_SECONDS = 0.5
BRUSH_THICKNESS = 8
PALM_CLEAR_SECONDS = 0.6

hover_start_time = None
hovered_box_idx = None
palm_start_time = None
prev_x, prev_y = None, None
paused = False
current_color = (0, 0, 255)
current_color_name = "Red"

def get_finger_status(lm):
    tips = [4, 8, 12, 16, 20]
    status = [0,0,0,0,0]
    try:
        status[0] = int(lm[tips[0]].x < lm[tips[0]-1].x)
        for i in range(1,5):
            status[i] = int(lm[tips[i]].y < lm[tips[i]-2].y)
    except:
        pass
    return status

def map_fingertip_to_palette(x, y):
    if HEADER_HEIGHT <= y <= (HEADER_HEIGHT + 80):
        idx = x // PALETTE_BOX_W
        if 0 <= idx < len(PALETTE_COLS):
            return idx
    return None

def run(frame, canvas_frame, results, last_action):
    global hover_start_time, hovered_box_idx, palm_start_time
    global prev_x, prev_y, paused, current_color, current_color_name

    h, w = frame.shape[:2]
    if results.multi_hand_landmarks:
        lms = results.multi_hand_landmarks[0].landmark
        ix, iy = int(lms[8].x * w), int(lms[8].y * h)
        finger_status = get_finger_status(lms)
        total_up = sum(finger_status)

        # Palette hover
        hovered_idx = map_fingertip_to_palette(ix, iy)
        if hovered_idx is not None:
            if hovered_box_idx != hovered_idx:
                hover_start_time = time.time()
                hovered_box_idx = hovered_idx
            else:
                if hover_start_time and (time.time()-hover_start_time) >= HOVER_SELECT_SECONDS:
                    box = PALETTE_COLS[hovered_idx][0]
                    name = PALETTE_COLS[hovered_idx][1]
                    if box == "CLEAR":
                        canvas_frame[:] = 255
                        last_action = "Canvas Cleared"
                    else:
                        current_color = box
                        current_color_name = name
                        last_action = f"Color: {name}"
                    hover_start_time = None
                    hovered_box_idx = None
        else:
            hover_start_time = None
            hovered_box_idx = None

        # Palm clear
        if total_up == 5:
            if palm_start_time is None:
                palm_start_time = time.time()
            else:
                if (time.time() - palm_start_time) >= PALM_CLEAR_SECONDS:
                    canvas_frame[:] = 255
                    last_action = "Canvas Cleared"
                    palm_start_time = None
        else:
            palm_start_time = None

        # Draw
        index_up = finger_status[1]==1
        middle_up = finger_status[2]==1
        only_index_up = index_up and not any([finger_status[0], finger_status[2], finger_status[3], finger_status[4]])
        if index_up and middle_up and not (finger_status[3] or finger_status[4]):
            paused = True
            prev_x, prev_y = None, None
        elif only_index_up:
            paused = False
            if prev_x is None or prev_y is None:
                prev_x, prev_y = ix, iy
            else:
                draw_col = (255,255,255) if current_color_name=="Eraser" else current_color
                cv2.line(canvas_frame, (prev_x, prev_y), (ix, iy), draw_col, BRUSH_THICKNESS)
                prev_x, prev_y = ix, iy

        # Draw pointer
        cv2.circle(frame, (ix, iy), 8, (0,120,255), -1)

    else:
        hover_start_time = None
        hovered_box_idx = None
        palm_start_time = None
        prev_x, prev_y = None, None

    # Overlay canvas
    gray = cv2.cvtColor(canvas_frame, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    mask_inv = cv2.bitwise_not(mask)
    frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    canvas_fg = cv2.bitwise_and(canvas_frame, canvas_frame, mask=mask)
    frame = cv2.add(frame_bg, canvas_fg)

    # Draw palette
    y1 = HEADER_HEIGHT
    y2 = y1 + 80
    for i, (col, name) in enumerate(PALETTE_COLS):
        x1 = i * PALETTE_BOX_W
        x2 = x1 + PALETTE_BOX_W
        if col == "CLEAR":
            cv2.rectangle(frame, (x1,y1), (x2,y2), (50,50,50), -1)
            cv2.putText(frame,"CLEAR",(x1+12,y1+50),cv2.FONT_HERSHEY_SIMPLEX,0.9,(200,200,200),2)
        else:
            cv2.rectangle(frame,(x1,y1),(x2,y2),col,-1)
            cv2.putText(frame,name,(x1+8,y2-8),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,0,0),1)

    return frame, canvas_frame, last_action
