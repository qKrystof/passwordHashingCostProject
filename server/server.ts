const ALGO = process.env.ALGO ?? "argon2id";
const PORT = Number(process.env.PORT ?? 3000);
const N_USERS = Number(process.env.N_USERS ?? 100);

type HashOpts =
  | { algorithm: "bcrypt"; cost: number }
  | { algorithm: "argon2id"; memoryCost: number; timeCost: number };

let hashOpts: HashOpts | null = null;
if (ALGO === "bcrypt") {
  hashOpts = { algorithm: "bcrypt", cost: Number(process.env.COST ?? 10) };
} else if (ALGO === "argon2id") {
  hashOpts = {
    algorithm: "argon2id",
    memoryCost: Number(process.env.MEM_KIB ?? 19456),
    timeCost: Number(process.env.TIME ?? 2),
  };
} else if (ALGO !== "sha256") {
  throw new Error(`unknown ALGO ${ALGO}`);
}

function sha256Hex(salt: string, pw: string): string {
  return new Bun.CryptoHasher("sha256").update(salt + pw).digest("hex");
}

async function hashPassword(pw: string): Promise<string> {

  if (hashOpts) return Bun.password.hash(pw, hashOpts);
  const salt = crypto.randomUUID();
  return `sha256$${salt}$${sha256Hex(salt, pw)}`;
}

async function verifyPassword(pw: string, stored: string): Promise<boolean> {
  if (hashOpts) return Bun.password.verify(pw, stored);
  const [, salt, digest] = stored.split("$");
  return sha256Hex(salt, pw) === digest;
}


const SEED_CONCURRENCY = Number(process.env.SEED_CONCURRENCY ?? N_USERS);
const users = new Map<string, string>();
for (let start = 0; start < N_USERS; start += SEED_CONCURRENCY) {
  const batch = Array.from({ length: Math.min(SEED_CONCURRENCY, N_USERS - start) }, (_, j) => start + j);
  await Promise.all(batch.map(async (i) => users.set(`user${i}`, await hashPassword(`pw-${i}-dummy`))));
}

const DUMMY_HASH = await hashPassword("no-such-user-placeholder");

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/health") return new Response("ok");


    if (url.pathname === "/sleep") {
      await Bun.sleep(Number(url.searchParams.get("ms") ?? 50));
      return new Response("slept");
    }

    if (url.pathname === "/login" && req.method === "POST") {
      let body: { username?: string; password?: string };
      try {
        body = (await req.json()) as typeof body;
      } catch {
        return new Response("bad json", { status: 400 });
      }
      const username = String(body.username ?? "");
      const stored = users.get(username) ?? DUMMY_HASH;
      const ok = await verifyPassword(String(body.password ?? ""), stored);
      if (!ok || !users.has(username)) {
        return Response.json({ ok: false }, { status: 401 });
      }
      return Response.json({ ok: true, session: crypto.randomUUID() });
    }
    return new Response("not found", { status: 404 });
  },
});

console.log(`READY ${ALGO} ${JSON.stringify(hashOpts)} port=${server.port} pid=${process.pid}`);
