import { teamHandlers } from "./teamHandlers";
import { userHandlers } from "./userHandlers";

// /users/search must be registered before /users/:id, otherwise "search" is read as an ID.
export const handlers = [...teamHandlers, ...userHandlers];
