/** O backend envia horários em UTC sem o sufixo de fuso. */
function lerDataUtc(iso: string): Date {
  return new Date(/(Z|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`);
}

export function tempoRelativo(iso: string, agora = Date.now()): string {
  const data = lerDataUtc(iso);
  const minutos = Math.floor((agora - data.getTime()) / 60_000);
  if (minutos < 1) return "agora";
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) return `há ${horas} h`;
  const dias = Math.floor(horas / 24);
  if (dias < 7) return `há ${dias} ${dias === 1 ? "dia" : "dias"}`;
  return data.toLocaleDateString("pt-BR");
}
