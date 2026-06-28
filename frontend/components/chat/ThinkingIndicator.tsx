import { THINKING_STEPS } from "@/lib/constants";
import { Check, Loader2 } from "lucide-react";

interface Props {
  currentStep: number;
}

export function ThinkingIndicator({ currentStep }: Props) {
  if (currentStep < 0) return null;

  return (
    <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-muted/50 border border-border max-w-sm">
      {THINKING_STEPS.map((step, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;

        return (
          <div key={step.key} className={`flex items-center gap-2 text-sm transition-all duration-300 ${
            isCompleted ? "text-muted-foreground" :
            isCurrent ? "text-foreground font-medium" :
            "text-muted-foreground/40"
          }`}>
            <span className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              {isCompleted ? (
                <Check className="w-3.5 h-3.5 text-green-500" />
              ) : isCurrent ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-current" />
              )}
            </span>
            {step.label}
          </div>
        );
      })}
    </div>
  );
}
