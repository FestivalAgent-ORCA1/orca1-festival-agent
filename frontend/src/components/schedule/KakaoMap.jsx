import { useEffect, useRef, useState } from "react";
import { categoryNames } from "../../lib/itinerary.js";

// 카카오맵 JavaScript 키는 브라우저에 공개되는 키입니다.
// 카카오 개발자 콘솔 > 플랫폼 > Web에 허용 도메인(localhost:5173, 배포 주소)을 꼭 등록하세요.
const APP_KEY = import.meta.env.VITE_KAKAO_MAP_KEY || "";
const ROUTE_COLOR = "#2855e7";

let sdkPromise = null;
function loadKakaoSdk() {
  if (window.kakao?.maps?.LatLng) return Promise.resolve(window.kakao);
  if (!sdkPromise)
    sdkPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(APP_KEY)}&autoload=false`;
      script.async = true;
      script.onload = () => {
        if (window.kakao?.maps) window.kakao.maps.load(() => resolve(window.kakao));
        else fail();
      };
      const fail = () => {
        sdkPromise = null;
        script.remove();
        reject(new Error("카카오맵을 불러오지 못했어요."));
      };
      script.onerror = fail;
      document.head.appendChild(script);
    });
  return sdkPromise;
}

/**
 * points: [{ seq, name, category, lat, lng }] — 방문 순서대로 번호 핀과 이동선을 그립니다.
 * activeSeq / onSelect: 시간표와 지도의 선택 상태를 맞출 때 사용합니다.
 */
export default function KakaoMap({ points = [], activeSeq = null, onSelect, className = "" }) {
  const [status, setStatus] = useState(APP_KEY ? "loading" : "nokey");
  const container = useRef(null);
  const map = useRef(null);
  const mapNode = useRef(null);
  const drawn = useRef({ overlays: [], line: null, pins: new Map() });
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const key = points.map((p) => `${p.seq}:${p.lat}:${p.lng}`).join("|");

  useEffect(() => {
    if (!APP_KEY) return undefined;
    let alive = true;
    loadKakaoSdk().then(
      () => alive && setStatus("ready"),
      () => alive && setStatus("error"),
    );
    return () => {
      alive = false;
    };
  }, []);

  // 핀·이동선 그리기
  useEffect(() => {
    if (status !== "ready" || !container.current || !points.length) return undefined;
    const { maps } = window.kakao;
    if (!map.current || mapNode.current !== container.current) {
      mapNode.current = container.current;
      map.current = new maps.Map(container.current, {
        center: new maps.LatLng(points[0].lat, points[0].lng),
        level: 5,
      });
    }
    const positions = points.map((p) => new maps.LatLng(p.lat, p.lng));
    const pins = new Map();
    const overlays = points.map((point, index) => {
      const pin = document.createElement("button");
      pin.type = "button";
      pin.className = `map-pin map-pin--${point.category}`;
      pin.textContent = String(point.seq);
      pin.title = `${point.seq}. ${point.name}`;
      pin.setAttribute("aria-label", `${point.seq}번 ${point.name} (${categoryNames[point.category] || "장소"})`);
      pin.addEventListener("click", () => onSelectRef.current?.(point.seq));
      pins.set(point.seq, pin);
      const overlay = new maps.CustomOverlay({
        position: positions[index],
        content: pin,
        yAnchor: 0.5,
        zIndex: 2,
      });
      overlay.setMap(map.current);
      return overlay;
    });
    const line = new maps.Polyline({
      path: positions,
      strokeWeight: 4,
      strokeColor: ROUTE_COLOR,
      strokeOpacity: 0.75,
      strokeStyle: "shortdash",
    });
    line.setMap(map.current);
    if (positions.length === 1) {
      map.current.setLevel(4);
      map.current.setCenter(positions[0]);
    } else {
      const bounds = new maps.LatLngBounds();
      positions.forEach((position) => bounds.extend(position));
      map.current.setBounds(bounds, 40, 40, 40, 40);
    }
    drawn.current = { overlays, line, pins };
    return () => {
      overlays.forEach((overlay) => overlay.setMap(null));
      line.setMap(null);
    };
    // points 배열은 매 렌더 새로 만들어지므로 좌표 문자열(key)로 비교합니다.
  }, [status, key]);

  // 선택된 장소 강조
  useEffect(() => {
    drawn.current.pins.forEach((pin, seq) => pin.classList.toggle("is-active", seq === activeSeq));
    const point = points.find((p) => p.seq === activeSeq);
    if (point && map.current && window.kakao?.maps)
      map.current.panTo(new window.kakao.maps.LatLng(point.lat, point.lng));
  }, [activeSeq, key, status]);

  // 화면 크기가 바뀌면 지도 다시 맞추기
  useEffect(() => {
    if (status !== "ready" || !container.current || typeof ResizeObserver === "undefined")
      return undefined;
    const observer = new ResizeObserver(() => map.current?.relayout());
    observer.observe(container.current);
    return () => observer.disconnect();
  }, [status]);

  if (!points.length)
    return (
      <div className={`route-map route-map--empty ${className}`}>
        <p>지도에 표시할 위치 정보가 없어요.</p>
      </div>
    );

  if (status === "nokey" || status === "error")
    return (
      <div className={`route-map ${className}`}>
        <RouteSketch points={points} activeSeq={activeSeq} onSelect={onSelect} />
        <p className="route-map-note">
          {status === "nokey"
            ? "카카오맵 키가 없어 방문 순서만 간단히 그렸어요."
            : "카카오맵을 불러오지 못해 방문 순서만 간단히 그렸어요."}
        </p>
      </div>
    );

  return (
    <div className={`route-map ${className}`}>
      <div
        ref={container}
        className="route-map-canvas"
        role="region"
        aria-label="방문 장소 지도"
      />
      {status === "loading" && <p className="route-map-note">지도를 불러오고 있어요.</p>}
    </div>
  );
}

// 키가 없을 때(예시 모드·로컬 개발) 쓰는 간단한 순서도
function RouteSketch({ points, activeSeq, onSelect }) {
  const W = 320;
  const H = 200;
  const PAD = 28;
  const midLat = points.reduce((sum, p) => sum + p.lat, 0) / points.length;
  const kx = Math.cos((midLat * Math.PI) / 180);
  const xs = points.map((p) => p.lng * kx);
  const ys = points.map((p) => p.lat);
  const [minX, maxX, minY, maxY] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const span = Math.max(maxX - minX, maxY - minY, 1e-6);
  const scale = Math.min((W - PAD * 2) / span, (H - PAD * 2) / span);
  const ox = (W - (maxX - minX) * scale) / 2;
  const oy = (H - (maxY - minY) * scale) / 2;
  const coords = points.map((p, i) => ({
    ...p,
    x: ox + (xs[i] - minX) * scale,
    y: H - (oy + (ys[i] - minY) * scale),
  }));
  return (
    <svg className="route-sketch" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="방문 순서 그림">
      <polyline
        points={coords.map((c) => `${c.x},${c.y}`).join(" ")}
        fill="none"
        stroke={ROUTE_COLOR}
        strokeWidth="2.5"
        strokeDasharray="6 5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {coords.map((c) => (
        <g
          key={c.seq}
          className={`sketch-pin sketch-pin--${c.category} ${c.seq === activeSeq ? "is-active" : ""}`}
          onClick={() => onSelect?.(c.seq)}
        >
          <title>{`${c.seq}. ${c.name}`}</title>
          <circle cx={c.x} cy={c.y} r="12" />
          <text x={c.x} y={c.y} dy="0.35em" textAnchor="middle">
            {c.seq}
          </text>
        </g>
      ))}
    </svg>
  );
}
