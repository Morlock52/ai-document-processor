import { NextResponse, type NextRequest } from "next/server";

const PUBLIC = ["/login", "/api/health", "/api/v1", "/_next", "/favicon.ico"];
const COOKIE = "studio_session";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (PUBLIC.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }
  const cookie = req.cookies.get(COOKIE);
  if (!cookie) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
