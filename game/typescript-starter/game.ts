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
  {
    id: "chain-02",
    title: "Цепочка записей",
    direction: "east",
    fact: "Блокчейн связывает блоки записей криптографически; сама запись не доказывает, что сведения, введённые человеком, были правдивы.",
    source: "NIST IR 8202, Blockchain Technology Overview: https://doi.org/10.6028/NIST.IR.8202",
    metaphor: "Блоки похожи на бусы, нанизанные в цепь; образ не объясняет всю криптографию.",
    choices: [
      {
        label: "Проверить происхождение данных до записи и правила сети",
        isEvidenceBased: true,
        explanation: "Целостность цепочки и достоверность исходных сведений — разные вопросы.",
      },
      {
        label: "Считать любую запись в цепочке доказанной истиной",
        isEvidenceBased: false,
        explanation: "Технология не проверяет автоматически истинность внешнего утверждения.",
      },
    ],
  },
  {
    id: "alert-03",
    title: "Сигнал или решение?",
    direction: "south",
    fact: "Уведомление о цене сообщает наблюдение из конкретного источника в конкретный момент; оно не предсказывает будущую цену.",
    source: "Учебная модель Crypto Watch; перед реальным использованием требуются проверка источника и задержки данных.",
    metaphor: "Оповещение — звонок в дверь, а не приказ открыть её.",
    choices: [
      {
        label: "Посмотреть время, источник и риск, затем решить самостоятельно",
        isEvidenceBased: true,
        explanation: "Сигнал отделён от самостоятельного решения.",
      },
      {
        label: "Покупать автоматически после любого оповещения",
        isEvidenceBased: false,
        explanation: "Порог цены сам по себе не обосновывает сделку.",
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
