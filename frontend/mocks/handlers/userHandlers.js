import { http, HttpResponse } from "msw";
import users from "../data/users.json";
import teamsData from "../data/teams.json";

function getUserProfile(userId) {
  const user = users.find((item) => item.id === userId);

  if (!user) return null;

  const membership = teamsData.team_members.find((item) => item.user_id === userId);
  const team = membership ? teamsData.teams.find((item) => item.id === membership.team_id) : null;

  return {
    id: user.id,
    nickname: user.nickname,
    avatar_url: user.avatar_url,
    team: team ? { id: team.id, name: team.name } : null,
    // The mock dataset does not define tournament registrations.
    // Keep this empty rather than inventing participation data.
    tournaments: [],
  };
}

export const userHandlers = [
  http.get("/api/me", () => {
    const profile = getUserProfile(users[0].id);

    return HttpResponse.json({
      id: profile.id,
      nickname: profile.nickname,
      avatar_url: profile.avatar_url,
    });
  }),

  http.post("/api/auth/logout", () => {
    return new HttpResponse(null, {
      status: 204,
    });
  }),

  http.get("/api/users/:id", ({ params }) => {
    const userId = Number(params.id);
    const profile = Number.isInteger(userId) ? getUserProfile(userId) : null;

    if (!profile) {
      return HttpResponse.json({ detail: "Игрок не найден" }, { status: 404 });
    }

    return HttpResponse.json(profile);
  }),
];
