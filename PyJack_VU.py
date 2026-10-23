#! /usr/bin/env python3

import os
import jack
import numpy as np
import random as rnd
import pygame

cwd = os.path.dirname(os.path.realpath(__file__)) + "/"

WIN_DIMS = (512, 512)
CENTER = (WIN_DIMS[0] // 2, WIN_DIMS[1] // 2)

TL = (0, 0)
TR = (WIN_DIMS[0], 0)
BL = (0, WIN_DIMS[1])
BR = WIN_DIMS

LINE_WIDTH = 4

# 1. Initialize Pygame Mixer with standard settings
pygame.init()

SAMPLE_RATE = 48000
SAMPLE_SIZE = 1024

pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=SAMPLE_SIZE)
pygame.mixer.init()

# Create a Pygame window for visualization/controls
screen = pygame.display.set_mode(WIN_DIMS)
pygame.display.set_caption("Billy's Vu_Meter")
clock = pygame.time.Clock()

# 2. Setup the JACK Client
client = jack.Client("JackClient")

if client.status.server_started:
    print("JACK server was started automatically.")

# Register an input port
input_port_L = client.inports.register("input_L")
input_port_R = client.inports.register("input_R")

# client.connect("USB-BH209A Analog Stereo:monitor_FL", "JackClient:input_L")
# client.connect("USB-BH209A Analog Stereo:monitor_FR", "JackClient:input_R")

client.connect("Built-in Audio Analog Stereo:monitor_FL", "JackClient:input_L")
client.connect("Built-in Audio Analog Stereo:monitor_FR", "JackClient:input_R")

# Global variable to safely pass audio data from the JACK thread to the Pygame thread
latest_audio_buffer_L = np.zeros(SAMPLE_SIZE, dtype=np.float32)
latest_audio_buffer_R = np.zeros(SAMPLE_SIZE, dtype=np.float32)

cover_img1 = pygame.image.load(f"{cwd}VU_Meter.png").convert_alpha()
cover_img = pygame.transform.scale(cover_img1, (WIN_DIMS))

cover_rect = cover_img.get_rect()
cover_rect.topleft = (0, 0)

@client.set_process_callback
def process(frames):
    global latest_audio_buffer_L, latest_audio_buffer_R
    # Read raw float32 buffer directly from JACK [-1.0, 1.0]
    buffer_L = input_port_L.get_array()
    buffer_R = input_port_R.get_array()

    # Store a copy for our Pygame loop to read
    latest_audio_buffer_L = buffer_L.copy()
    latest_audio_buffer_R = buffer_R.copy()


def randColor():
    r = rnd.randint(4, 80)
    g = rnd.randint(4, 80)
    b = rnd.randint(4, 80)

    return (r, g, b)

# 3. Activate JACK Client
with client:
    # print(f"JACK Client Active. Ports: {client.get_ports()}")

    # Main Pygame Event Loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Grab a snapshot of the current audio data
        audio_data_L = latest_audio_buffer_L
        audio_data_R = latest_audio_buffer_R

        # Calculate Peak Volume (or perform FFT for visualizers)
        peak_L = np.max(np.abs(audio_data_L))
        meter_height_L = int(peak_L * WIN_DIMS[1])  # Map to window height

        peak_R = np.max(np.abs(audio_data_R))
        meter_height_R = int(peak_R * WIN_DIMS[1])  # Map to window height

        # --- Draw Pygame Graphics ---
        if meter_height_L > 0 or meter_height_R > 0:
            screen.fill(randColor())  # Random background
        else:
            screen.fill("black")

        # Draw a visual audio meter bar based on real-time JACK input

        rectx1 = (WIN_DIMS[0] // 3)
        rectx2 = (rectx1 * 2)

        rectx1 = rectx1 - 15
        rectx2 = rectx2 - 15

        # Left

        pygame.draw.rect(screen, (255, 0, 100), (rectx1, (BL[1] - meter_height_L), 40, meter_height_L))

        pygame.draw.line(screen, (255, 0, 100), BL, (rectx1, BR[1] - meter_height_L), LINE_WIDTH)
        pygame.draw.line(screen, (255, 0, 100), (CENTER[0], BR[1]), (rectx1, BR[1] - meter_height_L), LINE_WIDTH)

        # Right

        pygame.draw.rect(screen, (0, 255, 100), (rectx2, (BL[1] - meter_height_R), 40, meter_height_R))

        pygame.draw.line(screen, (0, 255, 100), BR, (rectx2, BR[1] - meter_height_R), LINE_WIDTH)
        pygame.draw.line(screen, (0, 255, 100), (CENTER[0], BL[1]), (rectx2, BR[1] - meter_height_R), LINE_WIDTH)

        screen.blit(cover_img, cover_rect)

        pygame.display.flip()
        clock.tick(24)

pygame.quit()
