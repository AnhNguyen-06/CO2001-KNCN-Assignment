"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { Check, Info, X, AlertCircle } from "lucide-react";
import {
  AttendanceRecord,
  DEFAULT_PREFERENCES,
  ExportState,
  Member,
  Preferences,
} from "@/lib/domain";
import { api, ApiError, post } from "@/lib/api";
type Toast = { message: string; kind: "success" | "info" | "error" };
type WorkspaceData = {
  members: Member[];
  records: AttendanceRecord[];
  exports: ExportState[];
};
type Store = WorkspaceData & {
  preferences: Preferences;
  ready: boolean;
  backendError: string;
  notify: (message: string, kind?: Toast["kind"]) => void;
  refresh: (afterWrite?: boolean) => Promise<void>;
  addMember: (
    id: string,
    name: string,
    images: string[],
  ) => Promise<{ ok: boolean; message: string; code?: string }>;
  updatePreferences: (value: Partial<Preferences>) => void;
  resetPreferences: () => void;
};
const Context = createContext<Store | null>(null);
const PREFERENCES_KEY = "presence.preferences.v1";
export function AppProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<WorkspaceData>({
    members: [],
    records: [],
    exports: [],
  });
  const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);
  const [ready, setReady] = useState(false);
  const [backendError, setBackendError] = useState("");
  const [toast, setToast] = useState<Toast | null>(null);
  const pendingRefresh = useRef<Promise<void> | null>(null);
  const serviceReady = useRef(false);
  const mounted = useRef(true);
  const notify = useCallback(
    (message: string, kind: Toast["kind"] = "success") =>
      setToast({ message, kind }),
    [],
  );
  const refresh = useCallback((afterWrite = false): Promise<void> => {
    if (pendingRefresh.current)
      return afterWrite
        ? pendingRefresh.current.then(() => refresh())
        : pendingRefresh.current;
    const request = (async () => {
      try {
        const snapshot = await api<WorkspaceData>("/workspace");
        if (mounted.current) {
          setData(snapshot);
          setReady(true);
          serviceReady.current = true;
          setBackendError("");
        }
      } catch (error) {
        if (mounted.current) {
          setReady(false);
          serviceReady.current = false;
          setBackendError(
            error instanceof ApiError &&
              ["BACKEND_WAKING_UP", "BACKEND_UNAVAILABLE"].includes(error.code)
              ? "The recognition service may be waking up. This can take about a minute on free hosting. Retrying automatically."
              : error instanceof Error
                ? error.message
                : "The backend is unavailable.",
          );
        }
      } finally {
        pendingRefresh.current = null;
      }
    })();
    pendingRefresh.current = request;
    return request;
  }, []);
  useEffect(() => {
    mounted.current = true;
    try {
      const old = localStorage.getItem("presence.frontend.v1");
      const saved =
        JSON.parse(localStorage.getItem(PREFERENCES_KEY) ?? "null") ??
        (old ? JSON.parse(old).preferences : null);
      if (saved)
        setPreferences(
          Object.fromEntries(
            Object.entries(DEFAULT_PREFERENCES).map(([key, value]) => [
              key,
              typeof saved[key] === "boolean" ? saved[key] : value,
            ]),
          ) as Preferences,
        );
      localStorage.removeItem("presence.frontend.v1");
    } catch {}
    setPreferencesLoaded(true);
    void refresh();
    let timer: ReturnType<typeof setTimeout>;
    let disposed = false;
    const poll = async () => {
      if (document.visibilityState === "visible") await refresh();
      if (!disposed)
        timer = setTimeout(poll, serviceReady.current ? 15000 : 10000);
    };
    timer = setTimeout(poll, 10000);
    const visible = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      mounted.current = false;
      disposed = true;
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [refresh]);
  useEffect(() => {
    document.documentElement.dataset.reducedMotion = String(
      preferences.reduceMotion,
    );
    if (preferencesLoaded) {
      try {
        localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
      } catch {}
    }
  }, [preferences, preferencesLoaded]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 4800);
    return () => clearTimeout(timer);
  }, [toast]);
  async function addMember(id: string, name: string, images: string[]) {
    try {
      await post("/members", {
        person_id: id.trim(),
        full_name: name.trim(),
        images,
      });
      await refresh(true);
      notify(name.trim() + " is registered and ready to check in.");
      return { ok: true, message: "Member registered." };
    } catch (error) {
      await refresh();
      return {
        ok: false,
        message:
          error instanceof Error
            ? error.message
            : "Registration could not be saved.",
        code: error instanceof ApiError ? error.code : undefined,
      };
    }
  }
  return (
    <Context.Provider
      value={{
        ...data,
        preferences,
        ready,
        backendError,
        refresh,
        notify,
        addMember,
        updatePreferences: (value) =>
          setPreferences((previous) => ({ ...previous, ...value })),
        resetPreferences: () => {
          setPreferences(DEFAULT_PREFERENCES);
          notify("Preferences restored.");
        },
      }}
    >
      {children}
      {toast && (
        <div
          className={"toast toast-" + toast.kind}
          role="status"
          aria-live="polite"
        >
          {toast.kind === "success" ? (
            <Check size={18} />
          ) : toast.kind === "error" ? (
            <AlertCircle size={18} />
          ) : (
            <Info size={18} />
          )}
          <span>{toast.message}</span>
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast(null)}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </Context.Provider>
  );
}
export function useApp() {
  const value = useContext(Context);
  if (!value) throw new Error("AppProvider is required.");
  return value;
}
