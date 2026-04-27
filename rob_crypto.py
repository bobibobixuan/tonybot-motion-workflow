import argparse
import pathlib


FILE_HEADER_SIZE = 16
TAG_OFFSET = 8
TAG_LENGTH = 4
BLOCK_SIZE = 8
DELTA = 0x9E3779B9
MASK32 = 0xFFFFFFFF
ROUND_COUNT = 32
SUM_INIT = (DELTA * ROUND_COUNT) & MASK32
ENCRYPT_ARRAY = (0x00003D09, 0x00000017, 0x00001CCD, 0x3B7B8488)
RAW_WORD_PREFIX = 4
RAW_WORD_SENTINEL = 0xFF00


def u32_from_le_bytes(data):
    return data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)


def u32_to_le_bytes(value):
    return bytes((value >> (index * 8)) & 0xFF for index in range(4))


def align_up(value, block_size):
    if value % block_size == 0:
        return value
    return value + block_size - (value % block_size)


def tea_encrypt_block(v0, v1, key=ENCRYPT_ARRAY):
    total = 0
    for _ in range(ROUND_COUNT):
        total = (total + DELTA) & MASK32
        v0 = (v0 + (((v1 << 4) + key[0]) ^ (v1 + total) ^ ((v1 >> 5) + key[1]))) & MASK32
        v1 = (v1 + (((v0 << 4) + key[2]) ^ (v0 + total) ^ ((v0 >> 5) + key[3]))) & MASK32
    return v0, v1


def tea_decrypt_block(v0, v1, key=ENCRYPT_ARRAY):
    total = SUM_INIT
    for _ in range(ROUND_COUNT):
        v1 = (v1 - (((v0 << 4) + key[2]) ^ (v0 + total) ^ ((v0 >> 5) + key[3]))) & MASK32
        v0 = (v0 - (((v1 << 4) + key[0]) ^ (v1 + total) ^ ((v1 >> 5) + key[1]))) & MASK32
        total = (total - DELTA) & MASK32
    return v0, v1


def transform_blocks(body, block_transform):
    if len(body) % BLOCK_SIZE != 0:
        raise ValueError("body length must be a multiple of 8 bytes")
    output = bytearray(len(body))
    for offset in range(0, len(body), BLOCK_SIZE):
        block = body[offset:offset + BLOCK_SIZE]
        left = u32_from_le_bytes(block[:4])
        right = u32_from_le_bytes(block[4:])
        left, right = block_transform(left, right)
        output[offset:offset + 4] = u32_to_le_bytes(left)
        output[offset + 4:offset + 8] = u32_to_le_bytes(right)
    return bytes(output)


def encrypt_body(body, key=ENCRYPT_ARRAY):
    return transform_blocks(body, lambda left, right: tea_encrypt_block(left, right, key))


def decrypt_body(body, key=ENCRYPT_ARRAY):
    return transform_blocks(body, lambda left, right: tea_decrypt_block(left, right, key))


def decrypt_action_bytes(data, key=ENCRYPT_ARRAY):
    if len(data) < FILE_HEADER_SIZE:
        raise ValueError("ACT-40 file is too small")
    header = bytearray(data[:FILE_HEADER_SIZE])
    header[TAG_OFFSET:TAG_OFFSET + TAG_LENGTH] = b"\x00" * TAG_LENGTH
    body = decrypt_body(data[FILE_HEADER_SIZE:], key=key)
    return bytes(header) + body


def encrypt_action_bytes(data, key=ENCRYPT_ARRAY):
    if len(data) < FILE_HEADER_SIZE:
        raise ValueError("ACT-40 file is too small")
    header = bytearray(data[:FILE_HEADER_SIZE])
    header[TAG_OFFSET:TAG_OFFSET + TAG_LENGTH] = b"EYPT"
    body = encrypt_body(data[FILE_HEADER_SIZE:], key=key)
    return bytes(header) + body


def get_buffer_length(words):
    index = 0
    while words[index] != RAW_WORD_SENTINEL:
        index += 1
    return index


def raw_words_to_buffer(words):
    buffer_length = get_buffer_length(words) - RAW_WORD_PREFIX
    padded_length = align_up(buffer_length, BLOCK_SIZE)
    output = bytearray(padded_length)
    for index in range(buffer_length):
        output[index] = words[index + RAW_WORD_PREFIX] & 0xFF
    return bytes(output)


def encrypt_words(words, key=ENCRYPT_ARRAY):
    return encrypt_body(raw_words_to_buffer(words), key=key)


def decrypt_words(words, key=ENCRYPT_ARRAY):
    return decrypt_body(raw_words_to_buffer(words), key=key)


def parse_key(text):
    values = [int(part, 0) for part in text.split(",") if part.strip()]
    if len(values) != 4:
        raise ValueError("key must contain exactly 4 comma-separated integers")
    return tuple(value & MASK32 for value in values)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    file_parser = subparsers.add_parser("decrypt-file")
    file_parser.add_argument("input")
    file_parser.add_argument("output")
    file_parser.add_argument("--key")

    file_parser = subparsers.add_parser("encrypt-file")
    file_parser.add_argument("input")
    file_parser.add_argument("output")
    file_parser.add_argument("--key")

    args = parser.parse_args()
    key = parse_key(args.key) if args.key else ENCRYPT_ARRAY
    source = pathlib.Path(args.input).read_bytes()

    if args.command == "decrypt-file":
        result = decrypt_action_bytes(source, key=key)
    else:
        result = encrypt_action_bytes(source, key=key)

    pathlib.Path(args.output).write_bytes(result)
    print("output={}".format(args.output))
    print("length={}".format(len(result)))


if __name__ == "__main__":
    main()