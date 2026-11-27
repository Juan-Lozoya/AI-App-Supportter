import { useState } from "react";

import { useSubmitReview } from "../api/hooks";
import type { ReviewRequest, ReviewResponse } from "../api/types";
import { REVIEWER, formatDate, humanize, reviewTone } from "../lib/format";
import { Badge } from "./Badge";
import { Panel } from "./Panel";

interface ReviewPanelProps {
  analysisId: string;
  reviewStatus: ReviewResponse["review_status"];
  history: ReviewResponse["history"];
}

export function ReviewPanel({
  analysisId,
  reviewStatus,
  history,
}: ReviewPanelProps) {
  const submit = useSubmitReview(analysisId);
  const [comment, setComment] = useState("");

  function send(decision: ReviewRequest["decision"]) {
    submit.mutate(
      { decision, comment, reviewer: REVIEWER },
      { onSuccess: () => setComment("") },
    );
  }

  const base =
    "rounded-lg px-4 py-2.5 text-sm font-bold disabled:cursor-not-allowed disabled:opacity-60";

  return (
    <Panel
      title="Human Review"
      description="AI-assisted analysis requires human validation before processing."
    >
      <p className="mb-3 text-[13px]">
        Current decision:{" "}
        <Badge tone={reviewTone(reviewStatus)}>{humanize(reviewStatus)}</Badge>
      </p>

      <label className="block text-[13px] font-bold">
        Comment (optional)
        <textarea
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          className="mt-2 w-full resize-y rounded-lg border border-slate-300 p-3 text-sm font-normal focus:border-transparent focus:outline-2 focus:outline-accent"
        />
      </label>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className={`${base} bg-brand text-white hover:bg-brand-dark`}
          disabled={submit.isPending}
          onClick={() => send("approved")}
        >
          Approve
        </button>
        <button
          className={`${base} bg-brand-soft text-brand`}
          disabled={submit.isPending}
          onClick={() => send("needs_info")}
        >
          Request more info
        </button>
        <button
          className={`${base} bg-red-100 text-red-700`}
          disabled={submit.isPending}
          onClick={() => send("rejected")}
        >
          Reject
        </button>
      </div>

      {submit.error && (
        <p role="alert" className="mt-3 text-[13px] text-red-700">
          {submit.error.message}
        </p>
      )}

      {history.length > 0 && (
        <ul className="mt-5">
          {history.map((entry) => (
            <li
              key={`${entry.at}-${entry.decision}`}
              className="border-t border-[#edf0f4] py-3 text-[13px]"
            >
              <Badge tone={reviewTone(entry.decision)}>
                {humanize(entry.decision)}
              </Badge>{" "}
              <span className="text-muted">
                {entry.reviewer} · {formatDate(entry.at)}
              </span>
              {entry.comment && (
                <p className="mt-1 text-muted">{entry.comment}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
