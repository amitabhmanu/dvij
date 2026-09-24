// Concept diagrams for codex entries. An entry opts in with `diagram: <key>`
// in its frontmatter; the key must appear here. Each diagram is drawn only from
// numbers already stated in that entry (see the component's own note).
import Chakras from "./Chakras.astro";

export const DIAGRAMS: Record<string, any> = {
  chakras: Chakras,
};

export const diagramFor = (key?: string) => (key ? DIAGRAMS[key] : undefined);
