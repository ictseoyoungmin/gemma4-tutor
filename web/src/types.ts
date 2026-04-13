export type DashboardOverview = {
  user_id: string;
  memory_count: number;
  quiz_count: number;
  attempts_count: number;
  average_score: number;
};

export type SkillSnapshot = {
  skill_name: string;
  score: number;
  delta: number;
  evidence_count: number;
};

export type AchievementCard = {
  achievement_id: string;
  title: string;
  description: string;
  unlocked: boolean;
  unlocked_at?: string | null;
};

export type ReadyQuizSummary = {
  ready_pack_id: string;
  title: string;
  mode: string;
  difficulty: string;
  created_at: string;
};

export type BackgroundJob = {
  job_id: string;
  user_id: string;
  job_type: string;
  status: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DashboardDetail = {
  overview: DashboardOverview;
  skill_snapshots: SkillSnapshot[];
  achievements: AchievementCard[];
  ready_packs: ReadyQuizSummary[];
  active_jobs: BackgroundJob[];
  roadmap_placeholders: string[];
};

export type TutorResponse = {
  message: string;
  detected_intent: "chat" | "quiz_request" | "analysis" | "memory_update" | "image_learning";
  memory_to_store: {
    memory_id: string;
    category: string;
    content: string;
    confidence: number;
    created_at: string;
  }[];
  suggested_next_actions: string[];
};

export type ChatResponse = {
  session_id: string;
  run_id: string;
  output: TutorResponse;
  usage: Record<string, unknown>;
};

export type ToeicPracticeItem = {
  item_id: string;
  part_type: "part5";
  difficulty_level: "easy" | "medium" | "hard";
  question_text: string;
  prompt: string;
  options: string[];
  correct_option: string;
  explanation: string;
  grammar_tag: string;
  vocab_tag?: string | null;
  validated: boolean;
  validation_score: number;
};

export type ToeicNextResponse = {
  item: ToeicPracticeItem;
  recommended_difficulty: "easy" | "medium" | "hard";
  weak_tags: string[];
  recent_accuracy: number;
};

export type ToeicAnswerResponse = {
  item_id: string;
  correct: boolean;
  correct_option: string;
  explanation: string;
  grammar_tag: string;
  vocab_tag?: string | null;
  weak_tags: string[];
  recommended_difficulty: "easy" | "medium" | "hard";
  recent_accuracy: number;
};
