import { Skeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div aria-busy="true">
      <Skeleton width={160} height={14} />
      <Skeleton width="60%" height={40} style={{ marginTop: 14 }} />
      <Skeleton width="45%" height={16} style={{ marginTop: 14 }} />
      <Skeleton height={260} style={{ marginTop: 26 }} />
    </div>
  );
}
