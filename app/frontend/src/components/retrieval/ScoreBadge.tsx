interface ScoreBadgeProps {
  score: number;
  showBar?: boolean;
}

/**
 * Convert L2 distance to a display percentage.
 * L2 distance: 0 = perfect match, higher = worse match
 * We use an exponential decay to map to 0-100%:
 * - score 0 → 100%
 * - score 0.5 → ~78%
 * - score 1.0 → ~61%
 * - score 1.5 → ~47%
 * - score 2.0 → ~37%
 */
function scoreToPercentage(score: number): number {
  // Exponential decay: percentage = 100 * e^(-0.5 * score)
  const percentage = 100 * Math.exp(-0.5 * score);
  return Math.max(0, Math.min(100, percentage));
}

function getScoreColor(percentage: number): string {
  if (percentage >= 60) return 'bg-green-500';
  if (percentage >= 40) return 'bg-yellow-500';
  return 'bg-red-500';
}

/**
 * Displays a similarity score with optional progress bar.
 * Lower FAISS L2 distance = better match.
 */
export function ScoreBadge({ score, showBar = true }: Readonly<ScoreBadgeProps>) {
  const percentage = scoreToPercentage(score);
  const color = getScoreColor(percentage);

  if (!showBar) {
    return (
      <span className="text-xs text-muted-foreground font-mono">
        {score.toFixed(4)}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${percentage}%` }} />
      </div>
      <span className="text-xs text-muted-foreground w-12">{score.toFixed(3)}</span>
    </div>
  );
}
