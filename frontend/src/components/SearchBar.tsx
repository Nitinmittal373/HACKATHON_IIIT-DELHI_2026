"use client";

import { useRouter } from "next/navigation";
import { useId, useRef, type FormEvent } from "react";

import styles from "./SearchBar.module.css";

interface Props {
  label: string;
  placeholder: string;
  submitLabel: string;
}

const MAX_QUERY_LENGTH = 100;

/** The big search box. It takes a UP-RERA number, a project name or a promoter name. */
export function SearchBar({ label, placeholder, submitLabel }: Props) {
  const router = useRouter();
  const inputId = useId();
  const input = useRef<HTMLInputElement>(null);

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = input.current?.value.trim() ?? "";
    if (query.length < 2) {
      input.current?.focus();
      return;
    }
    router.push(`/check?q=${encodeURIComponent(query)}`);
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
      />
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
