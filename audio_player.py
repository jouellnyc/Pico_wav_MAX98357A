
import board
import busio
import sdcardio
import storage
import audiobusio
import audiocore
import audiomp3
import time
import os

print("=" * 50)
print("Pico SD Card Music Player")
print("=" * 50)

# ============= SD CARD SETUP =============
print("\n[1/3] Initializing SD card...")

try:
    # Initialize SPI for SD card
    spi = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)
    cs = board.GP17

    # Mount SD card
    sd = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")

    print("✓ SD card mounted successfully!")

except Exception as e:
    print(f"✗ SD card error: {e}")
    print("\nWiring check:")
    print("  CS   → GP17 (Pin 22)")
    print("  SCK  → GP18 (Pin 24)")
    print("  MOSI → GP19 (Pin 25)")
    print("  MISO → GP16 (Pin 21)")
    print("  VCC  → 3.3V (Pin 36)")
    print("  GND  → GND")
    raise

# ============= AUDIO SETUP =============
print("\n[2/3] Initializing audio...")

audio = audiobusio.I2SOut(
    bit_clock=board.GP14,    # BCLK
    word_select=board.GP15,  # LRC
    data=board.GP13          # DIN
)

print("✓ Audio initialized!")

# ============= MUSIC LIBRARY =============

def get_audio_files(directory="/sd"):
    """Get all audio files from SD card"""
    audio_files = []

    try:
        for filename in os.listdir(directory):
            filepath = f"{directory}/{filename}"

            # Check if it's an audio file
            if filename.lower().endswith(('.wav', '.mp3')):
                audio_files.append(filepath)

        # Sort alphabetically
        audio_files.sort()

    except Exception as e:
        print(f"Error reading directory: {e}")

    return audio_files

def play_file(filepath):
    """Play a single audio file"""
    try:
        filename = filepath.split('/')[-1]
        print(f"\n♪ Playing: {filename}")

        is_mp3 = filepath.lower().endswith('.mp3')

        with open(filepath, "rb") as f:
            if is_mp3:
                sound = audiomp3.MP3Decoder(f)
                print(f"  Format: MP3, {sound.sample_rate}Hz, {sound.channel_count}ch")
            else:
                sound = audiocore.WaveFile(f)
                print(f"  Format: WAV, {sound.sample_rate}Hz, {sound.channel_count}ch, {sound.bits_per_sample}bit")

            audio.play(sound)

            # Wait for playback with progress indicator
            start_time = time.monotonic()
            while audio.playing:
                elapsed = int(time.monotonic() - start_time)
                print(f"  Playing... {elapsed}s", end='\r')
                time.sleep(0.1)

            print(f"  ✓ Finished ({elapsed}s)                ")
            return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def play_all(shuffle=False, repeat=False):
    """Play all audio files on SD card"""
    files = get_audio_files()

    if not files:
        print("\n✗ No audio files found on SD card!")
        print("  Supported formats: .wav, .mp3")
        return

    print(f"\n[3/3] Found {len(files)} audio file(s)")
    print("-" * 50)

    for i, filepath in enumerate(files, 1):
        filename = filepath.split('/')[-1]
        print(f"{i}. {filename}")

    print("-" * 50)

    if shuffle:
        import random
        random.shuffle(files)
        print("🔀 Shuffle mode enabled")

    if repeat:
        print("🔁 Repeat mode enabled")

    # Play all files
    while True:
        for filepath in files:
            play_file(filepath)
            time.sleep(0.5)  # Pause between songs

        if not repeat:
            break

        print("\n🔁 Repeating playlist...")

def play_track(track_number):
    """Play a specific track by number"""
    files = get_audio_files()

    if not files:
        print("No audio files found!")
        return

    if 1 <= track_number <= len(files):
        play_file(files[track_number - 1])
    else:
        print(f"Track {track_number} not found. Available: 1-{len(files)}")

def list_tracks():
    """List all available tracks"""
    files = get_audio_files()

    if not files:
        print("No audio files found on SD card")
        return

    print(f"\nPlaylist ({len(files)} tracks):")
    print("-" * 50)
    for i, filepath in enumerate(files, 1):
        filename = filepath.split('/')[-1]
        print(f"  {i}. {filename}")
    print("-" * 50)

# ============= MAIN PROGRAM =============

# List all tracks
list_tracks()

# Auto-play mode
print("\n🎵 Starting playback...")
print("(Plays all files in order)\n")

try:
    play_all(shuffle=False, repeat=False)
    print("\n✓ Playback complete!")

except KeyboardInterrupt:
    print("\n\n⏹ Stopped by user")
    audio.stop()

print("\n" + "=" * 50)
print("Music Player Functions:")
print("  play_all()              - Play all files")
print("  play_all(shuffle=True)  - Play all shuffled")
print("  play_all(repeat=True)   - Repeat playlist")
print("  play_track(3)           - Play track #3")
print("  list_tracks()           - List all tracks")
print("  play_file('/sd/song.mp3') - Play specific file")
print("=" * 50)


