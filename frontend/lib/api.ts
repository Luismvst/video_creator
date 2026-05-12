const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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
    audio_original_filename: string | null;
    audio_rights_confirmed: boolean;
    has_audio: boolean;
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
    audio_rights_confirmed?: boolean;
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

export async function enqueueAnalysis(projectId: number): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/analysis/enqueue`, { method: "POST" });
  return parseJson(res);
}
