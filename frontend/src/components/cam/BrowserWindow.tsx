import { UpreraReplica } from "@/components/cam/UpreraReplica";
import type { SourceView } from "@/lib/checkState";
import type { Strings } from "@/lib/i18n";
import { SOURCE_INFO } from "@/lib/sources";
import { stopReason } from "@/lib/stopReason";
import type { SourceName } from "@/lib/types";
import styles from "./BrowserWindow.module.css";

interface Props {
  name: SourceName;
  view: SourceView;
  /** The page the agent is on, shown in the address bar. */
  address: string;
  /** Where a buyer can check this source themselves, when it is not the default one. */
  officialUrl?: string;
  percent: number;
  t: Strings;
}

const BADGE: Record<SourceView["status"], "live" | "stopped" | "finished" | "queued"> = {
  running: "live",
  blocked: "stopped",
  unread: "stopped",
  done: "finished",
  waiting: "queued",
};

/** The agent's browser: address bar, the live view (or an illustration) and a progress bar. */
export function BrowserWindow({ name, view, address, officialUrl, percent, t }: Props) {
  const label = t.cam.sourceLabels[name];
  const badge = BADGE[view.status];
  const stepText = view.status === "running" ? (view.note ?? t.cam.stepReading(label)) : t.cam.status[view.status];

  return (
    <section className={`card ${styles.window}`} aria-label={label}>
      <div className={styles.bar}>
        <span className={styles.lights} aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span className={`mono ${styles.address}`} title={address}>
          {address}
        </span>
        <span className={`mono ${styles.badge} ${styles[badge]}`}>
          {badge === "live" && <i className={styles.rec} aria-hidden="true" />}
          {t.cam[badge]}
        </span>
      </div>

      <div className={styles.screen}>
        <Screen name={name} view={view} t={t} label={label} officialUrl={officialUrl} />
      </div>

      <div className={styles.progress}>
        <span className="num">{percent}%</span>
        <div
          className={styles.track}
          role="progressbar"
          aria-label={t.cam.title}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
        >
          <div className={styles.fill} style={{ width: `${percent}%` }} />
        </div>
        <span className={styles.step}>{stepText}</span>
      </div>
      <p className={styles.caption}>
        {view.status === "running" && view.liveUrl ? t.cam.liveViewLabel : t.cam.illustrationNote}
      </p>
    </section>
  );
}

function Screen({
  name,
  view,
  t,
  label,
  officialUrl,
}: {
  name: SourceName;
  view: SourceView;
  t: Strings;
  label: string;
  officialUrl?: string;
}) {
  if (view.status === "running" && view.liveUrl) {
    return (
      <iframe
        className={styles.frame}
        src={view.liveUrl}
        title={t.cam.liveViewTitle(label)}
        sandbox="allow-scripts allow-same-origin"
        loading="lazy"
        referrerPolicy="no-referrer"
      />
    );
  }
  if (view.status === "running") return <UpreraReplica notes={view.notes} t={t} />;
  if (view.status === "blocked") {
    return <Notice tone="stopped" text={stopReason(view.reason, t)} name={name} href={officialUrl} t={t} />;
  }
  if (view.status === "unread") {
    return <Notice tone="stopped" text={t.cam.unreadReason} name={name} href={officialUrl} t={t} />;
  }
  return <Notice tone="quiet" text={t.cam.status[view.status]} name={name} href={officialUrl} t={t} />;
}

function Notice({
  tone,
  text,
  name,
  href,
  t,
}: {
  tone: "stopped" | "quiet";
  text: string;
  name: SourceName;
  href?: string;
  t: Strings;
}) {
  return (
    <div className={`${styles.notice} ${styles[tone === "stopped" ? "noticeStopped" : "noticeQuiet"]}`}>
      <p>{text}</p>
      {tone === "stopped" && (
        <a href={href ?? SOURCE_INFO[name].officialUrl} target="_blank" rel="noopener noreferrer">
          {t.cam.checkYourself}
          <span className="sr"> ({t.common.opensInNewTab})</span>
        </a>
      )}
    </div>
  );
}
