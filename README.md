# Raspberry Pi Pico Audio Player with MAX98357A

A complete audio playback system for Raspberry Pi Pico using the MAX98357A I2S amplifier, supporting WAV and MP3 files from SD card storage.

![Setup](pic1.png)

## Table of Contents
- [Hardware Requirements](#hardware-requirements)
- [Our Journey: Troubleshooting Story](#our-journey-troubleshooting-story)
- [Final Working Setup](#final-working-setup)
- [Wiring Guide](#wiring-guide)
- [Software Setup](#software-setup)
- [Usage](#usage)
- [Features](#features)

## Hardware Requirements

- Raspberry Pi Pico
- MAX98357A I2S Class D Amplifier Module
- MicroSD Card Module (SPI)
- Speaker (4Ω or 8Ω)
- 100µF capacitor (for testing PWM audio)
- MicroSD card (FAT32 formatted)
- Jumper wires
- USB cable for power/programming

![Hardware Components](pic2.png)

## Our Journey: Troubleshooting Story

### Initial Attempts with MicroPython

**Problem 1: No Sound from MAX98357A**

We started with MicroPython, attempting to generate I2S signals using the Pico's PIO (Programmable I/O) state machines. Despite correct wiring:
- GPIO 13 → DIN
- GPIO 14 → BCLK
- GPIO 15 → LRC
- Power and ground connected
- Speaker properly wired to OUT+ and OUT-

**Result:** Complete silence from three different MAX98357A boards.

**What we tried:**
1. Verified all pin connections with multimeter
2. Tested speaker with 1.5V battery (confirmed working)
3. Checked power delivery (5V confirmed on VIN)
4. Tried different GAIN settings (GND, floating, VIN)
5. Manually toggled pins to generate noise
6. Multiple PIO I2S implementations
7. Different sample rates and bit depths

**Mistake discovered:** Initially tested with wrong GPIO pins in code (9, 10, 11) while hardware was on (13, 14, 15). After correction, still no sound.

### Testing Individual Components

**PWM Audio Workaround**

To verify the Pico and speaker were functional, we implemented direct PWM audio:

```python
from machine import Pin, PWM
audio = PWM(Pin(13))
audio.freq(440)
audio.duty_u16(32768)
```

**Wiring:** GPIO 13 → 100µF capacitor → Speaker → GND

**Result:** Success! This proved:
- ✅ Pico GPIO pins working
- ✅ Speaker functional
- ✅ Basic audio generation possible
- ❌ MAX98357A or I2S implementation was the issue

![PWM Test Setup](pic3.png)

### The INMP441 Detour

While waiting for a potential MAX98357A replacement, we tested an INMP441 I2S MEMS microphone with the same pins.

**Result:** All zeros - no data received. This strongly suggested the MicroPython PIO I2S implementation wasn't generating proper I2S timing signals.

### The Solution: CircuitPython

**Breakthrough:** Switched from MicroPython to CircuitPython, which has native hardware I2S support via `audiobusio.I2SOut`.

```python
import board
import audiobusio

audio = audiobusio.I2SOut(
    bit_clock=board.GP14,
    word_select=board.GP15,
    data=board.GP13
)
```

**Result:** Immediate success! The MAX98357A worked perfectly on first try.

### Key Lessons Learned

1. **MicroPython's PIO I2S is unreliable** - While theoretically possible to bit-bang I2S with PIO, getting the timing perfect is extremely difficult
2. **CircuitPython has superior audio support** - Built-in hardware I2S libraries that actually work
3. **Component testing is crucial** - The PWM test proved our hardware was fine before we spent more time on software
4. **The boards weren't dead** - All three MAX98357A boards worked perfectly once we used proper I2S signals

## Final Working Setup

### System Architecture

```
┌─────────────────┐
│ Raspberry Pi    │
│ Pico            │
│ (CircuitPython) │
└────┬──┬──┬──────┘
     │  │  │
     │  │  └─ GPIO 13 (DIN) ────┐
     │  └──── GPIO 14 (BCLK) ───┤
     └─────── GPIO 15 (LRC) ─────┤
                                 │
                         ┌───────▼────────┐
                         │   MAX98357A    │
                         │  I2S Amplifier │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │    Speaker     │
                         │   4Ω or 8Ω     │
                         └────────────────┘

┌──────────────┐
│  MicroSD     │
│  Card Module ├─ SPI ─ GPIO 16-19
│  (Optional)  │
└──────────────┘
```

## Wiring Guide

### MAX98357A Connections

| MAX98357A Pin | Raspberry Pi Pico | Notes |
|---------------|-------------------|-------|
| LRC (Word Select) | GPIO 15 (Pin 20) | I2S left/right clock |
| BCLK (Bit Clock) | GPIO 14 (Pin 19) | I2S bit clock |
| DIN (Data In) | GPIO 13 (Pin 17) | I2S data signal |
| GAIN | GND or VIN | GND=9dB, Float=12dB, VIN=15dB |
| SD (Shutdown) | Not connected | Leave floating (enabled) |
| VIN | Pin 40 (VBUS/5V) | Power input |
| GND | Pin 38 (GND) | Ground |
| OUT+ | Speaker + | Amplifier output |
| OUT- | Speaker - | Amplifier output |

![MAX98357A Wiring](pic4.png)

### SD Card Module Connections (Optional)

| SD Module Pin | Raspberry Pi Pico |
|---------------|-------------------|
| CS | GPIO 17 (Pin 22) |
| SCK | GPIO 18 (Pin 24) |
| MOSI | GPIO 19 (Pin 25) |
| MISO | GPIO 16 (Pin 21) |
| VCC | 3.3V (Pin 36) |
| GND | GND (Pin 38) |

![Complete Wiring](pic5.png)

## Software Setup

### 1. Install CircuitPython

1. Download the latest CircuitPython `.uf2` file for Raspberry Pi Pico from [circuitpython.org](https://circuitpython.org/board/raspberry_pi_pico/)
2. Hold the BOOTSEL button on your Pico while plugging in USB
3. Drag the `.uf2` file to the RPI-RP2 drive that appears
4. Pico will reboot as CIRCUITPY drive

### 2. Test Audio Output

Create `code.py` on the CIRCUITPY drive:

```python
import board
import audiobusio
import audiocore
import array
import math

# Initialize I2S
audio = audiobusio.I2SOut(
    bit_clock=board.GP14,
    word_select=board.GP15,
    data=board.GP13
)

# Generate test tone
sample_rate = 16000
length = sample_rate // 440  # 440 Hz
samples = array.array("H", [0] * length)

for i in range(length):
    samples[i] = int((1 + math.sin(math.pi * 2 * i / length)) * 32767)

# Play tone
sample = audiocore.RawSample(samples, sample_rate=sample_rate)
audio.play(sample, loop=True)

import time
time.sleep(3)
audio.stop()
```

**Expected result:** You should hear a 440Hz tone for 3 seconds.

### 3. Install Complete Music Player

Copy the provided `code.py` from the repository to your CIRCUITPY drive.

## Usage

### Playing Audio Files

**Without SD Card:**
1. Copy `.wav` or `.mp3` files directly to CIRCUITPY drive
2. The player will automatically detect and play them

**With SD Card:**
1. Format SD card as FAT32
2. Copy audio files to SD card root directory
3. Insert into SD card module
4. Player will automatically mount and play files

### Interactive Functions

```python
# Play all files in order
play_all()

# Shuffle mode
play_all(shuffle=True)

# Repeat playlist
play_all(repeat=True)

# Play specific track
play_track(3)

# List all tracks
list_tracks()

# Play single file
play_file('/sd/song.mp3')

# Play musical note
play_note('A4', 0.5)

# Play custom tone
play_tone(440, 1.0)
```

## Features

✅ **Plays WAV files** - Any sample rate, mono or stereo, 16-bit
✅ **Plays MP3 files** - Hardware-accelerated MP3 decoding
✅ **SD card support** - Store hundreds of songs
✅ **Shuffle and repeat** - Built-in playlist management
✅ **High quality audio** - I2S digital audio with Class D amplifier
✅ **Simple API** - Easy-to-use functions for playback control
✅ **Auto-detection** - Automatically finds and plays audio files
✅ **Progress indicators** - Real-time playback status

## Troubleshooting

### No Sound

1. **Check volume** - Adjust GAIN pin (connect to VIN for maximum volume)
2. **Verify wiring** - Use multimeter to confirm connections
3. **Test speaker** - Touch speaker wires to 1.5V battery briefly
4. **Check SD pin** - Must be floating or at 3.3V, NOT ground
5. **Verify I2S signals** - Run test tone code first

### SD Card Not Detected

1. **Check format** - Must be FAT32
2. **Verify wiring** - Especially CS, SCK, MOSI, MISO
3. **Check power** - SD module needs 3.3V, not 5V
4. **Try different card** - Some cards are incompatible

### Poor Audio Quality

1. **Check speaker impedance** - Use 4Ω or 8Ω speaker
2. **Increase GAIN** - Connect GAIN to VIN
3. **Check power supply** - Ensure stable 5V from USB
4. **Use higher quality files** - 16-bit, 44.1kHz recommended

## Performance Notes

- **WAV files:** No CPU overhead, direct streaming
- **MP3 files:** Real-time decoding, works great on Pico
- **Sample rates:** Supports 8kHz - 48kHz
- **File size limits:** Limited only by SD card size
- **Playback quality:** Excellent with proper speaker and power

## Alternative: PWM Audio (No Amplifier)

If you want to test without the MAX98357A:

**Wiring:** GPIO 13 → 100µF capacitor → Speaker → GND

**Code:**
```python
from machine import Pin, PWM
import time

audio = PWM(Pin(13))
audio.freq(440)
audio.duty_u16(32768)
time.sleep(1)
audio.duty_u16(0)
```

**Note:** Very quiet, lower quality, but useful for testing.

## Future Enhancements

- [ ] Button controls for play/pause/next/previous
- [ ] Volume control potentiometer
- [ ] OLED display showing track info
- [ ] Bluetooth audio streaming
- [ ] Web interface for remote control
- [ ] Playlist files (M3U support)
- [ ] Equalizer controls

## Credits

Developed through extensive troubleshooting and testing with the Raspberry Pi Pico and MAX98357A amplifier. Special thanks to the CircuitPython team for excellent I2S support.

## License

MIT License - Feel free to use and modify for your projects!

---

**Note:** This project demonstrates the importance of choosing the right software framework. While MicroPython is excellent for many applications, CircuitPython's superior audio library support makes it the clear choice for audio projects on the Raspberry Pi Pico.
