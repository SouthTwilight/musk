import api from "@/core/api";

export interface ModuleInfo {
  name: string;
  display_name: string;
  icon: string;
  description: string;
  menu_order: number;
  url_prefix: string;
  version: string;
}

export async function fetchModules(): Promise<ModuleInfo[]> {
  try {
    const { data } = await api.get("/modules/");
    return data;
  } catch {
    return [];
  }
}
