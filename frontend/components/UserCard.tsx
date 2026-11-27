import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import type { User } from "@/lib/api";

export function UserCard({ user }: { user: User }) {
  return (
    <Link
      href={`/usuarios/${user.username}`}
      className="flex h-full items-center gap-3 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm hover:border-brand-500"
    >
      <Avatar user={user} />
      <div className="min-w-0">
        <p className="truncate font-medium">{user.name}</p>
        <p className="truncate text-sm text-zinc-500">
          @{user.username}
          {user.bio ? ` — ${user.bio}` : ""}
        </p>
      </div>
    </Link>
  );
}
