import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import type { User } from "@/lib/api";

export function UserCard({ user }: { user: User }) {
  return (
    <Link
      href={`/usuarios/${user.username}`}
      className="flex items-center gap-3 rounded-lg border bg-white p-3 hover:border-brand-500"
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
