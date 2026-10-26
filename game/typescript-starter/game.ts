/** FujiBall: typed starting point for the next implementation.
 * This module does not replace the currently playable JavaScript demo.
 */
export type Direction = "north" | "east" | "south" | "west";

export type Choice = {
  label: string;
  isEvidenceBased: boolean;
  explanation: string;
};

export type Scene = {
  id: string;
  title: string;
  direction: Direction;
  fact: string;
  source: string;
  metaphor: string;
  choices: readonly Choice[];
};

export type Answer = {
  sceneId: string;
  choiceIndex: number;
  reflection: string;
};

export type GameState = {
  currentScene: number;
  answers: readonly Answer[];
  complete: boolean;
};

export const starterScenes: readonly Scene[] = [
  {
    id: "risk-01",
    title: "Факт или обещание?",
    direction: "north",
    fact: "Прошлый рост цены не гарантирует будущий результат.",
    source: "Учебный принцип оценки риска; перед публикацией урока нужен точный проверенный источник.",
    metaphor: "Цена на графике — след, а не карта будущего.",
    choices: [
      {
        label: "Проверить источник, дату и риск потери средств",
        isEvidenceBased: true,
        explanation: "Это проверяемые вопросы, а не обещание дохода.",
      },
      {
        label: "Считать прошлый рост гарантией прибыли",
        isEvidenceBased: false,
        explanation: "Прошлые данные не гарантируют будущую цену.",
      },
    ],
  },
];

export function startGame(): GameState {
  return { currentScene: 0, answers: [], complete: false };
}

export function currentScene(state: GameState, scenes: readonly Scene[]): Scene | null {
  return scenes[state.currentScene] ?? null;
}

export function submitAnswer(
  state: GameState,
  scenes: readonly Scene[],
  choiceIndex: number,
  reflection: string,
): GameState {
  const scene = currentScene(state, scenes);
  if (!scene || state.complete) throw new Error("Игра уже завершена");
  if (!scene.choices[choiceIndex]) throw new Error("Выбери один из вариантов");
  const note = reflection.trim();
  if (!note) throw new Error("Добавь короткое объяснение выбора");

  const nextScene = state.currentScene + 1;
  return {
    currentScene: nextScene,
    answers: [...state.answers, { sceneId: scene.id, choiceIndex, reflection: note }],
    complete: nextScene >= scenes.length,
  };
}
