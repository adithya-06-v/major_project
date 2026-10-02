import { createFileRoute } from "@tanstack/react-router";
import { GeneMindApp } from "@/components/GeneMindApp";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "GeneMindAI — AI-Driven DNA Computing Platform" },
      { name: "description", content: "Explore nucleotide sequences with k-mer encoding, Random Forest classification, and SHAP explainability." },
      { property: "og:title", content: "GeneMindAI — AI-Driven DNA Computing Platform" },
      { property: "og:description", content: "A premium genomic analysis workflow for the human HBB locus." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return <GeneMindApp />;
}
