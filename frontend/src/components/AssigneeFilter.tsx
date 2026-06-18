"use client";

import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { fetchTeamMembers } from "@/lib/api";

export type AssigneeFilterValue = "" | "me" | "unassigned" | string;

type AssigneeFilterProps = {
  value: AssigneeFilterValue;
  onChange: (value: AssigneeFilterValue) => void;
};

export function AssigneeFilter({ value, onChange }: AssigneeFilterProps) {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const role = session?.user?.role ?? "";
  const canFilter = ["admin", "manager"].includes(role);

  const { data: teamMembers } = useQuery({
    queryKey: ["team-members", accessToken],
    queryFn: () => fetchTeamMembers(accessToken!),
    enabled: Boolean(accessToken) && canFilter,
  });

  if (!canFilter) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <label htmlFor="assignee-filter" className="text-sm text-zinc-600">
        Assignee
      </label>
      <select
        id="assignee-filter"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-500"
      >
        <option value="">All team members</option>
        <option value="me">Assigned to me</option>
        <option value="unassigned">Unassigned</option>
        {teamMembers?.map((member) => (
          <option key={member.id} value={String(member.id)}>
            {member.email}
          </option>
        ))}
      </select>
    </div>
  );
}
