"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { useLang } from "@/lib/LangProvider";
import { detectState, stateLabel } from "@/lib/states";
import { useStates } from "@/lib/useStates";
import styles from "./SearchBar.module.css";

interface Props {
  label: string;
  placeholder: string;
  submitLabel: string;
}

const MAX_QUERY_LENGTH = 100;
const ALL_INDIA = "";

/**
 * The big search box. It takes a RERA number of any state, a project name or a promoter name.
 * The state picker starts on All India and follows the number as it is typed.
 */
export function SearchBar({ label, placeholder, submitLabel }: Props) {
  const router = useRouter();
  const { lang, t } = useLang();
  const load = useStates();
  const inputId = useId();
  const stateId = useId();
  const input = useRef<HTMLInputElement>(null);
  const [state, setState] = useState(ALL_INDIA);
  // A state the visitor picked by hand is never changed by what they type.
  const [chosenByHand, setChosenByHand] = useState(false);
  const states = load.status === "ready" ? load.states : [];

  function follow(text: string) {
    if (!chosenByHand) setState(detectState(text, states)?.code ?? ALL_INDIA);
  }

  // The list can arrive after the visitor has started typing; look at what is there then.
  useEffect(() => {
    if (load.status === "ready") follow(input.current?.value ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load.status]);

  function typed(event: ChangeEvent<HTMLInputElement>) {
    follow(event.target.value);
  }

  function pick(event: ChangeEvent<HTMLSelectElement>) {
    setState(event.target.value);
    setChosenByHand(event.target.value !== ALL_INDIA);
  }

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = input.current?.value.trim() ?? "";
    if (query.length < 2) {
      input.current?.focus();
      return;
    }
    const scope = state === ALL_INDIA ? "" : `&state=${encodeURIComponent(state)}`;
    router.push(`/check?q=${encodeURIComponent(query)}${scope}`);
  }

  return (
    // Without JavaScript the form still works as a plain GET to the same address.
    <form id="search" className={styles.bar} action="/check" method="get" onSubmit={search} role="search">
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        aria-hidden="true"
        className={styles.icon}
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </svg>
      <label htmlFor={inputId} className="sr">
        {label}
      </label>
      <input
        ref={input}
        id={inputId}
        name="q"
        type="search"
        className={styles.input}
        placeholder={placeholder}
        maxLength={MAX_QUERY_LENGTH}
        minLength={2}
        autoComplete="off"
        required
        onChange={typed}
      />
      <label htmlFor={stateId} className="sr">
        {t.states.pickerLabel}
      </label>
      <select id={stateId} name="state" className={styles.state} value={state} onChange={pick}>
        <option value={ALL_INDIA}>{t.states.allIndia}</option>
        {states.map((item) => (
          <option key={item.code} value={item.code}>
            {stateLabel(item.code, item.name, lang)}
          </option>
        ))}
      </select>
      <button type="submit" className="btn btnBig">
        {submitLabel}
        <svg
          className="arrow"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </button>
    </form>
  );
}
