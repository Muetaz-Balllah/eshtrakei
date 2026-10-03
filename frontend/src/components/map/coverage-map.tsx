"use client";

import { useEffect, useRef } from "react";

export type MapTower = {
  id: number;
  company_name: string;
  name: string;
  latitude: number;
  longitude: number;
  radius_meters: number;
};

type MapLayer = { remove: () => void; bindPopup: (html: string) => void };
type LeafletMap = {
  setView: (center: [number, number], zoom: number) => void;
  fitBounds: (bounds: [number, number][], options?: { padding?: [number, number]; maxZoom?: number }) => void;
  on: (event: string, handler: (event: { latlng: { lat: number; lng: number } }) => void) => void;
  remove: () => void;
};

declare global {
  interface Window {
    L?: {
      map: (element: HTMLElement) => LeafletMap;
      tileLayer: (url: string, options: { attribution: string }) => { addTo: (map: LeafletMap) => void };
      circle: (center: [number, number], options: { radius: number; color: string; fillOpacity: number }) => { addTo: (map: LeafletMap) => MapLayer };
      marker: (center: [number, number]) => { addTo: (map: LeafletMap) => MapLayer };
    };
  }
}

let leafletLoading: Promise<void> | null = null;

function loadLeaflet() {
  if (window.L) return Promise.resolve();
  if (leafletLoading) return leafletLoading;
  leafletLoading = new Promise((resolve) => {
    if (!document.querySelector("link[data-leaflet]")) {
      const style = document.createElement("link");
      style.rel = "stylesheet";
      style.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      style.dataset.leaflet = "true";
      document.head.appendChild(style);
    }
    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = () => {
      const icons = window.L as unknown as { Icon?: { Default?: { prototype?: { _getIconUrl?: unknown }; mergeOptions: (options: object) => void } } };
      if (icons?.Icon?.Default) {
        delete icons.Icon.Default.prototype?._getIconUrl;
        icons.Icon.Default.mergeOptions({
          iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
          iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
          shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        });
      }
      resolve();
    };
    document.body.appendChild(script);
  });
  return leafletLoading;
}

export function CoverageMap({
  towers,
  onPick,
}: {
  towers: MapTower[];
  onPick?: (latitude: number, longitude: number) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const layers = useRef<MapLayer[]>([]);
  const towersRef = useRef(towers);
  towersRef.current = towers;
  const pickRef = useRef(onPick);
  pickRef.current = onPick;

  useEffect(() => {
    const node = host.current;
    if (!node) return;
    let cancelled = false;
    loadLeaflet().then(() => {
      if (cancelled || !node || !window.L || mapRef.current) return;
      const map = window.L.map(node);
      map.setView([32.8872, 13.1913], 11);
      window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap",
      }).addTo(map);
      map.on("click", (event) => pickRef.current?.(event.latlng.lat, event.latlng.lng));
      mapRef.current = map;
      paint(map);
    });
    return () => {
      cancelled = true;
      layers.current = [];
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  function paint(map: LeafletMap) {
    layers.current.forEach((layer) => layer.remove());
    layers.current = [];
    const current = towersRef.current;
    if (!window.L || current.length === 0) return;
    const bounds: [number, number][] = [];
    current.forEach((tower) => {
      const center: [number, number] = [Number(tower.latitude), Number(tower.longitude)];
      bounds.push(center);
      const label = `${tower.company_name} — ${tower.name}`;
      const circle = window.L!.circle(center, { radius: tower.radius_meters, color: "#f58220", fillOpacity: 0.18 }).addTo(map);
      circle.bindPopup(label);
      const marker = window.L!.marker(center).addTo(map);
      marker.bindPopup(label);
      layers.current.push(circle, marker);
    });
    if (bounds.length === 1) map.setView(bounds[0], 13);
    else map.fitBounds(bounds, { padding: [28, 28], maxZoom: 13 });
  }

  useEffect(() => {
    if (mapRef.current) paint(mapRef.current);
  }, [towers]);

  return <div ref={host} className="z-0 h-80 w-full overflow-hidden rounded-3xl lg:h-[32rem]" />;
}
