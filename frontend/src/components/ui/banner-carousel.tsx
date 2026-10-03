"use client";

import { useEffect, useRef, useState } from "react";
import { apiUrl } from "@/lib/api";
import { ar } from "@/messages/ar";

export type PromoBanner = { id: number; title: string; body: string; image_url: string | null };

export function BannerCarousel({ banners }: { banners: PromoBanner[] }) {
  const [index, setIndex] = useState(0);
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const startX = useRef(0);
  const count = banners.length;

  useEffect(() => {
    if (count < 2 || dragging) return;
    const timer = window.setInterval(() => setIndex((current) => (current + 1) % count), 7000);
    return () => window.clearInterval(timer);
  }, [count, dragging, index]);

  useEffect(() => {
    if (index >= count) setIndex(0);
  }, [count, index]);

  if (count === 0) return null;
  const banner = banners[index];

  function step(direction: number) {
    setIndex((current) => (current + direction + count) % count);
  }

  return (
    <section
      className="relative min-h-44 touch-pan-y overflow-hidden rounded-3xl text-white shadow-[0_12px_28px_rgba(30,58,95,0.08)]"
      onPointerDown={(event) => {
        startX.current = event.clientX;
        setDragging(true);
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        if (!dragging) return;
        setDragX(event.clientX - startX.current);
      }}
      onPointerUp={(event) => {
        const delta = event.clientX - startX.current;
        setDragging(false);
        setDragX(0);
        if (Math.abs(delta) > 48) step(delta > 0 ? -1 : 1);
      }}
      onPointerCancel={() => {
        setDragging(false);
        setDragX(0);
      }}
    >
      <div className={`absolute inset-0 ${dragging ? "" : "transition-transform duration-500 ease-out"}`} style={{ transform: `translateX(${dragX}px)` }}>
        {banner.image_url ? <img src={apiUrl(banner.image_url)} alt="" className="absolute inset-0 h-full w-full object-cover" /> : <div className="absolute inset-0 bg-[#101826]" />}
        <div className="absolute inset-0 bg-gradient-to-l from-[#07111c]/92 via-[#07111c]/75 to-transparent" />
        <div className="relative flex min-h-44 flex-col justify-between p-5">
          <span className="w-fit rounded-full bg-primary-container px-2.5 py-1 text-xs font-bold">{ar.ads}</span>
          <div>
            <h2 className="text-2xl font-extrabold">{banner.title}</h2>
            <p className="mt-1 max-w-xl text-sm text-white/85">{banner.body}</p>
          </div>
        </div>
      </div>
      {count > 1 ? (
        <div className="absolute bottom-3 start-5 z-10 flex gap-1.5">
          {banners.map((item, dot) => (
            <button key={item.id} type="button" aria-label={item.title} onClick={() => setIndex(dot)} className={`h-1.5 rounded-full transition ${dot === index ? "w-5 bg-white" : "w-1.5 bg-white/50"}`} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
