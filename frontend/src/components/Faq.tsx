"use client";

import { useState } from "react";

import { FaqItem } from "@/components/FaqItem";
import styles from "./Faq.module.css";

const QUESTIONS = [
  {
    question: "Is NeevCheck a credit rating or legal advice?",
    answer:
      "No. It is decision support built from public records. Every point links to the original record so you, your family or your lawyer can check it.",
  },
  {
    question: "Where does the data come from?",
    answer:
      "Official sources: UP-RERA, the company registry, insolvency orders from IBBI and NCLT, land authority lists and court and news reports. A TinyFish browser agent reads them live and saves the link and time.",
  },
  {
    question: "What if a website asks for a CAPTCHA?",
    answer:
      "We stop. NeevCheck never bypasses a CAPTCHA. That source is marked “Unable to verify”, which lowers confidence, not the score.",
  },
  {
    question: "Does finding nothing make a project safe?",
    answer:
      "No. Absence of a record never adds points. It only means nothing was found in the sources we could read.",
  },
];

/** Accessible accordion. The first answer starts open; each button announces its state. */
export function Faq() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className={`wrap section rv ${styles.faq}`} aria-labelledby="faq-title">
      <h2 id="faq-title" className={`h2 ${styles.title}`}>
        Questions, answered
      </h2>
      {QUESTIONS.map((item, index) => (
        <FaqItem
          key={item.question}
          id={`faq-${index}`}
          question={item.question}
          answer={item.answer}
          open={openIndex === index}
          onToggle={() => setOpenIndex(openIndex === index ? null : index)}
        />
      ))}
    </section>
  );
}
