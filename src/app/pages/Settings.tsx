import React from "react";
import { User, Bell, Palette, Shield, Plug, HardDrive } from "lucide-react";
import { useTheme, Theme, Mode } from "../theme-provider";

export function Settings() {
  const { theme, setTheme, mode, setMode } = useTheme();

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <p className="command-label mb-1">Operations</p>
          <h2 className="font-headline text-3xl font-black uppercase tracking-tight">System Settings</h2>
        </div>
        <button className="hard-press border-2 border-border bg-primary px-5 py-2.5 font-mono text-[11px] font-bold uppercase tracking-widest text-primary-foreground hover:bg-primary/90 transition-colors">
          Save Configuration
        </button>
      </div>

      <div className="flex flex-col md:flex-row gap-8 flex-1">
        {/* Settings Navigation */}
        <div className="w-full md:w-64 shrink-0 space-y-1">
          {[
            { id: "profile", label: "Profile", icon: User, active: true },
            { id: "appearance", label: "Appearance", icon: Palette },
            { id: "notifications", label: "Notifications", icon: Bell },
            { id: "security", label: "Security", icon: Shield },
            { id: "integrations", label: "Integrations", icon: Plug },
            { id: "data", label: "Data & Export", icon: HardDrive },
          ].map((item) => (
            <button
              key={item.id}
              className={`flex w-full items-center gap-3 border-2 px-4 py-3 text-left font-mono text-[11px] font-bold uppercase tracking-widest transition-colors hard-press ${
                item.active
                  ? "border-border bg-primary text-primary-foreground"
                  : "border-transparent text-foreground hover:border-border hover:bg-card"
              }`}
            >
              <item.icon size={16} />
              {item.label}
            </button>
          ))}
        </div>

        {/* Settings Content */}
        <div className="flex-1 space-y-8 pb-12">
          {/* Section: Profile */}
          <section className="border-2 border-border bg-card shadow-hard-xl">
            <div className="border-b-2 border-border bg-muted p-4">
              <h3 className="font-headline font-bold uppercase tracking-tight text-lg">Operator Profile</h3>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-6">
                <div className="flex size-24 shrink-0 items-center justify-center border-2 border-border bg-secondary text-2xl font-black">
                  JR
                </div>
                <div className="space-y-2">
                  <button className="hard-press border-2 border-border bg-background px-4 py-2 font-mono text-[10px] font-bold uppercase tracking-widest">
                    Change Avatar
                  </button>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    JPG, GIF or PNG. Max size 2MB.
                  </p>
                </div>
              </div>

              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="command-label text-[10px]">First Name</label>
                  <input
                    type="text"
                    defaultValue="Admin"
                    className="w-full border-2 border-border bg-background px-4 py-2.5 font-mono text-sm outline-none focus:border-primary focus:ring-0"
                  />
                </div>
                <div className="space-y-2">
                  <label className="command-label text-[10px]">Last Name</label>
                  <input
                    type="text"
                    defaultValue="User"
                    className="w-full border-2 border-border bg-background px-4 py-2.5 font-mono text-sm outline-none focus:border-primary focus:ring-0"
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <label className="command-label text-[10px]">Email Address</label>
                  <input
                    type="email"
                    defaultValue="admin@jobradar.local"
                    className="w-full border-2 border-border bg-background px-4 py-2.5 font-mono text-sm outline-none focus:border-primary focus:ring-0"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Section: Appearance */}
          <section className="border-2 border-border bg-card shadow-hard-xl" id="appearance">
            <div className="border-b-2 border-border bg-muted p-4">
              <h3 className="font-headline font-bold uppercase tracking-tight text-lg">Appearance</h3>
            </div>
            <div className="p-6 space-y-8">
              <div className="space-y-4">
                <div>
                  <h4 className="font-bold uppercase tracking-wide">Interface Mode</h4>
                  <p className="font-mono text-[10px] text-muted-foreground uppercase mt-1">
                    Select your preferred illumination level
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {(["light", "dark"] as Mode[]).map((m) => (
                    <button
                      key={m}
                      onClick={() => setMode(m)}
                      className={`hard-press flex items-center justify-center border-2 p-4 font-mono text-[11px] font-bold uppercase tracking-widest transition-colors ${
                        mode === m
                          ? "border-border bg-primary text-primary-foreground"
                          : "border-border bg-background text-foreground hover:bg-muted"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-bold uppercase tracking-wide">Color System</h4>
                  <p className="font-mono text-[10px] text-muted-foreground uppercase mt-1">
                    Select a core visual identity
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { id: "default", label: "Default (Base)" },
                    { id: "terminal", label: "Terminal (High Contrast)" },
                    { id: "blueprint", label: "Industrial Blueprint" },
                    { id: "phosphor", label: "Phosphor (Retro)" },
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id as Theme)}
                      className={`hard-press flex flex-col items-start border-2 p-4 text-left transition-colors ${
                        theme === t.id
                          ? "border-border bg-primary text-primary-foreground"
                          : "border-border bg-background text-foreground hover:bg-muted"
                      }`}
                    >
                      <span className="font-mono text-[11px] font-bold uppercase tracking-widest">{t.label}</span>
                      <span className={`mt-2 h-2 w-8 border-2 border-current ${theme === t.id ? "bg-primary-foreground" : "bg-primary"}`} />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Section: Preferences */}
          <section className="border-2 border-border bg-card shadow-hard-xl">
            <div className="border-b-2 border-border bg-muted p-4">
              <h3 className="font-headline font-bold uppercase tracking-tight text-lg">System Preferences</h3>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex items-center justify-between border-2 border-border p-4">
                <div>
                  <h4 className="font-bold uppercase tracking-wide">Developer Mode</h4>
                  <p className="font-mono text-[10px] text-muted-foreground uppercase mt-1">
                    Enable advanced logging and debugging tools
                  </p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center border-2 border-border bg-primary px-0.5">
                  <span className="inline-block size-4 translate-x-5 transform bg-primary-foreground transition-transform"></span>
                </button>
              </div>

              <div className="flex items-center justify-between border-2 border-border p-4">
                <div>
                  <h4 className="font-bold uppercase tracking-wide">Compact View</h4>
                  <p className="font-mono text-[10px] text-muted-foreground uppercase mt-1">
                    Decrease padding across all data tables
                  </p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center border-2 border-border bg-muted px-0.5">
                  <span className="inline-block size-4 translate-x-0 transform bg-foreground transition-transform"></span>
                </button>
              </div>
            </div>
          </section>

          <section className="border-2 border-red-500/50 bg-red-500/10 shadow-hard-xl">
            <div className="p-6">
              <h3 className="font-headline font-black uppercase tracking-tight text-red-500 mb-2">Danger Zone</h3>
              <p className="font-mono text-xs text-red-500/80 mb-4">
                Once you delete your account, there is no going back. Please be certain.
              </p>
              <button className="hard-press border-2 border-red-500 bg-red-500 text-white px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-widest">
                Delete Account
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}