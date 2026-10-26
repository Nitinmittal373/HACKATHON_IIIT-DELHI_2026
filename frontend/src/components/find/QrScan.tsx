"use client";

import { useEffect, useId, useRef, useState, type ChangeEvent } from "react";

import { ExtractedNumbers } from "@/components/find/ExtractedNumbers";
import { extractFromText } from "@/lib/api";
import { describeApiError } from "@/lib/apiMessages";
import { useLang } from "@/lib/LangProvider";
import { decodeImageData, decodePhoto } from "@/lib/qr";
import type { ExtractResponse } from "@/lib/types";
import styles from "./MoreWays.module.css";

const FRAME_EVERY_MS = 250;

type Phase =
  | { kind: "idle" }
  | { kind: "scanning" }
  | { kind: "sending" }
  | { kind: "done"; result: ExtractResponse }
  | { kind: "failed"; message: string };

/** A QR code from the camera or a photo, decoded in the browser; only its text is sent. */
export function QrScan() {
  const { t } = useLang();
  const photoId = useId();
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const copy = t.find.more.qr;

  function stopCamera() {
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
  }

  // The camera must never stay on after the visitor leaves this tab.
  useEffect(() => stopCamera, []);

  async function send(text: string) {
    stopCamera();
    setPhase({ kind: "sending" });
    try {
      setPhase({ kind: "done", result: await extractFromText(text) });
    } catch (error) {
      setPhase({ kind: "failed", message: describeApiError(error, t) });
    }
  }

  async function openCamera() {
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    } catch {
      return setPhase({ kind: "failed", message: copy.noCamera });
    }
    setPhase({ kind: "scanning" });
  }

  // Looks at the camera picture a few times a second until a code is read.
  useEffect(() => {
    if (phase.kind !== "scanning" || !video.current || !stream.current) return;
    const element = video.current;
    element.srcObject = stream.current;
    void element.play();
    const canvas = document.createElement("canvas");
    const timer = setInterval(async () => {
      if (!element.videoWidth) return;
      canvas.width = element.videoWidth;
      canvas.height = element.videoHeight;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) return;
      context.drawImage(element, 0, 0);
      const text = await decodeImageData(context.getImageData(0, 0, canvas.width, canvas.height));
      if (text) {
        clearInterval(timer);
        void send(text);
      }
    }, FRAME_EVERY_MS);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase.kind]);

  async function photo(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const text = await decodePhoto(file).catch(() => null);
    if (text) return send(text);
    setPhase({ kind: "failed", message: copy.noQr });
  }

  return (
    <div className={styles.drop}>
      <div className={styles.actions}>
        {phase.kind === "scanning" ? (
          <button type="button" className="btn2" onClick={() => { stopCamera(); setPhase({ kind: "idle" }); }}>
            {copy.stop}
          </button>
        ) : (
          <button type="button" className="btn" onClick={openCamera}>
            {copy.camera}
          </button>
        )}
        <label htmlFor={photoId} className="btn2">
          {copy.photo}
        </label>
        <input id={photoId} className="sr" type="file" accept="image/*" onChange={photo} />
      </div>
      {phase.kind === "scanning" && (
        <>
          <video ref={video} className={styles.video} playsInline muted aria-label={copy.cameraLabel} />
          <p className={styles.status} role="status">
            {copy.hint} {copy.scanning}
          </p>
        </>
      )}
      <p className={styles.privacy}>{copy.privacy}</p>
      {phase.kind === "failed" && (
        <p className={styles.error} role="alert">
          {phase.message}
        </p>
      )}
      {phase.kind === "done" && <ExtractedNumbers result={phase.result} />}
    </div>
  );
}
