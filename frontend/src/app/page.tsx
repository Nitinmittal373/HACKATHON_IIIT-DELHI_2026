import { Hero } from "@/components/Hero";
import { LegacyAnchors } from "@/components/pages/LegacyAnchors";
import { RecentStrip } from "@/components/RecentStrip";
import { WakeServer } from "@/components/WakeServer";

/**
 * The home page is the hero and its search, and the visitor's own recent checks. Everything
 * else lives on its own page: Check a project, How it works and For RWAs.
 */
export default function HomePage() {
  return (
    <main>
      <WakeServer />
      <LegacyAnchors />
      <Hero />
      <RecentStrip />
    </main>
  );
}
