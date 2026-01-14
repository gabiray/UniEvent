import React, { useEffect, useMemo, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import styles from "../../styles/QrScanner.module.css";

export default function QrScanner({
  active = false,
  onDecode,
  onStatus,
  fps = 10,
  qrbox = 260,
  cooldownMs = 1400,
}) {
  const elementId = useMemo(
    () => `qr-reader-${Math.random().toString(36).slice(2)}`,
    []
  );

  const qrRef = useRef(null);
  const lastScanRef = useRef({ text: "", ts: 0 });

  const [starting, setStarting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const stopScanner = async () => {
      try {
        if (qrRef.current) {
          // 2 = SCANNING (în multe versiuni), dar tratăm safe.
          await qrRef.current.stop?.();
          await qrRef.current.clear?.();
        }
      } catch {
        // ignore
      } finally {
        qrRef.current = null;
      }
    };

    const startScanner = async () => {
      if (!active || starting) return;

      setStarting(true);
      onStatus?.("Pornesc camera…");

      try {
        await stopScanner();
        if (cancelled) return;

        const qr = new Html5Qrcode(elementId);
        qrRef.current = qr;

        const config = {
          fps,
          qrbox: typeof qrbox === "number" ? { width: qrbox, height: qrbox } : qrbox,
          aspectRatio: 1.0,
        };

        const handleSuccess = async (decodedText) => {
          const now = Date.now();
          const last = lastScanRef.current;

          // evităm spam pe același cod
          if (decodedText === last.text && now - last.ts < cooldownMs) return;

          lastScanRef.current = { text: decodedText, ts: now };
          onStatus?.("Cod detectat. Verific…");

          try {
            await Promise.resolve(onDecode?.(decodedText));
          } catch {
            // dacă onDecode aruncă, nu blocăm scannerul
          }
        };

        // onFailure e foarte “noisy” (se apelează continuu), deci îl ignorăm
        const handleFailure = () => {};

        // Preferăm camera din spate (environment). Dacă nu merge, cădem pe primul device.
        try {
          await qr.start({ facingMode: "environment" }, config, handleSuccess, handleFailure);
        } catch {
          const cams = await Html5Qrcode.getCameras();
          if (!cams?.length) throw new Error("Nu găsesc camere disponibile.");
          await qr.start(cams[0].id, config, handleSuccess, handleFailure);
        }

        if (!cancelled) onStatus?.("Scanner pornit. Apropie QR-ul de cameră.");
      } catch (e) {
        if (!cancelled) onStatus?.(e?.message || "Nu pot porni scannerul.");
        await stopScanner();
      } finally {
        if (!cancelled) setStarting(false);
      }
    };

    if (active) startScanner();
    else stopScanner();

    return () => {
      cancelled = true;
      stopScanner();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, elementId, fps, qrbox, cooldownMs]);

  return (
    <div className={styles.wrap}>
      <div className={styles.reader} id={elementId} />
      <div className={styles.hint}>
        * Pe telefon, camera merge doar pe HTTPS (sau localhost).
      </div>
    </div>
  );
}
