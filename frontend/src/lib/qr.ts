/**
 * Reading a QR code on the visitor's own device. The picture and the camera never leave the
 * browser: only the text inside the code is sent on. Drawing a photo to a canvas also drops its
 * EXIF data (location, camera) before anything is read.
 */

const MAX_SIDE = 1200;

type Decoder = (data: Uint8ClampedArray, width: number, height: number) => { data: string } | null;

let decoder: Promise<Decoder> | null = null;

function loadDecoder(): Promise<Decoder> {
  decoder ??= import("jsqr").then((module) => module.default as Decoder);
  return decoder;
}

/** The text of the QR code in the picture, or null when there is none. */
export async function decodeImageData(image: ImageData): Promise<string | null> {
  const decode = await loadDecoder();
  return decode(image.data, image.width, image.height)?.data ?? null;
}

/** Draws a photo the visitor chose at a readable size and decodes it. */
export async function decodePhoto(file: File): Promise<string | null> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) return null;
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return decodeImageData(context.getImageData(0, 0, canvas.width, canvas.height));
}
