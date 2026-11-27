import { http, HttpResponse } from "msw";
import teamsData from "../data/teams.json";
import users from "../data/users.json";
import tournaments from "../data/tournaments.json";
import { homeTournaments } from "../../src/data/home-tournaments";
import matches from "../data/matches.json";
import { getTournamentResult, registrationRows } from "../tournamentResults";

const currentUserId = 1;
let nextTeamId = Math.max(...teamsData.teams.map((team) => team.id)) + 1;
let nextRegistrationId = Math.max(...registrationRows.map((registration) => registration.id)) + 1;

const findUser = (id) => users.find((user) => user.id === id);
const findTeam = (id) => teamsData.teams.find((team) => team.id === id);
const findTournament = (id) => {
  const tournament = tournaments.find((item) => item.id === id);
  if (tournament) return tournament;
  const homeTournament = homeTournaments.find((item) => item.id === id);
  return homeTournament
    ? {
        ...homeTournament,
        description: null,
        game: "cs2",
        rules: null,
        organizer_id: 1,
        created_at: homeTournament.starts_at,
      }
    : null;
};
const getMembers = (teamId) =>
  teamsData.team_members
    .filter((member) => member.team_id === teamId)
    .map((member) => {
      const user = member.user_id === null ? null : findUser(member.user_id);
      return {
        nickname: member.nickname ?? user?.nickname ?? "Игрок",
        user_id: member.user_id,
        avatar_url: user?.avatar_url ?? null,
        role: member.role,
      };
    })
    .sort((a, b) => {
      const order = { captain: 0, main: 1, sub: 2 };
      return order[a.role] - order[b.role];
    });

function getTeamProfile(teamId) {
  const team = findTeam(teamId);
  if (!team) return null;
  const captain = findUser(team.captain_id);
  if (!captain) return null;
  const teamRegistrations = registrationRows.filter((row) => row.team_id === teamId);
  return {
    id: team.id,
    name: team.name,
    captain: { id: captain.id, nickname: captain.nickname },
    members: getMembers(teamId),
    tournaments: teamRegistrations
      .map((registration) => {
        const tournament = findTournament(registration.tournament_id);
        if (!tournament) return null;
        return {
          id: tournament.id,
          title: tournament.title,
          starts_at: tournament.starts_at,
          status: tournament.status,
          application_status: registration.status,
          ...getTournamentResult(tournament, teamId),
        };
      })
      .filter(Boolean)
      .sort((a, b) => new Date(b.starts_at) - new Date(a.starts_at)),
  };
}

function getTeamOut(teamId) {
  const team = findTeam(teamId);
  if (!team) return null;
  return {
    id: team.id,
    name: team.name,
    captain_id: team.captain_id,
    members: getMembers(teamId).map(({ nickname, user_id, role }) => ({
      nickname,
      user_id,
      role,
    })),
  };
}

function getRegistrationOut(registration) {
  return {
    id: registration.id,
    tournament_id: registration.tournament_id,
    team_id: registration.team_id,
    status: registration.status,
  };
}

function getAdminRegistration(registration) {
  const team = findTeam(registration.team_id);
  return {
    id: registration.id,
    tournament_id: registration.tournament_id,
    team: { id: team.id, name: team.name },
    status: registration.status,
    members: getMembers(team.id).map(({ nickname, user_id, role }) => ({
      nickname,
      user_id,
      role,
    })),
  };
}

function error(detail, status) {
  return HttpResponse.json({ detail }, { status });
}

export const teamHandlers = [
  http.get("/api/matches/:matchId", ({ params }) => {
    const match = matches.find((item) => item.id === Number(params.matchId));
    if (!match) return error("Матч не найден", 404);
    const teamOut = (teamId) => {
      if (teamId === null) return null;
      const team = findTeam(teamId);
      return team ? { ...getTeamOut(teamId), members: getTeamOut(teamId).members } : null;
    };
    return HttpResponse.json({ ...match, team1: teamOut(match.team1_id), team2: teamOut(match.team2_id) });
  }),

  http.post("/api/tournaments/:tournamentId/start", async ({ params }) => {
    const tournament = findTournament(Number(params.tournamentId));
    if (!tournament) return error("Турнир не найден", 404);
    if (tournament.organizer_id !== currentUserId) return error("Недостаточно прав", 403);
    if (tournament.status !== "closed") return error(
      tournament.status === "running" || tournament.status === "finished" ? "Турнир уже запущен" : "Регистрация ещё не закрыта",
      409,
    );
    tournament.status = "running";
    return HttpResponse.json({ ...tournament, teams: [], matches: [] });
  }),

  http.post("/api/matches/:matchId/result", async ({ params, request }) => {
    const match = matches.find((item) => item.id === Number(params.matchId));
    if (!match) return error("Матч не найден", 404);
    const tournament = findTournament(match.tournament_id);
    if (tournament?.organizer_id !== currentUserId) return error("Недостаточно прав", 403);
    if (match.team1_id === null || match.team2_id === null) return error("В матче ещё нет обеих команд", 409);
    const body = await request.json();
    match.score1 = body.score1;
    match.score2 = body.score2;
    match.winner_id = body.score1 > body.score2 ? match.team1_id : match.team2_id;
    match.status = "finished";
    if (match.next_match_id === null) tournament.status = "finished";
    return HttpResponse.json(match);
  }),
  http.get("/api/users/search", ({ request }) => {
    const query = new URL(request.url).searchParams.get("q")?.trim() ?? "";
    if (query.length < 2) return HttpResponse.json([]);
    const normalized = query.toLocaleLowerCase();
    const matches = users
      .filter((user) => user.nickname.toLocaleLowerCase().startsWith(normalized))
      .sort((a, b) => a.nickname.localeCompare(b.nickname))
      .slice(0, 10)
      .map(({ id, nickname, avatar_url }) => ({ id, nickname, avatar_url }));
    return HttpResponse.json(matches);
  }),

  http.post("/api/teams", async ({ request }) => {
    const body = await request.json();
    const members = Array.isArray(body.members) ? body.members : [];
    const main = members.filter((member) => member.role === "main");
    const subs = members.filter((member) => member.role === "sub");
    if (main.length !== 4 || subs.length > 2) {
      return error("Проверьте количество игроков в составе", 422);
    }
    const captain = findUser(currentUserId);
    const names = [
      captain.nickname,
      ...members.map((member) => {
        const player = member.user_id ? findUser(member.user_id) : null;
        return player?.nickname ?? member.nickname;
      }),
    ];
    if (new Set(names.map((name) => name.toLocaleLowerCase())).size !== names.length) {
      return error("Ники в составе повторяются", 422);
    }
    for (const member of members) {
      if (member.user_id && !findUser(member.user_id)) {
        return error(`Игрок с ID ${member.user_id} не найден`, 404);
      }
    }

    const team = { id: nextTeamId++, name: body.name, captain_id: currentUserId };
    teamsData.teams.push(team);
    teamsData.team_members.push({
      team_id: team.id,
      user_id: currentUserId,
      nickname: captain.nickname,
      role: "captain",
    });
    for (const member of members) {
      const player = member.user_id ? findUser(member.user_id) : null;
      teamsData.team_members.push({
        team_id: team.id,
        user_id: member.user_id ?? null,
        nickname: player?.nickname ?? member.nickname,
        role: member.role,
      });
    }
    return HttpResponse.json(getTeamOut(team.id), { status: 201 });
  }),

  http.get("/api/teams/:teamId", ({ params }) => {
    const teamId = Number(params.teamId);
    const profile = Number.isInteger(teamId) ? getTeamProfile(teamId) : null;
    return profile ? HttpResponse.json(profile) : error("Команда не найдена", 404);
  }),

  http.get("/api/tournaments/:tournamentId", ({ params }) => {
    const tournamentId = Number(params.tournamentId);
    const tournament = findTournament(tournamentId);
    if (!tournament) return error("Турнир не найден", 404);
    const tournamentRegistrations = registrationRows.filter(
      (row) => row.tournament_id === tournamentId,
    );
    const teams = tournamentRegistrations
      .filter((row) => row.status === "approved")
      .map((row) => {
        const team = findTeam(row.team_id);
        return team ? { id: team.id, name: team.name, status: row.status } : null;
      })
      .filter(Boolean);
    return HttpResponse.json({
      ...tournament,
      teams_count: teams.length,
      teams,
      matches: [],
    });
  }),

  http.post("/api/tournaments/:tournamentId/registrations", async ({ params, request }) => {
    const tournamentId = Number(params.tournamentId);
    const tournament = findTournament(tournamentId);
    const { team_id: teamId } = await request.json();
    const team = findTeam(Number(teamId));
    if (!tournament) return error("Турнир не найден", 404);
    if (!team || team.captain_id !== currentUserId) {
      return error("Заявку подаёт капитан команды", 403);
    }
    if (tournament.status !== "registration") return error("Регистрация закрыта", 409);
    if (
      registrationRows.some((row) => row.tournament_id === tournamentId && row.team_id === team.id)
    ) {
      return error("Команда уже подала заявку", 409);
    }
    const approvedCount = registrationRows.filter(
      (row) => row.tournament_id === tournamentId && row.status === "approved",
    ).length;
    if (approvedCount >= tournament.max_teams) return error("Мест нет", 409);

    const playerIds = new Set(
      teamsData.team_members
        .filter((member) => member.team_id === team.id && member.user_id)
        .map((member) => member.user_id),
    );
    const conflicting = registrationRows
      .filter((row) => row.tournament_id === tournamentId && row.status !== "rejected")
      .map((row) => findTeam(row.team_id))
      .filter(Boolean)
      .some((otherTeam) =>
        teamsData.team_members.some(
          (member) => member.team_id === otherTeam.id && playerIds.has(member.user_id),
        ),
      );
    if (conflicting) return error("Игрок уже заявлен в другой команде", 409);

    const registration = {
      id: nextRegistrationId++,
      tournament_id: tournamentId,
      team_id: team.id,
      status: "pending",
    };
    registrationRows.push(registration);
    return HttpResponse.json(getRegistrationOut(registration), { status: 201 });
  }),

  http.get("/api/tournaments/:tournamentId/teams", ({ params }) => {
    const tournamentId = Number(params.tournamentId);
    const items = registrationRows
      .filter((row) => row.tournament_id === tournamentId && row.status === "approved")
      .map((row) => getTeamOut(row.team_id))
      .filter(Boolean);
    return HttpResponse.json({ items, total: items.length });
  }),

  http.get("/api/tournaments/:tournamentId/my-registration", ({ params }) => {
    const tournamentId = Number(params.tournamentId);
    const registration = registrationRows.find((row) => {
      const team = findTeam(row.team_id);
      return row.tournament_id === tournamentId && team?.captain_id === currentUserId;
    });
    return registration
      ? HttpResponse.json(getRegistrationOut(registration))
      : error("Заявка не найдена", 404);
  }),

  http.get("/api/tournaments/:tournamentId/registrations", ({ params }) => {
    const tournamentId = Number(params.tournamentId);
    const tournament = findTournament(tournamentId);
    if (!tournament) return error("Турнир не найден", 404);
    if (tournament.organizer_id !== currentUserId) {
      return error("Это может только организатор турнира", 403);
    }
    const items = registrationRows
      .filter((row) => row.tournament_id === tournamentId)
      .map(getAdminRegistration);
    return HttpResponse.json({ items, total: items.length });
  }),

  http.patch("/api/registrations/:registrationId", async ({ params, request }) => {
    const registrationId = Number(params.registrationId);
    const registration = registrationRows.find((row) => row.id === registrationId);
    if (!registration) return error("Заявка не найдена", 404);
    const tournament = findTournament(registration.tournament_id);
    if (tournament.organizer_id !== currentUserId) {
      return error("Это может только организатор турнира", 403);
    }
    if (tournament.status !== "registration") return error("Регистрация закрыта", 409);
    const body = await request.json();
    if (body.status === "approved" && registration.status !== "approved") {
      const approvedCount = registrationRows.filter(
        (row) => row.tournament_id === tournament.id && row.status === "approved",
      ).length;
      if (approvedCount >= tournament.max_teams) return error("Мест нет", 409);
    }
    registration.status = body.status;
    return HttpResponse.json(getAdminRegistration(registration));
  }),

  http.post("/api/tournaments/:tournamentId/close-registration", ({ params }) => {
    const tournamentId = Number(params.tournamentId);
    const tournament = findTournament(tournamentId);
    if (!tournament) return error("Турнир не найден", 404);
    if (tournament.organizer_id !== currentUserId) {
      return error("Это может только организатор турнира", 403);
    }
    if (tournament.status !== "registration") return error("Регистрация уже закрыта", 409);
    const approvedCount = registrationRows.filter(
      (row) => row.tournament_id === tournamentId && row.status === "approved",
    ).length;
    if (approvedCount < 2) return error("Нужно минимум 2 подтверждённые команды", 409);
    tournament.status = "closed";
    return HttpResponse.json({ ...tournament, teams_count: approvedCount });
  }),
];
