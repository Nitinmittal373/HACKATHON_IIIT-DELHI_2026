import type { Metadata } from "next";
import Link from "next/link";

import { ApiProblem } from "@/components/ApiProblem";
import { PageMessage } from "@/components/PageMessage";
import { AlertCard } from "@/components/sentinel/AlertCard";
import { ApiError, getAlerts } from "@/lib/api";
import type { Lang, Strings } from "@/lib/i18n";
import { getStrings } from "@/lib/i18n/server";
import type { Alert } from "@/lib/types";
import styles from "./alerts.module.css";

export const metadata: Metadata = { title: "Alerts · NeevCheck" };

interface Props {
  searchParams: Promise<{ email?: string | string[] }>;
}

async function load(email: string): Promise<Alert[] | ApiError> {
  try {
    return await getAlerts(email);
  } catch (error) {
    if (error instanceof ApiError) return error;
    throw error;
  }
}

export default async function AlertsPage({ searchParams }: Props) {
  const raw = (await searchParams).email;
  const email = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";
  const { t, lang } = await getStrings();

  return (
    <>
      <h1 className="h2 pageTitle">{t.alerts.title}</h1>
      <p className="pageLead">{t.alerts.lead}</p>
      {/* A plain GET form: the address carries the email, so the page can be reloaded and shared. */}
      <form className={styles.form} action="/alerts" method="get">
        <label htmlFor="alerts-email" className="sr">
          {t.alerts.emailLabel}
        </label>
        <input
          id="alerts-email"
          name="email"
          type="email"
          className={styles.input}
          placeholder={t.sentinel.emailPlaceholder}
          defaultValue={email}
          maxLength={254}
          required
        />
        <button type="submit" className="btn">
          {t.alerts.show}
        </button>
      </form>
      {email && <Results email={email} t={t} lang={lang} />}
    </>
  );
}

interface ResultsProps {
  email: string;
  t: Strings;
  lang: Lang;
}

async function Results({ email, t, lang }: ResultsProps) {
  const result = await load(email);
  if (result instanceof ApiError) {
    if (result.status === 422) {
      return (
        <PageMessage alert title={t.alerts.failedTitle}>
          {t.alerts.invalidEmail}
        </PageMessage>
      );
    }
    return <ApiProblem error={result} retryHref={`/alerts?email=${encodeURIComponent(email)}`} />;
  }
  if (result.length === 0) {
    return (
      <PageMessage
        title={t.alerts.empty}
        actions={
          <Link href="/#search" className="btn2">
            {t.nav.check}
          </Link>
        }
      />
    );
  }
  return (
    <ul className={styles.list}>
      {result.map((alert) => (
        <li key={alert.id}>
          <AlertCard alert={alert} t={t} lang={lang} />
        </li>
      ))}
    </ul>
  );
}
