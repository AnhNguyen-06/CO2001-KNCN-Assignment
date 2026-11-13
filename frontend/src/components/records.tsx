"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  FileSpreadsheet,
  LoaderCircle,
  Search,
  Table2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { displayDate, formatTime, initials, localDate } from "@/lib/domain";
import { useApp } from "./provider";
import { downloadRecords } from "@/lib/api";

const PAGE_SIZE = 8;

export function Records() {
  const { records, members, notify } = useApp();
  const params = useSearchParams();
  const [query, setQuery] = useState("");
  const [date, setDate] = useState("");
  const [memberId, setMemberId] = useState("");
  const [page, setPage] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [today, setToday] = useState("");
  useEffect(() => {
    setToday(localDate());
  }, []);
  useEffect(() => {
    setMemberId(params.get("member") ?? "");
    setPage(0);
  }, [params]);
  const filtered = records.filter(
    (record) =>
      (!date || record.date === date) &&
      (!memberId || record.memberId === memberId) &&
      `${record.name} ${record.memberId}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);
  const visible = filtered.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  );

  async function exportRecords() {
    setExporting(true);
    try {
      await downloadRecords({ date, memberId, query });
      notify(
        `Exported ${filtered.length} attendance record${filtered.length === 1 ? "" : "s"}.`,
      );
    } catch {
      notify("Could not export the workbook. Please try again.", "error");
    } finally {
      setExporting(false);
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="page-eyebrow">Every arrival, on record</div>
          <h1 className="luminous">A clear picture of presence.</h1>
          <p>Find a moment. Follow a day. Take your records with you.</p>
        </div>
        <button
          className="capsule primary-capsule"
          disabled={!filtered.length || exporting}
          onClick={exportRecords}
        >
          {exporting ? (
            <LoaderCircle size={14} className="spin" />
          ) : (
            <Download size={14} />
          )}
          {exporting ? "Preparing workbook…" : "Export Excel"}
        </button>
      </div>
      <div className="record-summary">
        <div>
          <span className="summary-icon">
            <Table2 size={19} strokeWidth={1.2} />
          </span>
          <span>
            <strong>{String(records.length).padStart(2, "0")}</strong> total
            check-ins
          </span>
        </div>
        <div>
          <span className="summary-icon">
            <CalendarDays size={19} strokeWidth={1.2} />
          </span>
          <span>
            <strong>
              {new Set(records.map((record) => record.date)).size
                .toString()
                .padStart(2, "0")}
            </strong>{" "}
            recorded days
          </span>
        </div>
        <span className="record-summary-note">
          <span className="mini-status-dot" /> Attendance records · saved in the
          database
        </span>
      </div>
      <section className="records-panel glass-panel">
        <div className="records-toolbar">
          <div className="search-field">
            <Search size={15} />
            <input
              aria-label="Search attendance records"
              placeholder="Search by name or ID…"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(0);
              }}
            />
          </div>
          <div className="record-filters">
            <button
              className={`filter-button ${date === today && date ? "selected" : ""}`}
              onClick={() => {
                setDate(date === today ? "" : today);
                setPage(0);
              }}
            >
              Today
            </button>
            <label className="date-filter">
              <CalendarDays size={14} />
              <input
                type="date"
                aria-label="Filter by attendance date"
                value={date}
                onChange={(event) => {
                  setDate(event.target.value);
                  setPage(0);
                }}
              />
            </label>
            {(query || date || memberId) && (
              <button
                className="text-button clear-filter"
                onClick={() => {
                  setQuery("");
                  setDate("");
                  setMemberId("");
                  setPage(0);
                }}
              >
                <X size={12} /> Clear filters
              </button>
            )}
          </div>
        </div>
        {memberId && (
          <div className="member-filter-chip">
            Showing{" "}
            {members.find((member) => member.id === memberId)?.name ?? memberId}
            <button
              aria-label="Remove member filter"
              onClick={() => setMemberId("")}
            >
              <X size={12} />
            </button>
          </div>
        )}
        <div className="table-scroll">
          <table className="records-table">
            <thead>
              <tr>
                <th>No.</th>
                <th>Member</th>
                <th>Member ID</th>
                <th>Date</th>
                <th>Check-in time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((record, index) => {
                const member = members.find(
                  (item) => item.id === record.memberId,
                );
                return (
                  <tr key={record.id}>
                    <td className="row-number">
                      {String(currentPage * PAGE_SIZE + index + 1).padStart(
                        2,
                        "0",
                      )}
                    </td>
                    <td>
                      <span className="table-member">
                        <span
                          className={`avatar avatar-${member?.color ?? "blue"}`}
                        >
                          {initials(record.name)}
                        </span>
                        {record.name}
                      </span>
                    </td>
                    <td className="mono-text">{record.memberId}</td>
                    <td>{displayDate(record.date, true)}</td>
                    <td className="mono-text">
                      {formatTime(record.recordedAt)}
                    </td>
                    <td>
                      <span className="present-label">
                        <Check size={12} /> Present
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="empty-state records-empty">
            <div className="empty-orbit">
              <FileSpreadsheet size={28} strokeWidth={1} />
              <i />
            </div>
            <h2>
              {records.length
                ? "No check-ins match just yet."
                : "Your first arrival starts the story."}
            </h2>
            <p>
              {records.length
                ? "Try a different date, name, or member ID."
                : "Turn on the camera in Attendance to record your first check-in."}
            </p>
            {records.length ? (
              <button
                className="capsule"
                onClick={() => {
                  setDate("");
                  setQuery("");
                  setMemberId("");
                }}
              >
                Clear filters
              </button>
            ) : (
              <Link className="capsule" href="/attendance">
                Go to Attendance <ChevronRight size={14} />
              </Link>
            )}
          </div>
        )}
        <div className="table-footer">
          <span>
            {filtered.length
              ? `${currentPage * PAGE_SIZE + 1}–${Math.min((currentPage + 1) * PAGE_SIZE, filtered.length)} of ${filtered.length} records`
              : "0 records"}
          </span>
          <div>
            <button
              className="icon-button"
              aria-label="Previous records page"
              disabled={currentPage === 0}
              onClick={() => setPage((value) => value - 1)}
            >
              <ChevronLeft size={16} />
            </button>
            <span>
              Page {currentPage + 1} of {totalPages}
            </span>
            <button
              className="icon-button"
              aria-label="Next records page"
              disabled={currentPage + 1 >= totalPages}
              onClick={() => setPage((value) => value + 1)}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </section>
      <div className="records-note">
        <FileSpreadsheet size={14} />
        <span>
          Excel exports include the records in your current view, with dates and
          times in UTC+07:00.
        </span>
      </div>
    </>
  );
}
