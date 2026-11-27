import { Link } from "@tanstack/react-router";

const item = "block rounded-lg p-3.5 text-slate-300";
const active = { className: "bg-navy-2 text-white" };

// Estas secciones todavía no tienen endpoints ni rutas.
const upcoming = ["All Events", "Pending Review", "Reports", "Settings"];

export function Sidebar() {
  return (
    <>
      <aside className="fixed inset-y-0 left-0 hidden w-60 bg-navy px-[18px] py-6 text-white md:block">
        <div className="mb-10 text-[19px] font-bold">
          Corporate <span className="text-accent">Actions</span>
        </div>
        <nav aria-label="Main" className="flex flex-col gap-2">
          <Link
            to="/"
            activeOptions={{ exact: true }}
            activeProps={active}
            className={`${item} hover:bg-navy-2`}
          >
            Dashboard
          </Link>
          <Link
            to="/analyses/new"
            activeProps={active}
            className={`${item} hover:bg-navy-2`}
          >
            New Analysis
          </Link>
          {/* {upcoming.map((label) => (
            <span
              key={label}
              aria-disabled="true"
              className={`${item} flex cursor-not-allowed items-center justify-between opacity-40`}
            >
              {label}
              <span className="text-xs">soon</span>
            </span>
          ))} */}
        </nav>
      </aside>

      {/* En móvil el sidebar se oculta; queda una barra simple. */}
      <nav
        aria-label="Main (mobile)"
        className="flex gap-2 bg-navy px-4 py-3 text-sm text-white md:hidden"
      >
        <Link
          to="/"
          activeOptions={{ exact: true }}
          activeProps={active}
          className="rounded-lg px-3 py-2"
        >
          Dashboard
        </Link>
        <Link
          to="/analyses/new"
          activeProps={active}
          className="rounded-lg px-3 py-2"
        >
          New Analysis
        </Link>
      </nav>
    </>
  );
}
