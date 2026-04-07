import boto3
import json
import time
import random
import math

# AWS Connection - UPDATE THIS TO MATCH YOUR TERRAFORM OUTPUT
STREAM_NAME = "f1-pulse-dev-stream" 
kinesis = boto3.client('kinesis', region_name='us-east-1')

# --- THE PHYSICS ENGINE ---
TRACK_CENTER_X, TRACK_CENTER_Y = 500, 300
TRACK_RADIUS_X, TRACK_RADIUS_Y = 400, 150

drivers = {
    "HAM": {"progress_angle": 0.0, "base_speed": 260},
    "BOT": {"progress_angle": -0.3, "base_speed": 255}
}

def generate_telemetry(driver_id, state):
    # 1. Base speed + variance
    speed = state['base_speed'] + random.uniform(-10, 10)
    
    # 2. Corner Logic (Braking zones)
    normalized_angle = state['progress_angle'] % (2 * math.pi)
    is_in_corner = False
    if (1.2 < normalized_angle < 1.9) or (4.3 < normalized_angle < 5.0):
        speed = random.uniform(110, 150) # Slow down for the turn
        is_in_corner = True
        
    # 3. Physics Updates
    rpm = (speed / 350) * 12000 + random.uniform(-200, 200)
    throttle = random.uniform(85, 100) if not is_in_corner else random.uniform(10, 30)
    
    # Move along the track
    state['progress_angle'] += (speed * 0.0005)
    pos_x = TRACK_CENTER_X + TRACK_RADIUS_X * math.cos(state['progress_angle'])
    pos_y = TRACK_CENTER_Y + TRACK_RADIUS_Y * math.sin(state['progress_angle'])
    
    # 4. SENSITIVE TRACTION LOSS 
    # Triggered when accelerating OUT of a corner
    traction_loss = 0
    if is_in_corner and random.random() > 0.4:
        traction_loss = 1
        # Simulate a loss of traction by reducing speed
        speed *= 0.8
    return {
        "Driver": driver_id,
        "Timestamp": int(time.time() * 1000),
        "Speed": round(speed, 1),
        "RPM": round(rpm, 0),
        "Throttle": round(throttle, 0),
        "TractionLoss": traction_loss,
        "Position_X": round(pos_x, 2),
        "Position_Y": round(pos_y, 2)
    }

print(f"Physics Engine Active: Streaming to {STREAM_NAME}...")
while True:
    for driver in ["HAM", "BOT"]:
        try:
            payload = generate_telemetry(driver, drivers[driver])
            kinesis.put_record(StreamName=STREAM_NAME, Data=json.dumps(payload), PartitionKey=driver)
        except Exception as e:
            print(f"Error: {e}")
    time.sleep(1)