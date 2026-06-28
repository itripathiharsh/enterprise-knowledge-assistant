interface Props { questions: string[]; onSelect: (q: string) => void; }

export function FollowUpSuggestions({ questions, onSelect }: Props) {
  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-xs text-muted-foreground px-1">Suggested follow-ups</p>
      {questions.map((q, i) => (
        <button key={i} onClick={() => onSelect(q)}
          className="text-left text-xs px-3 py-2 rounded-lg border border-border
                     hover:border-primary/50 hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground">
          {q}
        </button>
      ))}
    </div>
  );
}
