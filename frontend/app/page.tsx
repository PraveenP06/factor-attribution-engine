import Link from "next/link";

const projects = [
  {
    title: "Factor Attribution Engine",
    description:
      "Decomposes stock and portfolio returns into systematic factor exposures using Fama-French and Carhart models. Answers: did this go up because it's good, or because it's a leveraged market bet?",
    tags: ["Python", "FastAPI", "statsmodels", "Fama-French", "Newey-West HAC"],
    href: "/factor-attribution",
    status: "live",
  },
];

export default function Home() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16">
      <header className="mb-16">
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Praveen Patibandla</h1>
        <p className="text-slate-400 text-sm">
          Software engineer · Georgia Tech · ppatibandla3@gatech.edu
        </p>
        <div className="flex gap-4 mt-4 text-xs text-slate-500">
          <a
            href="https://github.com"
            className="hover:text-slate-300 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            github
          </a>
          <a href="mailto:ppatibandla3@gatech.edu" className="hover:text-slate-300 transition-colors">
            email
          </a>
        </div>
      </header>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-slate-500 mb-6">Projects</h2>
        <div className="flex flex-col gap-4">
          {projects.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              className="block border border-[#2a2d3e] rounded-lg p-5 hover:border-indigo-500/50 hover:bg-[#1a1d2e] transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-slate-100 font-semibold group-hover:text-indigo-400 transition-colors">
                  {p.title}
                </h3>
                {p.status === "live" && (
                  <span className="flex items-center gap-1 text-xs text-emerald-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                    live
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-sm leading-relaxed mb-3">{p.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {p.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-0.5 rounded bg-[#0f1117] border border-[#2a2d3e] text-slate-500"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
