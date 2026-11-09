// 예시(mock) 모드의 AI 채팅·일정 계산·일정 저장 (FE2).
// 실제 장소처럼 보이지 않도록 장소 이름에 "예시"를 붙이고, 서버로 아무것도 보내지 않습니다.
import { ApiError } from "./client.js";
import { demoFestivals } from "../data/festivals.js";
import { festivalStatus } from "../lib/format.js";
import {
  isDate,
  isTime,
  todayInSeoul,
  toMinutes,
  toTime,
  toSchedulePayload,
} from "../lib/itinerary.js";

const SCHEDULE_KEY = "orca:demo:schedules:v1";
const TRAVEL_MIN = 15;

const STOPS = [
  { key: "lunch", category: "restaurant", name: "예시 · 점심 식당", minutes: 60, dx: -0.012, dy: 0.006 },
  { key: "walk", category: "attraction", name: "예시 · 근처 산책 코스", minutes: 90, dx: 0.01, dy: 0.011 },
  { key: "cafe", category: "cafe", name: "예시 · 쉬어 가는 카페", minutes: 50, dx: 0.004, dy: -0.009 },
  { key: "festival", category: "festival", minutes: 150 },
  { key: "dinner", category: "restaurant", name: "예시 · 저녁 식당", minutes: 60, dx: -0.006, dy: -0.004 },
];
// 시간이 모자라면 이 순서로 뺍니다. 축제는 빼지 않습니다.
const DROP_ORDER = ["cafe", "walk", "dinner", "lunch"];

const findFestival = (id) => demoFestivals.find((item) => item.content_id === id);

const summary = (festival) =>
  festival && { ...festival, status: festivalStatus(festival) };

function wait(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(signal.reason);
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(signal.reason);
      },
      { once: true },
    );
  });
}

export function buildDemoItinerary({
  festival_content_id,
  visit_date,
  start_time = "10:00",
  end_time = "21:00",
}) {
  const festival = findFestival(festival_content_id);
  if (!festival)
    throw new ApiError(404, "FESTIVAL_NOT_FOUND", "축제를 찾을 수 없어요.");
  if (!isDate(visit_date) || visit_date < festival.start_date || visit_date > festival.end_date)
    throw new ApiError(
      400,
      "VISIT_DATE_OUT_OF_RANGE",
      `방문일은 축제 기간(${festival.start_date} ~ ${festival.end_date}) 안에서 골라 주세요.`,
    );
  const start = toMinutes(start_time);
  const end = toMinutes(end_time);
  if (!isTime(start_time) || !isTime(end_time) || end - start < 120)
    throw new ApiError(400, "TIME_TOO_SHORT", "일정을 만들려면 2시간 이상이 필요해요.");

  let stops = [...STOPS];
  const need = (list) =>
    list.reduce((sum, stop) => sum + stop.minutes, 0) + TRAVEL_MIN * (list.length - 1);
  for (const key of DROP_ORDER) {
    if (need(stops) <= end - start) break;
    stops = stops.filter((stop) => stop.key !== key);
  }
  if (need(stops) > end - start) {
    stops = stops.map((stop) => ({ ...stop, minutes: Math.min(stop.minutes, end - start) }));
  }

  let clock = start;
  const items = stops.map((stop, index) => {
    const travel = index ? TRAVEL_MIN : null;
    if (travel) clock += travel;
    const isFestival = stop.category === "festival";
    const item = {
      seq: index + 1,
      category: stop.category,
      content_id: isFestival ? festival.content_id : `demo-${stop.key}`,
      name: isFestival ? festival.title : stop.name,
      address: isFestival ? festival.address : `${festival.area_name} · 예시 위치`,
      lng: Number((festival.lng + (stop.dx || 0)).toFixed(6)),
      lat: Number((festival.lat + (stop.dy || 0)).toFixed(6)),
      start_time: toTime(clock),
      end_time: toTime(clock + stop.minutes),
      travel_min_from_prev: travel,
      distance_km_from_prev: travel ? 2.1 + index * 0.4 : null,
      memo: isFestival ? festival.place || null : null,
    };
    clock += stop.minutes;
    return item;
  });
  return {
    festival_content_id: festival.content_id,
    visit_date,
    start_time,
    end_time,
    total_travel_min: TRAVEL_MIN * (items.length - 1),
    items,
    warnings: [
      {
        code: "DEMO_DATA",
        message: "미리 보기용 예시 장소와 이동 시간이에요. 실제 장소가 아니에요.",
      },
    ],
  };
}

function defaultVisitDate(festival, today = todayInSeoul()) {
  if (today >= festival.start_date && today <= festival.end_date) return today;
  return festival.start_date;
}

function parseHour(text, suffix) {
  const match = text.match(new RegExp(`(\\d{1,2})\\s*시\\s*${suffix}`));
  const hour = match ? Number(match[1]) : NaN;
  return hour >= 0 && hour <= 23 ? `${String(hour).padStart(2, "0")}:00` : null;
}

function parseDate(text, festival) {
  const iso = text.match(/\d{4}-\d{2}-\d{2}/);
  if (iso) return iso[0];
  const md = text.match(/(\d{1,2})\s*월\s*(\d{1,2})\s*일/);
  if (md)
    return `${festival.start_date.slice(0, 4)}-${md[1].padStart(2, "0")}-${md[2].padStart(2, "0")}`;
  return null;
}

const mentioned = (text) =>
  demoFestivals.find((festival) =>
    text.replace(/\s/g, "").includes(festival.title.replace(/축제$/, "")),
  );

export function demoChatReply({ message, context = {} }) {
  const text = String(message || "");
  const previous = context.itinerary;
  const named = mentioned(text);
  const festival =
    named ||
    findFestival(context.festival_content_id) ||
    findFestival(previous?.festival_content_id);
  const wantsPlan =
    /일정|코스|시간표|짜줘|동선|카페|끝나게|시작하게|일찍|늦게/.test(text) ||
    (previous && /바꿔|추가|빼/.test(text));

  if (wantsPlan) {
    if (!festival)
      return {
        intent: "itinerary",
        blocks: [
          { type: "text", text: "어느 축제로 하루 일정을 짜드릴까요?" },
          {
            type: "quick_replies",
            options: demoFestivals.map((item) => ({
              label: item.title,
              message: `${item.title}로 일정 짜줘`,
            })),
          },
        ],
      };
    const sameFestival = previous?.festival_content_id === festival.content_id;
    const visit_date =
      parseDate(text, festival) ||
      (sameFestival ? previous.visit_date : defaultVisitDate(festival));
    const start_time =
      parseHour(text, "부터") || (sameFestival ? previous.start_time : "10:00");
    const end_time =
      parseHour(text, "까지") || (sameFestival ? previous.end_time : "21:00");
    try {
      const itinerary = buildDemoItinerary({
        festival_content_id: festival.content_id,
        visit_date,
        start_time,
        end_time,
      });
      return {
        intent: "itinerary",
        blocks: [
          {
            type: "text",
            text: `${festival.title}에 가는 ${Number(visit_date.slice(5, 7))}월 ${Number(visit_date.slice(8, 10))}일 일정을 만들었어요. ${start_time}에 출발해서 ${end_time} 전에 마무리하는 코스예요.\n지금은 미리 보기라 장소는 예시로 채웠어요.`,
          },
          { type: "timeline", itinerary, savable: true },
          {
            type: "quick_replies",
            options: [
              { label: "더 일찍 끝내줘", message: "18시까지 끝나게 바꿔줘" },
              { label: "늦게 시작할래", message: "13시부터 시작하게 바꿔줘" },
              { label: "다른 축제 추천", message: "다른 축제도 추천해줘" },
            ],
          },
        ],
      };
    } catch (error) {
      return {
        intent: "itinerary",
        blocks: [
          { type: "text", text: error.message },
          {
            type: "quick_replies",
            options: [
              {
                label: "축제 첫날로",
                message: `${festival.title} ${Number(festival.start_date.slice(5, 7))}월 ${Number(festival.start_date.slice(8, 10))}일 일정 짜줘`,
              },
              { label: "10시~21시로", message: `${festival.title} 10시부터 21시까지 일정 짜줘` },
            ],
          },
        ],
      };
    }
  }

  // 추천·정보 질문은 메시지에 축제 이름이 있을 때만 그 축제로 좁힙니다.
  if (/추천|축제|주말|어디|갈 만한|가볼/.test(text) || named) {
    const list = named ? [named] : demoFestivals;
    return {
      intent: named ? "festival_info" : "recommend",
      blocks: [
        {
          type: "text",
          text: named
            ? `${named.title}는 ${named.place || named.address}에서 열려요. 자세한 운영 정보는 카드를 눌러 확인해 주세요.`
            : "미리 보기에 담긴 축제 중에서 골라봤어요. 마음에 드는 곳이 있으면 일정도 짜드릴게요.",
        },
        {
          type: "festival_cards",
          items: list.map((item) => ({ festival: summary(item), reason: item.summary || null })),
        },
        {
          type: "quick_replies",
          options: list.slice(0, 3).map((item) => ({
            label: `${item.title} 일정`,
            message: `${item.title}로 일정 짜줘`,
          })),
        },
      ],
    };
  }

  return {
    intent: "smalltalk",
    blocks: [
      {
        type: "text",
        text: "저는 축제를 추천하고, 방문일에 맞춰 주변 장소와 함께 하루 일정을 짜드려요. 어떤 축제를 찾고 계세요?",
      },
      {
        type: "quick_replies",
        options: [
          { label: "이번 주말 축제", message: "이번 주말에 갈 만한 축제 추천해줘" },
          { label: "일정 짜줘", message: "축제 일정 짜줘" },
        ],
      },
    ],
  };
}

export function createPlannerDemo(storage) {
  let memory = [];
  const read = () => {
    try {
      const stored = JSON.parse(storage?.getItem(SCHEDULE_KEY) || "null");
      return Array.isArray(stored) ? stored : memory;
    } catch {
      return memory;
    }
  };
  const write = (list) => {
    memory = list;
    try {
      storage?.setItem(SCHEDULE_KEY, JSON.stringify(list));
    } catch {
      /* 저장이 막혀도 메모리에서 동작 */
    }
  };
  const notFound = () =>
    new ApiError(404, "SCHEDULE_NOT_FOUND", "일정을 찾을 수 없어요.");
  const withFestival = (schedule) => ({
    ...schedule,
    festival: summary(findFestival(schedule.festival_content_id)) || null,
  });

  return {
    async chat(body, signal) {
      await wait(700, signal);
      return demoChatReply(body);
    },
    async calculateItinerary(body, signal) {
      await wait(500, signal);
      return buildDemoItinerary(body);
    },
    async getSchedules() {
      return read()
        .map((schedule) => {
          const full = withFestival(schedule);
          return {
            id: full.id,
            title: full.title,
            visit_date: full.visit_date,
            festival: full.festival,
            item_count: full.items.length,
          };
        })
        .sort((a, b) => b.id - a.id);
    },
    async getSchedule(id) {
      const found = read().find((schedule) => String(schedule.id) === String(id));
      if (!found) throw notFound();
      return withFestival(found);
    },
    async createSchedule(payload) {
      const list = read();
      const schedule = {
        ...toSchedulePayload(payload, payload.title),
        id: Math.max(0, ...list.map((item) => item.id)) + 1,
        created_at: new Date().toISOString(),
      };
      write([...list, schedule]);
      return withFestival(schedule);
    },
    async updateSchedule(id, payload) {
      const list = read();
      const index = list.findIndex((schedule) => String(schedule.id) === String(id));
      if (index < 0) throw notFound();
      const schedule = { ...list[index], ...toSchedulePayload(payload, payload.title) };
      write(list.with(index, schedule));
      return withFestival(schedule);
    },
    async deleteSchedule(id) {
      const list = read();
      if (!list.some((schedule) => String(schedule.id) === String(id))) throw notFound();
      write(list.filter((schedule) => String(schedule.id) !== String(id)));
      return null;
    },
  };
}
