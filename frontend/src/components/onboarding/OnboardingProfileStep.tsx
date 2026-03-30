import { CurrencyDollar, Key, MapPin, MagnifyingGlass, UserCircle } from "@phosphor-icons/react";
import Input from "../ui/Input";
import Select from "../ui/Select";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";

export function OnboardingProfileStep({
  fullName,
  location,
  salaryMin,
  salaryMax,
  preferredJobTypes,
  preferredRemoteTypes,
  onChange,
}: {
  fullName: string;
  location: string;
  salaryMin: string;
  salaryMax: string;
  preferredJobTypes: string[];
  preferredRemoteTypes: string[];
  onChange: (patch: Partial<Record<string, string | string[]>>) => void;
}) {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Profile"
        description="Set the identity, role mix, and pay floor that the workspace should use."
      />
      <div className="grid gap-4 md:grid-cols-2">
        <Input
          label="Full name"
          value={fullName}
          onChange={(event) => onChange({ fullName: event.target.value })}
          placeholder="Jane Doe"
          icon={<UserCircle size={16} weight="bold" />}
        />
        <Input
          label="Location"
          value={location}
          onChange={(event) => onChange({ location: event.target.value })}
          placeholder="New York, NY"
          icon={<MapPin size={16} weight="bold" />}
        />
        <Select
          label="Preferred job types"
          value={preferredJobTypes[0] ?? ""}
          onChange={(event) => onChange({ preferredJobTypes: event.target.value ? [event.target.value] : [] })}
          options={[
            { value: "full_time", label: "Full-time" },
            { value: "part_time", label: "Part-time" },
            { value: "contract", label: "Contract" },
            { value: "freelance", label: "Freelance" },
            { value: "internship", label: "Internship" },
          ]}
          placeholder="Select a primary job type"
        />
        <Select
          label="Preferred remote type"
          value={preferredRemoteTypes[0] ?? ""}
          onChange={(event) => onChange({ preferredRemoteTypes: event.target.value ? [event.target.value] : [] })}
          options={[
            { value: "remote", label: "Remote" },
            { value: "hybrid", label: "Hybrid" },
            { value: "onsite", label: "On-site" },
          ]}
          placeholder="Select a primary remote type"
        />
        <Input
          label="Salary minimum"
          type="number"
          value={salaryMin}
          onChange={(event) => onChange({ salaryMin: event.target.value })}
          icon={<CurrencyDollar size={16} weight="bold" />}
        />
        <Input
          label="Salary maximum"
          type="number"
          value={salaryMax}
          onChange={(event) => onChange({ salaryMax: event.target.value })}
          icon={<CurrencyDollar size={16} weight="bold" />}
        />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <StateBlock
          tone="muted"
          icon={<UserCircle size={18} weight="bold" />}
          title="Profile"
          description="The identity and salary frame behind every match."
        />
        <StateBlock
          tone="warning"
          icon={<MagnifyingGlass size={18} weight="bold" />}
          title="Search seeds"
          description="The queries, locations, and watchlist that shape the feed."
        />
        <StateBlock
          tone="success"
          icon={<Key size={18} weight="bold" />}
          title="Integrations"
          description="Optional engines that broaden search and drafting."
        />
      </div>
    </div>
  );
}
