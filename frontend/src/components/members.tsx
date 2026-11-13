"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  ArrowUpRight,
  Check,
  Fingerprint,
  Plus,
  Search,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { displayDate, initials, localDate, Member } from "@/lib/domain";
import { useApp } from "./provider";
import { Modal } from "./modal";
import { Registration } from "./registration";

export function Members() {
  const { members, records, ready } = useApp();
  const params = useSearchParams();
  const router = useRouter();
  const [registering, setRegistering] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Member | null>(null);
  const [today, setToday] = useState("");
  useEffect(() => {
    setToday(localDate());
  }, []);
  useEffect(() => {
    if (params.get("register") === "true") setRegistering(true);
  }, [params]);
  function closeRegistration() {
    setRegistering(false);
    if (params.has("register")) router.replace("/members", { scroll: false });
  }
  const filtered = members.filter((member) =>
    `${member.name} ${member.id}`.toLowerCase().includes(query.toLowerCase()),
  );
  const present = new Set(
    records
      .filter((record) => record.date === today)
      .map((record) => record.memberId),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="page-eyebrow">Your familiar faces</div>
          <h1 className="luminous">Good to know you.</h1>
          <p>A place for everyone who makes your day.</p>
        </div>
        <button
          className="capsule primary-capsule glow-capsule"
          disabled={!ready}
          onClick={() => setRegistering(true)}
        >
          <Plus size={14} /> Register member
        </button>
      </div>
      <div className="list-toolbar">
        <div className="toolbar-title">
          <Users size={16} />
          <h2>All members</h2>
          <span className="count-badge">{members.length}</span>
        </div>
        <div className="search-field">
          <Search size={15} />
          <input
            aria-label="Search members"
            placeholder="Search by name or ID…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          {query && (
            <button
              aria-label="Clear member search"
              onClick={() => setQuery("")}
            >
              ×
            </button>
          )}
        </div>
      </div>
      <div className="member-grid">
        {filtered.map((member) => (
          <button
            className="member-card glass-panel"
            key={member.id}
            onClick={() => setSelected(member)}
          >
            <div className="member-card-top">
              <span className="member-card-id">{member.id}</span>
              <ArrowUpRight size={16} />
            </div>
            <div className={`member-portrait portrait-${member.color}`}>
              <div className="portrait-ring" />
              <span>{initials(member.name)}</span>
              <i />
              <Fingerprint
                className="portrait-fingerprint"
                size={20}
                strokeWidth={1}
              />
            </div>
            <h2>{member.name}</h2>
            <p>{member.role}</p>
            <div className="member-card-bottom">
              <span>
                <ScanSample /> {member.samples} face samples
              </span>
              <span
                className={
                  present.has(member.id) ? "member-present" : "member-waiting"
                }
              >
                {present.has(member.id) ? (
                  <>
                    <i /> Present today
                  </>
                ) : (
                  "Ready to check in"
                )}
              </span>
            </div>
          </button>
        ))}
        {!query && (
          <button
            className="add-member-card"
            onClick={() => setRegistering(true)}
          >
            <span className="add-member-icon">
              <Plus size={24} strokeWidth={1} />
            </span>
            <h2>Someone new?</h2>
            <p>Make them a familiar face.</p>
            <span>
              Register member <ArrowUpRight size={13} />
            </span>
          </button>
        )}
      </div>
      {filtered.length === 0 && (
        <div className="empty-state">
          <Search size={28} strokeWidth={1} />
          <h2>No familiar faces found.</h2>
          <p>Try another name or member ID.</p>
          <button className="capsule" onClick={() => setQuery("")}>
            Clear search
          </button>
        </div>
      )}
      <div className="members-note">
        <Fingerprint size={16} />
        <span>
          Your registered identities and face embeddings are saved in the
          attendance database.
        </span>
      </div>
      {registering && <Registration onClose={closeRegistration} />}
      {selected && (
        <Modal title="Member profile" onClose={() => setSelected(null)}>
          <div className="member-detail">
            <span className={`avatar avatar-large avatar-${selected.color}`}>
              {initials(selected.name)}
            </span>
            <h3>{selected.name}</h3>
            <p>{selected.role}</p>
            <dl className="review-details">
              <div>
                <dt>Member ID</dt>
                <dd>{selected.id}</dd>
              </div>
              <div>
                <dt>Registered</dt>
                <dd>{displayDate(selected.joinedAt, true)}</dd>
              </div>
              <div>
                <dt>Profile type</dt>
                <dd>Face recognition</dd>
              </div>
              <div>
                <dt>Today’s attendance</dt>
                <dd>
                  {present.has(selected.id) ? (
                    <>
                      <Check size={14} /> Present
                    </>
                  ) : (
                    "Waiting to check in"
                  )}
                </dd>
              </div>
              <div>
                <dt>Total check-ins</dt>
                <dd>
                  {
                    records.filter((record) => record.memberId === selected.id)
                      .length
                  }
                </dd>
              </div>
            </dl>
            <Link
              href={`/records?member=${encodeURIComponent(selected.id)}`}
              className="capsule primary-capsule"
              onClick={() => setSelected(null)}
            >
              View attendance <ArrowUpRight size={14} />
            </Link>
          </div>
        </Modal>
      )}
    </>
  );
}

function ScanSample() {
  return (
    <span className="sample-dots" aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
  );
}
