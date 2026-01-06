import {
  Target,
  AlertTriangle,
  XCircle,
  Award,
  Lightbulb,
  Brain
} from "lucide-react";

/* ---------------- COMMON ---------------- */
const Score = ({ value, label }) => (
  <div className="p-6 rounded-xl bg-secondary/50 text-center">
    <p className="text-4xl font-bold">{Number(value || 0).toFixed(0)}%</p>
    <p className="text-sm text-muted-foreground mt-1">{label}</p>
  </div>
);

const Section = ({ title, children }) => (
  <div>
    <h4 className="font-semibold mb-2">{title}</h4>
    {children}
  </div>
);

/* ---------------- SEMANTIC ---------------- */
const SemanticResult = ({ data }) => (
  <div className="space-y-6">
    <Score value={data.semantic_match_score} label="Semantic Match Score" />

    <div className="p-4 rounded-xl bg-secondary/50">
      <p className="text-sm text-muted-foreground">Verdict</p>
      <p className="font-semibold">{data.verdict}</p>
    </div>

    {data.missing_skills?.length > 0 && (
      <Section title="Missing Skills">
        <ul className="list-disc ml-6">
          {data.missing_skills.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      </Section>
    )}

    {data.missing_responsibilities?.length > 0 && (
      <Section title="Missing Responsibilities">
        <ul className="space-y-1">
          {data.missing_responsibilities.map((r, i) => (
            <li key={i} className="flex gap-2">
              <XCircle className="h-4 w-4 text-destructive" /> {r}
            </li>
          ))}
        </ul>
      </Section>
    )}
  </div>
);

/* ---------------- QUALITY ---------------- */
const QualityResult = ({ data }) => (
  <div className="space-y-6">
    <Score value={data.resume_score} label="ATS Resume Score" />

    <div className="grid grid-cols-2 gap-4">
      <Score value={data.section_completeness} label="Section Completeness" />
      <Score value={data.grammar_quality} label="Grammar Quality" />
      <Score value={data.bullet_quality} label="Bullet Quality" />
      <Score value={data.skill_structure} label="Skill Structure" />
      <Score value={data.formatting_quality} label="Formatting Quality" />
    </div>

    <div className="p-4 bg-secondary/50 rounded-xl">
      <p className="font-semibold">Interpretation</p>
      <p className="text-sm text-muted-foreground">{data.interpretation}</p>
    </div>
  </div>
);

/* ---------------- IMPROVEMENT ---------------- */
const ImprovementResult = ({ data }) => (
  <div className="space-y-6">
    {data.skill_gap_suggestions?.length > 0 && (
      <Section title="Skill Gap Suggestions">
        <ul className="list-disc ml-6">
          {data.skill_gap_suggestions.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      </Section>
    )}

    {data.grammar_tips?.length > 0 && (
      <Section title="Grammar Tips">
        <ul className="list-disc ml-6">
          {data.grammar_tips.map((t, i) => <li key={i}>{t}</li>)}
        </ul>
      </Section>
    )}

    {data.skill_section_tips?.length > 0 && (
      <Section title="Skill Section Tips">
        <ul className="list-disc ml-6">
          {data.skill_section_tips.map((t, i) => <li key={i}>{t}</li>)}
        </ul>
      </Section>
    )}
  </div>
);

/* ---------------- ML ---------------- */
const MLResult = ({ data }) => (
  <div className="space-y-6">
    <Score value={data.ml_resume_score} label="ML Predicted Score" />
  </div>
);

/* ---------------- MAIN CARD ---------------- */
const ResultCard = ({ type, data, isLoading }) => {
  if (isLoading) return <div className="card-elevated p-8">Loading…</div>;
  if (!data) return null;
  if (data.error) return <div className="card-elevated p-6 text-destructive">{data.error}</div>;

  return (
    <div className="card-elevated p-8">
      {type === "semantic" && <SemanticResult data={data} />}
      {type === "quality" && <QualityResult data={data} />}
      {type === "improve" && <ImprovementResult data={data} />}
      {type === "ml" && <MLResult data={data} />}
    </div>
  );
};

export default ResultCard;
