export function MensagemErro({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-lg border border-erro-borda bg-erro-fundo p-2 text-sm text-erro-texto">
      {children}
    </p>
  );
}
