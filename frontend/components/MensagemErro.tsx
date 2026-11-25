export function MensagemErro({ children }: { children: string }) {
  return <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{children}</p>;
}
