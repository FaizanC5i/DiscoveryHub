import type { QuickAccessItem } from "../types/dashboard";
import { QuickAccessCard } from "./QuickAccessCard";

interface QuickAccessProps {
  items: QuickAccessItem[];
}

export function QuickAccess({ items }: QuickAccessProps) {
  return (
    <section aria-labelledby="quick-access-heading" className="flex flex-col gap-4">
      <h2 id="quick-access-heading" className="text-title-small font-semibold text-fg">
        Quick Access
      </h2>
      <ul className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {items.map((item) => (
          <li key={item.key}>
            <QuickAccessCard item={item} />
          </li>
        ))}
      </ul>
    </section>
  );
}
