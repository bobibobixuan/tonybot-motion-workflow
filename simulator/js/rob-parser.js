const FRAME_SIZE = 248;
const FILE_HEADER_SIZE = 16;
const FRAME_HEADER_SIZE = 8;
const ACTIVE_CHANNELS = 16;
const WORDS_PER_CHANNEL = 3;
const TEA_DELTA = 0x9E3779B9;
const TEA_ROUNDS = 32;
const TEA_SUM_INIT = (TEA_DELTA * TEA_ROUNDS) >>> 0;
const ENCRYPT_ARRAY = [0x00003D09, 0x00000017, 0x00001CCD, 0x3B7B8488];

function u16le(data, offset) {
  return data[offset] | (data[offset + 1] << 8);
}

function u32le(data, offset) {
  return (
    data[offset] |
    (data[offset + 1] << 8) |
    (data[offset + 2] << 16) |
    (data[offset + 3] << 24)
  ) >>> 0;
}

function u32ToBytes(value) {
  const bytes = new Uint8Array(4);
  bytes[0] = value & 0xFF;
  bytes[1] = (value >>> 8) & 0xFF;
  bytes[2] = (value >>> 16) & 0xFF;
  bytes[3] = (value >>> 24) & 0xFF;
  return bytes;
}

function teaDecryptBlock(v0, v1, key) {
  let sum = TEA_SUM_INIT;
  for (let i = 0; i < TEA_ROUNDS; i++) {
    v1 = (v1 - (((v0 << 4) + key[2]) ^ (v0 + sum) ^ ((v0 >>> 5) + key[3]))) >>> 0;
    v0 = (v0 - (((v1 << 4) + key[0]) ^ (v1 + sum) ^ ((v1 >>> 5) + key[1]))) >>> 0;
    sum = (sum - TEA_DELTA) >>> 0;
  }
  return [v0, v1];
}

function teaDecryptBody(body, key) {
  if (body.length % 8 !== 0) {
    throw new Error("TEA body length must be multiple of 8");
  }

  const output = new Uint8Array(body.length);
  for (let offset = 0; offset < body.length; offset += 8) {
    const left = u32le(body, offset);
    const right = u32le(body, offset + 4);
    const [decryptedLeft, decryptedRight] = teaDecryptBlock(left, right, key);
    output.set(u32ToBytes(decryptedLeft), offset);
    output.set(u32ToBytes(decryptedRight), offset + 4);
  }
  return output;
}

export function parseRobFile(buffer) {
  const data = new Uint8Array(buffer);
  if (data.length < FILE_HEADER_SIZE) throw new Error("文件太小");

  const magic = String.fromCharCode(...data.slice(0, 6));
  if (magic !== "ACT-40") throw new Error(`不支持的文件格式: ${magic}`);

  const frameCount = u16le(data, 6);
  const tagBytes = data.slice(8, 12);
  const tag = String.fromCharCode(...tagBytes).replace(/\0/g, "");
  const rawFrames =
    tag === "EYPT"
      ? teaDecryptBody(data.slice(FILE_HEADER_SIZE), ENCRYPT_ARRAY)
      : data.slice(FILE_HEADER_SIZE);
  const expectedLength = frameCount * FRAME_SIZE;
  if (rawFrames.length < expectedLength) throw new Error("帧数据不完整");

  const frames = [];
  for (let i = 0; i < frameCount; i++) {
    const start = i * FRAME_SIZE;
    const frame = rawFrames.slice(start, start + FRAME_SIZE);
    const duration = u16le(frame, 0);
    const pose = [];
    for (let channel = 0; channel < ACTIVE_CHANNELS; channel++) {
      pose.push(u16le(frame, FRAME_HEADER_SIZE + channel * WORDS_PER_CHANNEL * 2));
    }
    frames.push({ duration, pose, raw: frame });
  }

  return { magic, tag, frameCount, frames };
}
