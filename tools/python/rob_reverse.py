import argparse
import pathlib
from collections import Counter


FRAME_SIZE = 248
FILE_HEADER_SIZE = 16
FRAME_HEADER_SIZE = 8
BLOCK_SIZE = 8
CHANNEL_COUNT = 40
WORDS_PER_CHANNEL = 3
PAYLOAD_WORDS = CHANNEL_COUNT * WORDS_PER_CHANNEL
FILLER_TRIPLET = (0x5555, 0, 0)
ACTIVE_CHANNELS = 16
ACTIVE_PAYLOAD_BYTES = ACTIVE_CHANNELS * WORDS_PER_CHANNEL * 2


def u16le(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def chunks(seq, size):
    for index in range(0, len(seq), size):
        yield seq[index:index + size]


def block_hex_list(data):
    return [block.hex().upper() for block in chunks(data, BLOCK_SIZE)]


def parse_file(file_path):
    raw = pathlib.Path(file_path).read_bytes()
    if len(raw) < FILE_HEADER_SIZE:
        raise ValueError("file too small")
    magic = raw[:6].decode("ascii", errors="replace")
    frame_count = u16le(raw, 6)
    tag = raw[8:12].decode("ascii", errors="replace").rstrip("\x00")
    version = u16le(raw, 12)
    reserved = u16le(raw, 14)
    expected_length = FILE_HEADER_SIZE + frame_count * FRAME_SIZE
    frames = []
    for frame_index in range(frame_count):
        start = FILE_HEADER_SIZE + frame_index * FRAME_SIZE
        end = start + FRAME_SIZE
        frame = raw[start:end]
        if len(frame) != FRAME_SIZE:
            raise ValueError("truncated frame {}".format(frame_index))
        frames.append(frame)
    return {
        "path": str(file_path),
        "magic": magic,
        "frame_count": frame_count,
        "tag": tag,
        "version": version,
        "reserved": reserved,
        "length": len(raw),
        "expected_length": expected_length,
        "frames": frames,
    }


def parse_plain_frame(frame):
    duration = u16le(frame, 0)
    marker = u16le(frame, 2)
    reserved_a = u16le(frame, 4)
    reserved_b = u16le(frame, 6)
    payload = frame[FRAME_HEADER_SIZE:]
    channels = []
    for channel_index in range(CHANNEL_COUNT):
        channel_offset = channel_index * WORDS_PER_CHANNEL * 2
        channels.append(
            (
                u16le(payload, channel_offset),
                u16le(payload, channel_offset + 2),
                u16le(payload, channel_offset + 4),
            )
        )
    return {
        "duration": duration,
        "marker": marker,
        "reserved_a": reserved_a,
        "reserved_b": reserved_b,
        "channels": channels,
    }


def summarize_plain(parsed):
    print("file: {}".format(parsed["path"]))
    print("magic: {}".format(parsed["magic"]))
    print("tag: {}".format(parsed["tag"] or "<plain>"))
    print("frames: {}".format(parsed["frame_count"]))
    print("length: {} expected: {}".format(parsed["length"], parsed["expected_length"]))
    durations = []
    markers = Counter()
    non_zero_second = 0
    non_zero_third = 0
    active_channel_counts = []
    filler_channel_counts = []
    for frame in parsed["frames"]:
        info = parse_plain_frame(frame)
        durations.append(info["duration"])
        markers[info["marker"]] += 1
        active_channel_counts.append(sum(1 for triple in info["channels"] if triple != FILLER_TRIPLET))
        filler_channel_counts.append(sum(1 for triple in info["channels"] if triple == FILLER_TRIPLET))
        for first_word, second_word, third_word in info["channels"]:
            if second_word:
                non_zero_second += 1
            if third_word:
                non_zero_third += 1
    print("durations: {}".format(", ".join(str(value) for value in durations)))
    print("markers: {}".format(", ".join("0x{:04X} x{}".format(key, value) for key, value in sorted(markers.items()))))
    print("active_channels_per_frame: {}".format(", ".join(str(value) for value in active_channel_counts)))
    print("filler_channels_per_frame: {}".format(", ".join(str(value) for value in filler_channel_counts)))
    print("non_zero_second_words: {}".format(non_zero_second))
    print("non_zero_third_words: {}".format(non_zero_third))
    preview = parse_plain_frame(parsed["frames"][0])
    print("frame0 first 10 channels:")
    for index, triple in enumerate(preview["channels"][:10], start=1):
        print("  ch{:02d}: {}".format(index, triple))
    tail_start = next((index for index, triple in enumerate(preview["channels"], start=1) if triple == FILLER_TRIPLET), None)
    if tail_start is not None:
        print("frame0 filler_tail_starts_at_channel: {}".format(tail_start))


def as_words(data):
    return [u16le(data, index) for index in range(0, len(data), 2)]


def score_words(words):
    in_servo_range = sum(1 for word in words if 0 <= word <= 1023)
    in_extended_range = sum(1 for word in words if 0 <= word <= 2000)
    zeros = sum(1 for word in words if word == 0)
    return {
        "servo_ratio": in_servo_range / len(words),
        "extended_ratio": in_extended_range / len(words),
        "zero_ratio": zeros / len(words),
    }


def repeat_key_xor(data, key):
    return bytes(value ^ key[index % len(key)] for index, value in enumerate(data))


def swap_u16_bytes(data):
    swapped = bytearray(len(data))
    for index in range(0, len(data), 2):
        swapped[index] = data[index + 1]
        swapped[index + 1] = data[index]
    return bytes(swapped)


def rotate_left(data, amount):
    return bytes(((value << amount) & 0xFF) | (value >> (8 - amount)) for value in data)


def rotate_right(data, amount):
    return bytes((value >> amount) | ((value << (8 - amount)) & 0xFF) for value in data)


def candidate_transforms(frame):
    payload = frame[FRAME_HEADER_SIZE:]
    header = frame[:FRAME_HEADER_SIZE]
    candidates = {
        "identity": payload,
        "swap_u16": swap_u16_bytes(payload),
        "xor_frame_header": repeat_key_xor(payload, header),
        "xor_reversed_header": repeat_key_xor(payload, header[::-1]),
    }
    for amount in range(1, 8):
        candidates["rol{}".format(amount)] = rotate_left(payload, amount)
        candidates["ror{}".format(amount)] = rotate_right(payload, amount)
        candidates["xor_header_rol{}".format(amount)] = repeat_key_xor(payload, rotate_left(header, amount))
        candidates["xor_header_ror{}".format(amount)] = repeat_key_xor(payload, rotate_right(header, amount))
    return candidates


def summarize_eypt(parsed, top_n):
    print("file: {}".format(parsed["path"]))
    print("magic: {}".format(parsed["magic"]))
    print("tag: {}".format(parsed["tag"] or "<plain>"))
    print("frames: {}".format(parsed["frame_count"]))
    print("length: {} expected: {}".format(parsed["length"], parsed["expected_length"]))
    frame_headers = [frame[:FRAME_HEADER_SIZE].hex().upper() for frame in parsed["frames"]]
    payloads = [frame[FRAME_HEADER_SIZE:] for frame in parsed["frames"]]
    tail_reference = payloads[0][ACTIVE_PAYLOAD_BYTES:]
    tail_constant = all(payload[ACTIVE_PAYLOAD_BYTES:] == tail_reference for payload in payloads)
    tail_blocks = block_hex_list(tail_reference)
    print("frame_header_patterns:")
    for key, count in Counter(frame_headers).most_common():
        print("  {} x{}".format(key, count))
    print("active_payload_bytes_per_frame: {}".format(ACTIVE_PAYLOAD_BYTES))
    print("tail_payload_bytes_per_frame: {}".format(len(tail_reference)))
    print("tail_constant_across_frames: {}".format(tail_constant))
    print("tail_block_patterns:")
    for key, count in Counter(tail_blocks).most_common():
        print("  {} x{}".format(key, count))
    best = []
    for frame_index, frame in enumerate(parsed["frames"]):
        candidates = []
        for name, payload in candidate_transforms(frame).items():
            words = as_words(payload)
            scores = score_words(words)
            first_words = words[:10]
            candidates.append((scores["servo_ratio"], scores["extended_ratio"], -scores["zero_ratio"], name, first_words))
        candidates.sort(reverse=True)
        best.append((frame_index, candidates[:top_n]))
    for frame_index, rows in best:
        print("frame {} best candidates:".format(frame_index))
        for servo_ratio, extended_ratio, negative_zero_ratio, name, first_words in rows:
            print(
                "  {:20s} servo={:.3f} extended={:.3f} zero={:.3f} first10={}".format(
                    name,
                    servo_ratio,
                    extended_ratio,
                    -negative_zero_ratio,
                    first_words,
                )
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="path to .rob file")
    parser.add_argument("--top", type=int, default=5, help="number of candidate transforms to print for EYPT files")
    args = parser.parse_args()

    parsed = parse_file(args.file)
    if parsed["magic"] != "ACT-40":
        raise SystemExit("unsupported magic: {}".format(parsed["magic"]))
    if parsed["length"] != parsed["expected_length"]:
        print("warning: length mismatch")
    if parsed["tag"] == "EYPT":
        summarize_eypt(parsed, args.top)
    else:
        summarize_plain(parsed)


if __name__ == "__main__":
    main()