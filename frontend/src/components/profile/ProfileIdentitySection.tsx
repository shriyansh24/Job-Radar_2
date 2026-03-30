import { Envelope, GithubLogo, Globe, LinkSimple, MapPin, Phone, UserCircle } from "@phosphor-icons/react";
import Input from "../ui/Input";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";
import { SettingsSection } from "../system/SettingsSection";
import type { FormState } from "./constants";
import { BRUTAL_FIELD, WORK_AUTH_OPTIONS } from "./constants";

type ProfileIdentitySectionProps = {
  isLoading: boolean;
  form: FormState;
  userEmail?: string | null;
  onUpdateField: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
};

function ProfileIdentitySection({ isLoading, form, userEmail, onUpdateField }: ProfileIdentitySectionProps) {
  return (
    <SettingsSection title="Identity and links" description="The basics that every other surface references." className="!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]">
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} variant="rect" className="h-12 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <Input label="Full name" value={form.full_name} onChange={(event) => onUpdateField("full_name", event.target.value)} placeholder="Jane Doe" icon={<UserCircle size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="Email" value={userEmail ?? ""} disabled icon={<Envelope size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="Phone" value={form.phone} onChange={(event) => onUpdateField("phone", event.target.value)} placeholder="+1 555 000 0000" icon={<Phone size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="Location" value={form.location} onChange={(event) => onUpdateField("location", event.target.value)} placeholder="New York, NY" icon={<MapPin size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="LinkedIn" value={form.linkedin_url} onChange={(event) => onUpdateField("linkedin_url", event.target.value)} placeholder="https://linkedin.com/in/..." icon={<LinkSimple size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="GitHub" value={form.github_url} onChange={(event) => onUpdateField("github_url", event.target.value)} placeholder="https://github.com/..." icon={<GithubLogo size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Input label="Portfolio" value={form.portfolio_url} onChange={(event) => onUpdateField("portfolio_url", event.target.value)} placeholder="https://..." icon={<Globe size={16} weight="bold" />} className={BRUTAL_FIELD} />
          <Select label="Work authorization" value={form.work_authorization} onChange={(event) => onUpdateField("work_authorization", event.target.value)} options={WORK_AUTH_OPTIONS} className={BRUTAL_FIELD} />
        </div>
      )}
    </SettingsSection>
  );
}

export { ProfileIdentitySection };
export type { ProfileIdentitySectionProps };
