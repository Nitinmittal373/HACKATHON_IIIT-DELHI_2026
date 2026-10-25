"use client";

import { useState } from "react";

import { FaqItem } from "@/components/FaqItem";
import styles from "./Faq.module.css";

interface Props {
  title: string;
  items: { question: string; answer: string }[];
}

/** Accessible accordion. The first answer starts open; each button announces its state. */
export function Faq({ title, items }: Props) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className={`wrap section rv ${styles.faq}`} aria-labelledby="faq-title">
      <h2 id="faq-title" className={`h2 ${styles.title}`}>
        {title}
      </h2>
      {items.map((item, index) => (
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
