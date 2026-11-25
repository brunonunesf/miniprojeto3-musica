import type { User } from "@/lib/api";

type Props = {
  user: Pick<User, "name" | "avatar_url">;
  tamanho?: "md" | "xl";
};

const TAMANHOS = {
  md: "h-10 w-10 text-base",
  xl: "h-24 w-24 text-4xl",
};

export function Avatar({ user, tamanho = "md" }: Props) {
  const classes = TAMANHOS[tamanho];

  if (user.avatar_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={user.avatar_url} alt="" className={`${classes} shrink-0 rounded-full object-cover`} />
    );
  }

  return (
    <div
      aria-hidden="true"
      className={`${classes} flex shrink-0 items-center justify-center rounded-full bg-zinc-200 font-semibold`}
    >
      {user.name[0]?.toUpperCase()}
    </div>
  );
}
