"use client";

import { useEffect, useReducer, useRef, useState } from "react";

import { eventsUrl, getCheck } from "@/lib/api";
import { applyCheck, applyEvent, initialState, type CamState } from "@/lib/checkState";
import type { CheckEvent, CheckStatus, DisplayScore, EventType } from "@/lib/types";

export type Connection = "live" | "reconnecting" | "polling" | "closed";

// A record keyed by the generated event type: a new event type in the API fails the build here.
const LISTENED: Record<EventType, true> = {
  "source.started": true,
  "source.live_url": true,
  "source.progress": true,
  "finding.added": true,
  "source.blocked": true,
  "source.completed": true,
  "check.completed": true,
};
const EVENT_TYPES = Object.keys(LISTENED) as EventType[];
const RECONNECT_DELAYS_MS = [1000, 2000, 4000];
const POLL_INTERVAL_MS = 4000;

type Action = { kind: "event"; event: CheckEvent } | { kind: "update"; apply: Update };
type Update = (current: CamState) => CamState;

function reduce(state: CamState, action: Action): CamState {
  return action.kind === "event" ? applyEvent(state, action.event) : action.apply(state);
}

/**
 * Follows one check: Server-Sent Events first, reconnecting a few times, then polling every
 * four seconds. It stops as soon as the check is over. It only reports state; the page decides
 * what to do about it, so this hook never navigates.
 */
export function useCheckEvents(checkId: string): { state: CamState; connection: Connection } {
  const [state, dispatch] = useReducer(reduce, undefined, initialState);
  const [connection, setConnection] = useState<Connection>("live");
  // A reconnect replays the run from the start; events already shown are skipped by number.
  const seen = useRef(0);

  useEffect(() => {
    let stopped = false;
    let source: EventSource | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let failures = 0;

    function stop() {
      stopped = true;
      source?.close();
      clearTimeout(timer);
      setConnection("closed");
    }

    function onMessage(message: MessageEvent<string>) {
      const number = Number(message.lastEventId);
      if (number && number <= seen.current) return;
      seen.current = number || seen.current;
      let event: CheckEvent;
      try {
        event = JSON.parse(message.data) as CheckEvent;
      } catch {
        return;
      }
      dispatch({ kind: "event", event });
      if (event.type === "check.completed") stop();
    }

    function connect() {
      source = new EventSource(eventsUrl(checkId));
      source.onopen = () => {
        failures = 0;
        setConnection("live");
      };
      for (const type of EVENT_TYPES) {
        source.addEventListener(type, (message) => onMessage(message as MessageEvent<string>));
      }
      source.onerror = () => {
        source?.close();
        if (stopped) return;
        const delay = RECONNECT_DELAYS_MS[failures];
        failures += 1;
        if (delay === undefined) {
          setConnection("polling");
          void poll();
          return;
        }
        setConnection("reconnecting");
        timer = setTimeout(connect, delay);
      };
    }

    async function poll() {
      if (stopped) return;
      try {
        const check = await getCheck(checkId);
        if (stopped) return;
        dispatch({ kind: "update", apply: (current) => applyCheck(current, check) });
        if (check.status === "completed" || check.status === "failed") {
          const { display_score: score } = check;
          dispatch({ kind: "update", apply: (current) => finish(current, check.status, score) });
          stop();
          return;
        }
      } catch {
        // The backend may be restarting; keep trying until the check is over.
      }
      timer = setTimeout(() => void poll(), POLL_INTERVAL_MS);
    }

    connect();
    return stop;
  }, [checkId]);

  return { state, connection };
}

function finish(current: CamState, status: CheckStatus, score: DisplayScore | null): CamState {
  if (status === "completed") return { ...current, outcome: { status: "completed", score } };
  const message = "The check could not be completed";
  return { ...current, outcome: { status: "failed", message } };
}
