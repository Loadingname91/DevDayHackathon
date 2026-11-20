// Photos and files for Clair (spec/clair-agent.md §3, FR-C3, FR-C6, FR-C12).
// The device does the work the server should never have to: it decodes the picture, scales it to 1568 px on the long side,
// re-encodes it as JPEG (which also drops EXIF and GPS), and uploads the file straight into Storage. `/clair/turns` then
// carries only the Storage paths (clair-agent.md §2). Nothing here touches the DOM beyond a canvas.
import { isMocked } from '../api/client';
import { authConfigured, supabase } from './auth';

export type AttKind = 'image' | 'pdf' | 'text';
export type AttState = 'preparing' | 'ready' | 'uploading' | 'uploaded' | 'error';
/** What went wrong with an upload, so the tile can say it and Retry can be offered. */
export type UploadErrorKind = 'bucket_missing' | 'denied' | 'network';

export type Attachment = {
  id: string;
  kind: AttKind;
  name: string;
  mime: string;
  size: number;
  /** an object URL of the prepared picture (a downscaled JPEG, never the 12 MP original); revoked by the hook */
  preview?: string;
  state: AttState;
  error?: string;
  /** an upload failure can be retried; a type or size refusal cannot (remove it) */
  retry?: boolean;
  /** the Storage path once uploaded: `{workspace_id}/{uuid}.{ext}` */
  path?: string;
  /** what is uploaded: the downscaled JPEG, or the file as picked */
  blob?: Blob;
  /** the prepared picture's size in pixels (images only) */
  w?: number;
  h?: number;
  /** milliseconds `prepareImage` took (images only; shown nowhere, read by the harness) */
  prep?: number;
};

/** What a sent turn keeps of an attachment: enough to draw its tile and its thumbnail. Never the bytes; the archive keeps only the name. */
export type Thumb = { kind: AttKind; name: string; url?: string };
/** Frees what `useAttachments().take()` handed over. */
export const revokeThumbs = (t: readonly Thumb[]) => t.forEach((x) => x.url && URL.revokeObjectURL(x.url));
/** Local ids never use crypto.randomUUID: the voice checks count its calls to prove one request per turn. */
export const uid = () => `a${Date.now().toString(36)}${Math.random().toString(36).slice(2, 9)}`;

// ---- limits (clair-agent.md §3, §13; backend.md §11 row 36)
export const MAX_ATTACHMENTS = 5;
export const LONG_SIDE = 1568;
export const MAX_IMAGE_IN = 25 * 1024 * 1024; // before the downscale: a 12 MP photo is 3 to 8 MB, a panorama can be more
export const MAX_IMAGE_OUT = 5 * 1024 * 1024; // the server rejects an image over 5 MB (backend.md §11 row 36)
export const MAX_PDF = 10 * 1024 * 1024;
export const MAX_TEXT = 1024 * 1024;
export const JPEG_QUALITY = 0.85;
/** The backend needs non-empty text on a turn; an attachment alone sends this (reported as a contract note). */
export const ATTACH_ONLY_TEXT = 'Read this and tell me what you find.';

// ---- words (design/DESIGN.md §8: sentence case, no pronoun for Clair)
export const CANT_READ = "Can't read this yet. A photo or PDF works.";
export const SIXTH = 'Up to 5 per message';
export const UPLOAD_FAILED = "Couldn't upload. Try again";
const BUCKET_MISSING = "Uploads aren't turned on for this server yet.";

const EXT = (name: string) => (name.match(/\.([a-z0-9]+)$/i)?.[1] ?? '').toLowerCase();
const IMG_EXT = new Set(['jpg', 'jpeg', 'png', 'webp', 'gif', 'heic', 'heif', 'avif', 'bmp']);
const TEXT_EXT: Record<string, string> = { csv: 'text/csv', txt: 'text/plain', ics: 'text/calendar', md: 'text/markdown' };

export type Class = { kind: AttKind; mime: string } | { error: string };

/** Which kind of attachment a file is, by its type and then its name (a phone or Windows often leaves `type` empty or wrong). */
export function classify(file: Pick<File, 'name' | 'type'>): Class {
  const type = (file.type || '').toLowerCase(), ext = EXT(file.name);
  if (type === 'image/svg+xml' || ext === 'svg') return { error: CANT_READ };
  if (type.startsWith('image/') || IMG_EXT.has(ext)) return { kind: 'image', mime: type.startsWith('image/') ? type : 'image/jpeg' };
  if (type === 'application/pdf' || ext === 'pdf') return { kind: 'pdf', mime: 'application/pdf' };
  if (type === 'text/plain' || type === 'text/csv' || type === 'text/calendar' || type === 'text/markdown' || ext in TEXT_EXT) {
    return { kind: 'text', mime: TEXT_EXT[ext] ?? (type || 'text/plain') };
  }
  return { error: CANT_READ };
}

export type Verdict =
  | { file: File; kind: AttKind; mime: string; error?: undefined; tile: true }
  /** `tile`: a refused file still gets a tile saying why (a type or a size); the sixth gets none, only the notice */
  | { file: File; kind?: undefined; mime?: undefined; error: string; tile: boolean };

/**
 * What to do with `add`, given what is already attached: at most 5 in all (the sixth is refused, no tile), PDF up to 10 MB,
 * text up to 1 MB, a photo up to 25 MB before it is scaled down. Order is kept. Pure: no state, no DOM.
 */
export function validate(list: readonly Pick<Attachment, 'id'>[], add: readonly File[]): Verdict[] {
  let room = MAX_ATTACHMENTS - list.length;
  return add.map((file): Verdict => {
    if (room <= 0) return { file, error: SIXTH, tile: false };
    room--; // a refused type or size still shows its tile, so it takes a place until removed
    const c = classify(file);
    if ('error' in c) return { file, error: c.error, tile: true };
    const cap = c.kind === 'image' ? MAX_IMAGE_IN : c.kind === 'pdf' ? MAX_PDF : MAX_TEXT;
    if (file.size > cap) {
      const what = c.kind === 'image' ? 'photo' : c.kind === 'pdf' ? 'PDF' : 'file';
      return { file, error: `That ${what} is over ${cap / 1024 / 1024} MB.`, tile: true };
    }
    return { file, kind: c.kind, mime: c.mime, tile: true };
  });
}

// ---- the picture

type Decoded = { src: CanvasImageSource; w: number; h: number; close: () => void };

async function decode(file: Blob): Promise<Decoded> {
  // createImageBitmap applies the EXIF rotation when asked; where the options bag throws (old Safari) or the format is not
  // decodable that way (HEIC in Safari), an <img> element still renders it, and browsers rotate that by the EXIF too.
  if (typeof createImageBitmap === 'function') {
    for (const opts of [{ imageOrientation: 'from-image' } as ImageBitmapOptions, undefined]) {
      try {
        const bmp = opts ? await createImageBitmap(file, opts) : await createImageBitmap(file);
        return { src: bmp, w: bmp.width, h: bmp.height, close: () => bmp.close() };
      } catch { /* try the next way */ }
    }
  }
  const url = URL.createObjectURL(file);
  try {
    const img = new Image();
    img.decoding = 'async';
    img.src = url;
    await img.decode();
    return { src: img, w: img.naturalWidth, h: img.naturalHeight, close: () => { img.src = ''; } };
  } finally {
    URL.revokeObjectURL(url);
  }
}

const toBlob = (c: HTMLCanvasElement, q: number) =>
  new Promise<Blob | null>((ok) => c.toBlob(ok, 'image/jpeg', q));

export type Prepared = { blob: Blob; w: number; h: number; ms: number };

/**
 * Decodes the file, scales it so its long side is at most 1568 px (never up), and encodes a JPEG at 0.85. The bitmap and the
 * canvas are freed as soon as the blob exists. A picture that cannot be decoded throws `Error('unreadable')`.
 */
export async function prepareImage(file: Blob, signal?: AbortSignal): Promise<Prepared> {
  const t0 = performance.now();
  const gone = () => { if (signal?.aborted) throw new DOMException('aborted', 'AbortError'); };
  let d: Decoded;
  try { d = await decode(file); } catch { throw new Error('unreadable'); }
  try {
    gone();
    if (!d.w || !d.h) throw new Error('unreadable');
    const k = Math.min(1, LONG_SIDE / Math.max(d.w, d.h));
    const w = Math.max(1, Math.round(d.w * k)), h = Math.max(1, Math.round(d.h * k));
    const canvas = document.createElement('canvas');
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('unreadable');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h); // a transparent PNG would turn black as a JPEG
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(d.src, 0, 0, w, h);
    d.close();
    let blob: Blob | null = null;
    for (const q of [JPEG_QUALITY, 0.7, 0.55]) { // a picture over 5 MB at 1568 px is a rare noise-heavy one: step the quality down
      blob = await toBlob(canvas, q);
      gone();
      if (blob && blob.size <= MAX_IMAGE_OUT) break;
    }
    canvas.width = canvas.height = 0; // free the pixels now rather than at the next GC
    if (!blob || blob.size > MAX_IMAGE_OUT) throw new Error('unreadable');
    return { blob, w, h, ms: Math.round(performance.now() - t0) };
  } finally {
    d.close();
  }
}

// ---- the upload

export class UploadError extends Error {
  constructor(public kind: UploadErrorKind, message?: string) { super(message ?? kind); }
}

/** supabase-js's StorageError carries `message` and sometimes `statusCode`; a thrown fetch has neither. */
export function mapStorageError(err: unknown): UploadError {
  const e = err as { message?: string; statusCode?: string | number; status?: number } | null;
  const msg = String(e?.message ?? ''), code = String(e?.statusCode ?? e?.status ?? '');
  if (/bucket not found/i.test(msg) || code === '404') return new UploadError('bucket_missing', msg);
  if (/row-level security|unauthori[sz]ed|forbidden|not allowed|jwt|invalid.*token/i.test(msg) || code === '401' || code === '403') return new UploadError('denied', msg);
  return new UploadError('network', msg);
}

const EXT_OF: Record<AttKind, (a: Attachment) => string> = {
  image: () => 'jpg',
  pdf: () => 'pdf',
  text: (a) => (EXT(a.name) in TEXT_EXT ? EXT(a.name) : 'txt'),
};
const CONTENT_TYPE = (a: Attachment) => (a.kind === 'image' ? 'image/jpeg' : a.kind === 'pdf' ? 'application/pdf' : TEXT_EXT[EXT(a.name)] ?? 'text/plain');

/** Real Storage only when the app talks to the live API for turns; otherwise nothing leaves the device. */
const liveUploads = () => authConfigured && !isMocked('/clair/turns');

/**
 * Mock-mode switches for the demo menu and the tests (mock uploads are otherwise instant and never fail):
 * `?mock=upload-fail` fails every upload with `network`, `?mock=upload-fail-once` fails the first one, `?mock=upload-slow` takes 2 s.
 * Set `mockUpload.fault` to '' and Retry goes through.
 */
export const mockUpload: { fault: '' | UploadErrorKind; once: boolean; delay: number } = { fault: '', once: false, delay: 0 };
try {
  const m = new URLSearchParams(location.search).get('mock');
  if (m === 'upload-fail') mockUpload.fault = 'network';
  if (m === 'upload-fail-once') { mockUpload.fault = 'network'; mockUpload.once = true; }
  if (m === 'upload-slow') mockUpload.delay = 2000;
} catch { /* no location: a test runner */ }

/** The mock's stand-in path keeps the file's name, so the scripted run can tell a syllabus from a bank file (mocks/scenarios.ts). */
export const mockPath = (a: Pick<Attachment, 'name' | 'kind'>, ext: string) =>
  `mock/${uid()}-${a.name.toLowerCase().replace(/\.[a-z0-9]+$/, '').replace(/[^a-z0-9]+/g, '-').slice(0, 40)}.${ext}`;

/**
 * Uploads the prepared file to the private bucket `clair-uploads` at `{workspace_id}/{uuid}.{ext}` (Storage RLS checks the
 * folder; the path is never reused, so `upsert` is off) and returns the path. In mock mode it resolves at once to a fake path.
 * Throws `UploadError` with a kind.
 */
export async function upload(att: Attachment, workspaceId: string | undefined): Promise<string> {
  const ext = EXT_OF[att.kind](att);
  if (!liveUploads()) {
    if (mockUpload.delay) await new Promise((r) => setTimeout(r, mockUpload.delay));
    if (mockUpload.fault) { const kind = mockUpload.fault; if (mockUpload.once) mockUpload.fault = ''; throw new UploadError(kind); }
    return mockPath(att, ext);
  }
  if (!workspaceId) throw new UploadError('denied', 'no workspace');
  const body = att.blob;
  if (!body) throw new UploadError('network', 'nothing to upload');
  const path = `${workspaceId}/${crypto.randomUUID()}.${ext}`;
  try {
    const { error } = await (await supabase()).storage.from('clair-uploads').upload(path, body, { contentType: CONTENT_TYPE(att), upsert: false });
    if (error) throw error;
  } catch (e) {
    throw e instanceof UploadError ? e : mapStorageError(e);
  }
  return path;
}

export const uploadMessage = (e: UploadError) => (e.kind === 'bucket_missing' ? BUCKET_MISSING : UPLOAD_FAILED);

/** The turn's attachment fields: uploaded pictures in `images`, PDFs and text files in `files`. Errors and unfinished ones are left out. */
export function toRequest(list: readonly Attachment[]): { images: string[]; files: string[] } {
  const done = list.filter((a) => a.state === 'uploaded' && a.path);
  return {
    images: done.filter((a) => a.kind === 'image').map((a) => a.path!),
    files: done.filter((a) => a.kind !== 'image').map((a) => a.path!),
  };
}

export const sizeText = (n: number) => (n < 1024 * 1024 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / 1024 / 1024).toFixed(1).replace(/\.0$/, '')} MB`);
/** "PDF", "CSV", "ICS", "TXT", "MD" for the typed tile. */
export const typeName = (a: Pick<Attachment, 'kind' | 'name'>) => (a.kind === 'pdf' ? 'PDF' : a.kind === 'text' ? EXT(a.name).toUpperCase() || 'TXT' : 'Photo');
