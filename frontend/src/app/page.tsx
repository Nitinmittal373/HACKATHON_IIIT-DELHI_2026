import { Hero } from "@/components/Hero";
import { EXAMPLE_REPORT } from "@/lib/example8334";

/** The home page fetches nothing: its examples are a recorded real check, labelled as such. */
export default function HomePage() {
  return (
    <main>
      <Hero report={EXAMPLE_REPORT} />
    </main>
  );
}
