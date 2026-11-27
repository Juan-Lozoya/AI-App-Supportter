import { Outlet, createRootRoute } from "@tanstack/react-router";

import { Sidebar } from "../components/Sidebar";

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: () => <p className="p-8">Page not found.</p>,
});

function RootLayout() {
  return (
    <>
      <Sidebar />
      <div className="md:ml-60">
        <main className="p-[18px] md:p-[30px]">
          <Outlet />
        </main>
        <footer className="pb-8 text-center text-xs text-slate-400">
          Corporate Actions Analyzer | AI-assisted operations | Human validation
          required
        </footer>
      </div>
    </>
  );
}
