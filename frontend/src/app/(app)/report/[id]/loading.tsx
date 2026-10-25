import { Skeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div aria-busy="true">
      <Skeleton width={220} height={14} />
      <Skeleton width="50%" height={40} style={{ marginTop: 14 }} />
      <Skeleton width="35%" height={16} style={{ marginTop: 12 }} />
      <Skeleton height={230} style={{ marginTop: 26 }} />
      <Skeleton height={280} style={{ marginTop: 20 }} />
    </div>
  );
}
