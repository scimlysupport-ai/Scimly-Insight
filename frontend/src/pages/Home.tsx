import { Link } from "react-router-dom";
import AuthStatus from "../components/AuthStatus";

export default function Home() {
  return (
    <div className="min-h-screen bg-scimly-bg text-scimly-text font-body relative flex flex-col justify-between">
      
      {/* Decorative Radial Background Glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-scimly-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] bg-scimly-accent/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="relative z-10 w-full max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-scimly-primary to-scimly-accent flex items-center justify-center shadow-lg shadow-scimly-primary/20">
            <span className="font-display font-black text-white text-lg">S</span>
          </div>
          <div className="flex flex-col">
            <span className="font-display font-bold text-xl tracking-tight leading-none text-white">Scimly Insight</span>
            <span className="text-[10px] text-scimly-accent font-semibold tracking-wider uppercase mt-1">SaaS Platform</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 bg-scimly-surface/60 backdrop-blur-md border border-scimly-border/80 px-3.5 py-1.5 rounded-full text-[11px] font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-scimly-accent animate-pulse" />
            <span className="text-scimly-muted">Service Status:</span>
            <span className="text-scimly-accent font-semibold">Online & Secure</span>
          </div>
          <AuthStatus />
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center max-w-5xl mx-auto px-6 py-12 text-center gap-12">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-scimly-accent/10 border border-scimly-accent/20 text-xs font-semibold text-scimly-accent">
            ✨ Collaborative Access Governance & Analytics
          </div>
          <h1 className="font-display text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.1] max-w-4xl">
            Transform Access Reviews into <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-scimly-primary via-blue-400 to-scimly-accent bg-clip-text text-transparent">
              Collaborative Dashboards
            </span>
          </h1>
          <p className="text-scimly-muted text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
            Upload CSV datasets to visualize user permissions, create secure workspaces, delegate reviewer roles, schedule refreshes, and track SOC 2 audit logs in real-time.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
          <Link
            to="/upload"
            className="w-full sm:w-auto bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-sm px-8 py-3.5 rounded-xl hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-scimly-primary/25 transition-all"
          >
            Create Dashboard →
          </Link>
          <Link
            to="/dashboards"
            className="w-full sm:w-auto bg-scimly-surface/60 backdrop-blur-md border border-scimly-border hover:bg-scimly-surface hover:text-white text-scimly-text font-medium text-sm px-8 py-3.5 rounded-xl transition-all"
          >
            Go to My Dashboards
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid gap-6 md:grid-cols-3 w-full mt-6">
          
          {/* Card 1 */}
          <div className="group rounded-2xl border border-scimly-border/70 bg-scimly-surface/40 hover:bg-scimly-surface/60 backdrop-blur-md p-6 text-left transition-all duration-300 hover:translate-y-[-2px] hover:border-scimly-primary/30">
            <div className="h-10 w-10 rounded-xl bg-scimly-primary/10 border border-scimly-primary/20 flex items-center justify-center mb-4 text-scimly-primary group-hover:bg-scimly-primary group-hover:text-white transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94-3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
              </svg>
            </div>
            <h3 className="font-display font-semibold text-base text-white mb-2">Global Collaboration</h3>
            <p className="text-xs text-scimly-muted leading-relaxed">
              Create teams and delegate access controls. Assign roles (Admin, Editor, Viewer) to govern who can modify dashboard views.
            </p>
          </div>

          {/* Card 2 */}
          <div className="group rounded-2xl border border-scimly-border/70 bg-scimly-surface/40 hover:bg-scimly-surface/60 backdrop-blur-md p-6 text-left transition-all duration-300 hover:translate-y-[-2px] hover:border-scimly-primary/30">
            <div className="h-10 w-10 rounded-xl bg-scimly-primary/10 border border-scimly-primary/20 flex items-center justify-center mb-4 text-scimly-primary group-hover:bg-scimly-primary group-hover:text-white transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
              </svg>
            </div>
            <h3 className="font-display font-semibold text-base text-white mb-2">Auditor Sharing Links</h3>
            <p className="text-xs text-scimly-muted leading-relaxed">
              Generate read-only shared links to present access audits directly to external regulators and SOC 2 compliance consultants.
            </p>
          </div>

          {/* Card 3 */}
          <div className="group rounded-2xl border border-scimly-border/70 bg-scimly-surface/40 hover:bg-scimly-surface/60 backdrop-blur-md p-6 text-left transition-all duration-300 hover:translate-y-[-2px] hover:border-scimly-primary/30">
            <div className="h-10 w-10 rounded-xl bg-scimly-primary/10 border border-scimly-primary/20 flex items-center justify-center mb-4 text-scimly-primary group-hover:bg-scimly-primary group-hover:text-white transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a9.04 9.04 0 01-1.807 1.43 1.809 1.809 0 01-2.44 0 9.04 9.04 0 01-1.807-1.43m0 0a9.001 9.001 0 011.807-13.115 9.037 9.037 0 012.44 0 9.001 9.001 0 011.807 13.115zm-6.378-4.5A9.003 9.003 0 0012 21a9.003 9.003 0 006.741-2.968" />
              </svg>
            </div>
            <h3 className="font-display font-semibold text-base text-white mb-2">Alerts & Cron Refreshes</h3>
            <p className="text-xs text-scimly-muted leading-relaxed">
              Schedule automated dataset refreshes and set custom threshold triggers to alert your team when unauthorized privileges arise.
            </p>
          </div>

        </div>

        {/* Pricing Tiers Section */}
        <div className="w-full mt-10 space-y-8 pt-10 border-t border-scimly-border/40">
          <div className="text-center space-y-2">
            <h2 className="font-display text-2xl sm:text-3xl font-bold text-white">Simple, Transparent Pricing</h2>
            <p className="text-xs sm:text-sm text-scimly-muted max-w-lg mx-auto">
              Get started with our free tier and upgrade as your compliance and audit review team grows.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3 w-full max-w-5xl mx-auto">
            
            {/* Free Plan */}
            <div className="rounded-2xl border border-scimly-border/80 bg-scimly-surface/30 p-6 flex flex-col justify-between text-left transition-all hover:border-scimly-border">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-scimly-muted">Free Plan</h4>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className="text-3xl font-extrabold text-white">$0</span>
                    <span className="text-xs text-scimly-muted">/ month</span>
                  </div>
                  <p className="text-xs text-scimly-muted mt-2">For individuals and trial purposes.</p>
                </div>
                <ul className="space-y-2 text-xs">
                  <li className="flex items-center gap-2">✓ 1 Active Workspace</li>
                  <li className="flex items-center gap-2">✓ Up to 10MB dataset files</li>
                  <li className="flex items-center gap-2">✓ 3 Saved Dashboards</li>
                  <li className="flex items-center gap-2 text-scimly-muted/50">✗ No Team Collaboration</li>
                  <li className="flex items-center gap-2 text-scimly-muted/50">✗ No Scheduled Syncs</li>
                </ul>
              </div>
              <Link to="/upload" className="w-full text-center mt-6 text-xs px-4 py-2.5 rounded-lg border border-scimly-border text-white hover:bg-scimly-surface/60 transition-all font-medium">
                Get Started Free
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="rounded-2xl border-2 border-scimly-primary bg-scimly-surface/40 p-6 flex flex-col justify-between text-left relative transition-all shadow-lg shadow-scimly-primary/5">
              <div className="absolute top-0 right-6 transform -translate-y-1/2 bg-scimly-primary text-scimly-bg text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded">Popular</div>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-scimly-primary">Pro Plan</h4>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className="text-3xl font-extrabold text-white">$49</span>
                    <span className="text-xs text-scimly-muted">/ month</span>
                  </div>
                  <p className="text-xs text-scimly-muted mt-2">For independent security auditors.</p>
                </div>
                <ul className="space-y-2 text-xs">
                  <li className="flex items-center gap-2">✓ Unlimited Uploads (up to 50MB)</li>
                  <li className="flex items-center gap-2">✓ Unlimited Saved Dashboards</li>
                  <li className="flex items-center gap-2">✓ Custom PDF & PNG Exporting</li>
                  <li className="flex items-center gap-2">✓ Secure Read-Only Auditor Links</li>
                  <li className="flex items-center gap-2 text-scimly-muted/50">✗ No Multi-User Teams</li>
                </ul>
              </div>
              <Link to="/upload" className="w-full text-center mt-6 text-xs px-4 py-2.5 rounded-lg bg-scimly-primary text-scimly-bg hover:scale-[1.01] transition-all font-semibold">
                Upgrade to Pro
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="rounded-2xl border border-scimly-border/80 bg-scimly-surface/30 p-6 flex flex-col justify-between text-left transition-all hover:border-scimly-border">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-scimly-accent">Enterprise Plan</h4>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className="text-3xl font-extrabold text-white">$199</span>
                    <span className="text-xs text-scimly-muted">/ month</span>
                  </div>
                  <p className="text-xs text-scimly-muted mt-2">For team-wide security governance.</p>
                </div>
                <ul className="space-y-2 text-xs">
                  <li className="flex items-center gap-2">✓ Unlimited Teams & Members</li>
                  <li className="flex items-center gap-2">✓ Role Access Controls (Admin/Viewer)</li>
                  <li className="flex items-center gap-2">✓ Real-time Threshold Alerts</li>
                  <li className="flex items-center gap-2">✓ Full Activity Audit Logs (SOC 2)</li>
                  <li className="flex items-center gap-2">✓ Priority Datasets (up to 1GB)</li>
                </ul>
              </div>
              <Link to="/enterprise" className="w-full text-center mt-6 text-xs px-4 py-2.5 rounded-lg border border-scimly-border text-white hover:bg-scimly-surface/60 transition-all font-medium">
                Access Enterprise Suite
              </Link>
            </div>

          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-6xl mx-auto px-6 py-8 border-t border-scimly-border/40 text-center flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-scimly-muted">
        <div>© 2026 Scimly Insight. Runs securely in the cloud. Built for enterprise efficiency.</div>
        <div className="flex gap-4">
          <Link to="/enterprise" className="hover:text-scimly-primary transition-colors">Enterprise Suite</Link>
          <span className="text-scimly-border">•</span>
          <Link to="/dashboards" className="hover:text-scimly-primary transition-colors">My Gallery</Link>
        </div>
      </footer>

    </div>
  );
}
