export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type LyricSection = {
  id: number;
  song_id: number;
  label: string;
  kind: string;
  sort_order: number;
  start_line_index: number;
  end_line_index: number;
  created_at: string;
};

export type LyricInsight = {
  id: number;
  song_id: number;
  category: string;
  text: string;
  sort_order: number;
  source: string;
  created_at: string;
};

export type DocumentsPreview = {
  visual_bible_markdown: string;
  treatment_markdown: string;
};

export type ProjectDetail = {
  id: number;
  name: string;
  created_at: string;
  song: null | {
    id: number;
    project_id: number;
    title: string | null;
    artist: string | null;
    language: string | null;
    mood: string | null;
    lyrics_text: string | null;
    target_duration_seconds: number | null;
    pacing_profile: string | null;
    audio_original_filename: string | null;
    audio_rights_confirmed: boolean;
    lyrics_rights_confirmed: boolean;
    has_audio: boolean;
    sections: LyricSection[];
    insights: LyricInsight[];
    structure_warnings: string[];
    line_timings_json?: string | null;
    creative_intake_json?: string | null;
    director_answers_json?: string | null;
    creative_routes_json?: string | null;
    selected_route_id?: string | null;
    creative_lock_at?: string | null;
    creative_lock_snapshot_json?: string | null;
    creative_locked?: boolean;
    timeline_plan_json?: string | null;
    scenes_json?: string | null;
    shots_json?: string | null;
    generation_plan_json?: string | null;
    review_matrix_json?: string | null;
    updated_at: string;
  };
};

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    let msg = res.statusText;
    if (text) {
      try {
        const j = JSON.parse(text) as { detail?: unknown };
        if (typeof j.detail === "string") msg = j.detail;
        else if (Array.isArray(j.detail)) msg = j.detail.map(String).join("; ");
        else if (j.detail != null) msg = JSON.stringify(j.detail);
        else msg = text;
      } catch {
        msg = text;
      }
    }
    throw new Error(msg);
  }
  return JSON.parse(text) as T;
}

export async function createProject(name: string): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return parseJson<ProjectDetail>(res);
}

export async function getProject(id: number): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects/${id}`, { cache: "no-store" });
  return parseJson<ProjectDetail>(res);
}

export async function patchSong(
  projectId: number,
  body: {
    title?: string | null;
    artist?: string | null;
    language?: string | null;
    mood?: string | null;
    lyrics_text?: string | null;
    target_duration_seconds?: number | null;
    pacing_profile?: string | null;
    audio_rights_confirmed?: boolean;
    lyrics_rights_confirmed?: boolean;
    line_timings_json?: string | null;
    creative_intake_json?: string | null;
    director_answers_json?: string | null;
    creative_routes_json?: string | null;
    selected_route_id?: string | null;
    timeline_plan_json?: string | null;
    scenes_json?: string | null;
    shots_json?: string | null;
    generation_plan_json?: string | null;
    review_matrix_json?: string | null;
  },
): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<ProjectDetail>(res);
}

export async function uploadAudio(projectId: number, file: File): Promise<ProjectDetail> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/audio`, {
    method: "POST",
    body: fd,
  });
  return parseJson<ProjectDetail>(res);
}

export async function enqueueAnalysis(
  projectId: number,
): Promise<{ status: string; message: string; recommendations?: string[] }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/analysis/enqueue`, { method: "POST" });
  return parseJson(res);
}

export async function getLyricLines(projectId: number): Promise<{ lines: { index: number; text: string }[] }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/lines`, { cache: "no-store" });
  return parseJson(res);
}

export async function createLyricSection(
  projectId: number,
  body: { label: string; kind: string; start_line_index: number; end_line_index: number },
): Promise<LyricSection> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/sections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<LyricSection>(res);
}

export async function patchLyricSection(
  projectId: number,
  sectionId: number,
  body: {
    label?: string;
    kind?: string;
    start_line_index?: number;
    end_line_index?: number;
    sort_order?: number;
  },
): Promise<LyricSection> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/sections/${sectionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<LyricSection>(res);
}

export async function reorderLyricSections(projectId: number, sectionIds: number[]): Promise<LyricSection[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/sections/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ section_ids: sectionIds }),
  });
  return parseJson<LyricSection[]>(res);
}

export async function deleteLyricSection(projectId: number, sectionId: number): Promise<LyricSection> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/sections/${sectionId}`, {
    method: "DELETE",
  });
  return parseJson<LyricSection>(res);
}

export async function generateLyricInsights(
  projectId: number,
  body: { mode?: "auto" | "heuristic" | "llm"; replace?: boolean } = {},
): Promise<{ created_count: number; engine: string; note: string | null }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/insights/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson(res);
}

export async function createLyricInsight(
  projectId: number,
  body: { category: string; text: string },
): Promise<LyricInsight> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/insights`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<LyricInsight>(res);
}

export async function patchLyricInsight(
  projectId: number,
  insightId: number,
  body: { category?: string; text?: string; sort_order?: number },
): Promise<LyricInsight> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/insights/${insightId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<LyricInsight>(res);
}

export async function deleteLyricInsight(projectId: number, insightId: number): Promise<LyricInsight> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/insights/${insightId}`, {
    method: "DELETE",
  });
  return parseJson<LyricInsight>(res);
}

export async function lockCreative(projectId: number): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/creative/lock`, { method: "POST" });
  return parseJson<ProjectDetail>(res);
}

export async function unlockCreative(projectId: number): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/creative/unlock`, { method: "POST" });
  return parseJson<ProjectDetail>(res);
}

export async function getDocumentsPreview(projectId: number): Promise<DocumentsPreview> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/documents/preview`, { cache: "no-store" });
  return parseJson<DocumentsPreview>(res);
}

export async function reorderLyricInsights(projectId: number, insightIds: number[]): Promise<LyricInsight[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/song/insights/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ insight_ids: insightIds }),
  });
  return parseJson<LyricInsight[]>(res);
}
