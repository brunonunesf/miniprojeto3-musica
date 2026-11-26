type Props = {
  nota: string;
  texto: string;
  aoMudarNota: (nota: string) => void;
  aoMudarTexto: (texto: string) => void;
};

const NOTAS = Array.from({ length: 11 }, (_, nota) => String(nota));

/** Nota e texto: os campos que valem tanto para criar quanto para editar uma review. */
export function CamposReview({ nota, texto, aoMudarNota, aoMudarTexto }: Props) {
  return (
    <>
      <div>
        <label htmlFor="nota" className="field-label">Nota (0 a 10)</label>
        <select id="nota" required value={nota} onChange={(e) => aoMudarNota(e.target.value)} className="field-input">
          <option value="" disabled>Escolha uma nota</option>
          {NOTAS.map((valor) => <option key={valor} value={valor}>{valor}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="texto" className="field-label">Sua análise (opcional)</label>
        <textarea id="texto" rows={6} maxLength={5000} value={texto} onChange={(e) => aoMudarTexto(e.target.value)} className="field-input resize-y" />
      </div>
    </>
  );
}
