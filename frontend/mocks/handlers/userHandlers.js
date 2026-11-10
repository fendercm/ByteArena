import { http, HttpResponse } from "msw";
import users from "../data/users.json";

export const userHandlers = [
  // Кто я
  http.get("/me", () => {
    const user = users[0];

    return HttpResponse.json({
      id: user.id,
      nickname: user.nickname,
      avatar_url: user.avatar_url,
    });
  }),

  // Выйти из аккаунта
  http.post("/auth/logout", () => {
    return new HttpResponse(null, {
      status: 204,
    });
  }),

  // Профиль игрока
  http.get("/users/:id", ({ params }) => {
    const userId = Number(params.id);
    const user = users.find((item) => item.id === userId);

    if (!user) {
      return HttpResponse.json(
        { detail: "Игрок не найден" },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      id: user.id,
      nickname: user.nickname,
      avatar_url: user.avatar_url,
    });
  }),
];