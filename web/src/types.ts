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
  generation?: PackGenerationMeta | null;
  created_at: string;
};

export type PracticeItemSummary = {
  item_id: string;
  part_type: string;
  difficulty_level: string;
  prompt: string;
  grammar_tag: string;
  vocab_tag?: string | null;
  source: string;
  created_at: string;
};

export type ReadyPackDetail = {
  ready_pack_id: string;
  pack: QuizPack;
  generation?: PackGenerationMeta | null;
};

export type PracticeItemDetail = {
  item: ToeicPracticeItem;
  source: string;
  created_at: string;
};

export type QuizItem = {
  prompt: string;
  choices: string[];
  answer: string;
  explanation: string;
  skill_tags: string[];
};

export type QuizPack = {
  title: string;
  mode: "toeic" | "grammar" | "conversation" | "image" | "idiom";
  difficulty: "easy" | "medium" | "hard";
  items: QuizItem[];
};

export type ReadyPackLaunchResponse = {
  ready_pack_id: string;
  quiz_id: string;
  pack: QuizPack;
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

export type WorkerStatusResponse = {
  state: "running" | "stopped";
  pid?: number | null;
  poll_interval?: number | null;
  max_jobs?: number | null;
  last_exit_code?: number | null;
};

export type ProblemStats = {
  total_ready_packs: number;
  total_practice_items: number;
  practice_items_by_part: Record<string, number>;
  ready_packs_by_mode: Record<string, number>;
};

export type PackGenerationMeta = {
  strategy: string;
  validated: boolean;
  validation_errors: string[];
  harness: Record<string, unknown>;
  error?: string | null;
};

export type ProblemInventoryResponse = {
  stats: ProblemStats;
  ready_packs: ReadyQuizSummary[];
  practice_items: PracticeItemSummary[];
  active_jobs: BackgroundJob[];
  ready_pack_page: number;
  practice_item_page: number;
  page_size: number;
};

export type ProblemGenerationResponse = {
  queued_job: BackgroundJob;
  requested_pack_count: number;
};

export type HarnessCaseResult = {
  case_id: string;
  status_code: number;
  elapsed_ms: number;
  passed: boolean;
  body_preview: string;
};

export type HarnessRunResponse = {
  passed: number;
  total: number;
  results: HarnessCaseResult[];
};

export type DeleteResourceResponse = {
  deleted: boolean;
  resource_id: string;
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

export type QuizSubmitResponse = {
  quiz_id: string;
  total: number;
  correct: number;
  feedback: string[];
  score: number;
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
